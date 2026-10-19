"""Cobro de la cuenta de una mesa (F-02, CU-02 pasos 2-6, Contrato 3)."""

from dataclasses import dataclass

from app.aplicacion.casos_de_uso.caja.estrategias_pago import (
    FabricaEstrategiasPago,
    orden_de_procesamiento,
)
from app.aplicacion.casos_de_uso.facturacion.emisor_facturas import EmisorDeFacturas
from app.aplicacion.casos_de_uso.facturacion.gestor_facturacion import GestorFacturacion
from app.aplicacion.puertos import PublicadorEventos, Reloj, UnidadDeTrabajo
from app.dominio.estados_pedido import ESTADOS_EN_SERVICIO, EstadoPedido
from app.dominio.eventos import CuentaCobrada, EstadoDePedidoCambiado, MesasActualizadas
from app.dominio.excepciones import PedidoNoEncontradoError
from app.dominio.factura import Factura
from app.dominio.pago import Pago, SolicitudLineaPago, validar_desglose
from app.dominio.pedido import Pedido
from app.dominio.usuario import Usuario


@dataclass(frozen=True)
class ResultadoCobro:
    pago: Pago
    factura: Factura


class GestorCobros:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos, reloj: Reloj,
                 estrategias: FabricaEstrategiasPago, emisor: EmisorDeFacturas,
                 facturacion: GestorFacturacion) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj
        self._estrategias = estrategias
        self._emisor = emisor
        self._facturacion = facturacion

    def cuentas_abiertas(self) -> list[Pedido]:
        """IU-03 panel izquierdo: mesas con pedido en curso. Solo las entregadas se cobran."""
        with self._uow:
            pedidos = self._uow.pedidos.listar_por_estados(ESTADOS_EN_SERVICIO)
        return sorted(pedidos, key=lambda p: (p.estado != EstadoPedido.ENTREGADO, p.numero_mesa))

    async def cobrar(self, pedido_id: int, lineas: list[SolicitudLineaPago], cajero: Usuario) -> ResultadoCobro:
        ahora = self._reloj.ahora()
        with self._uow:
            self._uow.jornadas.actual().exigir_abierta()                # M-02
            pedido = self._pedido(pedido_id)
            pedido.registrar_pago()                                       # Solo si está ENTREGADO.
            validar_desglose(lineas, pedido.total)                        # RF-06
            mesa = self._uow.mesas.obtener(pedido.numero_mesa)
            mesa.liberar()                                                # CU-05 paso 9
            factura = self._emisor.emitir(self._uow, pedido, ahora)       # RF-07

            # La tarjeta es lo último que puede fallar: si algo anterior no cuadra,
            # nunca se llega a cobrarla. Un rechazo deshace toda la transacción (5a).
            procesadas = [
                self._estrategias.para(solicitud.metodo).procesar(solicitud, f"PED-{pedido.id}")
                for solicitud in sorted(lineas, key=orden_de_procesamiento)
            ]                                                             # RF-08
            pago = self._uow.pagos.agregar(Pago(
                pedido.id, pedido.jornada_id, procesadas, ahora, cajero.id, factura_id=factura.id,
            ))                                                            # RF-09
            self._uow.pedidos.guardar(pedido)
            self._uow.mesas.guardar(mesa)
            self._uow.confirmar()

        await self._eventos.publicar(
            CuentaCobrada(pedido.id, pedido.numero_mesa, pago.total),
            EstadoDePedidoCambiado(pedido.id, pedido.numero_mesa, pedido.estado.value),
            MesasActualizadas((pedido.numero_mesa,)),
        )
        factura = await self._facturacion.enviar_a_dian(factura.id)       # Diagrama 3
        return ResultadoCobro(pago, factura)

    def _pedido(self, pedido_id: int) -> Pedido:
        pedido = self._uow.pedidos.obtener(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)
        return pedido
