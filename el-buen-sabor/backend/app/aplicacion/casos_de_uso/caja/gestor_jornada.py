"""Jornada de caja: resumen del día, cierre y apertura (RF-10, RF-11, CU-06)."""

from dataclasses import dataclass

from app.aplicacion.puertos import (
    PublicadorEventos,
    Reloj,
    ServicioFacturacionElectronica,
    UnidadDeTrabajo,
)
from app.dominio.estados_pedido import ESTADOS_EN_SERVICIO, EstadoPedido
from app.dominio.eventos import JornadaActualizada
from app.dominio.excepciones import JornadaYaAbiertaError, ServicioExternoError
from app.dominio.inventario import Ingrediente
from app.dominio.jornada import CuadreDeCaja, Jornada, ReporteCierre
from app.dominio.usuario import Usuario

_PEDIDOS_PROCESADOS = frozenset({EstadoPedido.PAGADO, EstadoPedido.FACTURADO})


@dataclass(frozen=True)
class ResumenDelDia:
    """IU-04 Resumen: tarjetas de métricas y alerta de inventario."""

    jornada: Jornada
    ventas_totales: int
    pedidos_procesados: int
    ticket_promedio: int
    facturas_validadas: int
    facturas_emitidas: int
    mesas_en_servicio: int
    alertas_inventario: list[Ingrediente]


class GestorJornada:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos,
                 reloj: Reloj, servicio_dian: ServicioFacturacionElectronica) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj
        self._dian = servicio_dian

    def resumen(self) -> ResumenDelDia:
        with self._uow:
            jornada = self._uow.jornadas.actual()
            pagos = self._uow.pagos.listar_por_jornada(jornada.id)
            facturas = self._uow.facturas.listar_por_jornada(jornada.id)
            ventas = sum(pago.total for pago in pagos)
            return ResumenDelDia(
                jornada=jornada,
                ventas_totales=ventas,
                pedidos_procesados=self._uow.pedidos.contar_por_jornada_y_estados(
                    jornada.id, _PEDIDOS_PROCESADOS),
                ticket_promedio=ventas // len(pagos) if pagos else 0,
                facturas_validadas=sum(1 for f in facturas if f.esta_validada),
                facturas_emitidas=len(facturas),
                mesas_en_servicio=len(self._uow.pedidos.listar_por_estados(ESTADOS_EN_SERVICIO)),
                alertas_inventario=[i for i in self._uow.ingredientes.listar() if i.esta_bajo_minimo],
            )

    def previsualizar_cierre(self, efectivo_contado: int, observacion: str | None = None) -> ReporteCierre:
        """Muestra al administrador bloqueos e inconsistencias ANTES de cerrar."""
        with self._uow:
            return self._cuadre(self._uow.jornadas.actual(), efectivo_contado, observacion).generar_reporte()

    async def cerrar(self, efectivo_contado: int, observacion: str | None,
                     confirmar_inconsistencias: bool, administrador: Usuario) -> Jornada:
        """CU-02 pasos 8-10: cuadre, reporte a la DIAN y jornada cerrada (E-08)."""
        with self._uow:
            jornada = self._uow.jornadas.actual()
            cuadre = self._cuadre(jornada, efectivo_contado, observacion)
            previo = cuadre.generar_reporte()
            jornada.verificar_que_puede_cerrar(previo, confirmar_inconsistencias)

            respuesta = self._dian.enviar_reporte_diario(
                jornada, previo.total_ventas, previo.facturas_emitidas)
            if not respuesta.aceptada:
                raise ServicioExternoError(
                    f"La DIAN no recibió el reporte diario: {respuesta.mensaje}. La caja sigue abierta."
                )
            jornada.cerrar(cuadre.generar_reporte(comprobante_dian=respuesta.codigo),
                           confirmar_inconsistencias, self._reloj.ahora(), administrador.id)
            self._uow.jornadas.guardar(jornada)
            self._uow.confirmar()
        await self._eventos.publicar(JornadaActualizada(jornada.estado.value))
        return jornada

    async def abrir(self, base_caja: int, administrador: Usuario) -> Jornada:
        with self._uow:
            if self._uow.jornadas.actual().esta_abierta:
                raise JornadaYaAbiertaError()
            jornada = self._uow.jornadas.agregar(
                Jornada.abrir(base_caja, self._reloj.ahora(), administrador.id))
            self._uow.confirmar()
        await self._eventos.publicar(JornadaActualizada(jornada.estado.value))
        return jornada

    def _cuadre(self, jornada: Jornada, efectivo_contado: int, observacion: str | None) -> CuadreDeCaja:
        return CuadreDeCaja(
            jornada=jornada,
            pagos=self._uow.pagos.listar_por_jornada(jornada.id),
            facturas=self._uow.facturas.listar_por_jornada(jornada.id),
            pedidos_sin_cerrar=self._uow.pedidos.contar_por_jornada_y_estados(
                jornada.id, ESTADOS_EN_SERVICIO),
            pedidos_cancelados=self._uow.pedidos.contar_por_jornada_y_estados(
                jornada.id, frozenset({EstadoPedido.CANCELADO})),
            efectivo_contado=efectivo_contado,
            observacion=observacion,
        )
