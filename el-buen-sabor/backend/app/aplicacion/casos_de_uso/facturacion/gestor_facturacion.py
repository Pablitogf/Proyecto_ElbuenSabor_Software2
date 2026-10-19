"""GestorFacturacion del diagrama de secuencia 3 (F-03, RF-07, RD-05)."""

from dataclasses import dataclass

from app.aplicacion.puertos import (
    PublicadorEventos,
    Reloj,
    ServicioFacturacionElectronica,
    UnidadDeTrabajo,
)
from app.dominio.estados_pedido import EstadoPedido
from app.dominio.eventos import EstadoDePedidoCambiado, FacturaActualizada
from app.dominio.excepciones import FacturaNoEncontradaError, FacturaYaValidadaError
from app.dominio.factura import Factura
from app.dominio.pago import Pago
from app.dominio.pedido import Pedido


@dataclass(frozen=True)
class FacturaConDetalle:
    factura: Factura
    pedido: Pedido
    pago: Pago | None


class GestorFacturacion:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos,
                 reloj: Reloj, servicio_dian: ServicioFacturacionElectronica) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj
        self._dian = servicio_dian

    async def enviar_a_dian(self, factura_id: int) -> Factura:
        """Envía (o reenvía) la factura. Si la DIAN la valida, el pedido queda
        Facturado (RD-05). Si no responde, la factura queda pendiente y el cajero
        puede reintentar: el pago ya está registrado y no se cobra dos veces."""
        with self._uow:
            factura = self._factura(factura_id)
            if factura.esta_validada:
                raise FacturaYaValidadaError(factura.numero)
            pedido = self._uow.pedidos.obtener(factura.pedido_id)

            respuesta = self._dian.enviar_factura(factura, pedido)
            if respuesta.xml_enviado:
                factura.xml = respuesta.xml_enviado
            if respuesta.aceptada:
                factura.registrar_validacion(respuesta.codigo, self._reloj.ahora())
                if pedido.estado == EstadoPedido.PAGADO:
                    pedido.facturar()
                    self._uow.pedidos.guardar(pedido)
            else:
                factura.registrar_fallo_envio(respuesta.mensaje or "La DIAN no respondió.")
            self._uow.facturas.guardar(factura)
            self._uow.confirmar()

        await self._eventos.publicar(
            FacturaActualizada(factura.id, factura.numero, factura.estado.value),
            EstadoDePedidoCambiado(pedido.id, pedido.numero_mesa, pedido.estado.value),
        )
        return factura

    def recientes(self, limite: int = 20) -> list[FacturaConDetalle]:
        with self._uow:
            return [self._con_detalle(f) for f in self._uow.facturas.listar_recientes(limite)]

    def detalle(self, factura_id: int) -> FacturaConDetalle:
        with self._uow:
            return self._con_detalle(self._factura(factura_id))

    def _con_detalle(self, factura: Factura) -> FacturaConDetalle:
        return FacturaConDetalle(
            factura, self._uow.pedidos.obtener(factura.pedido_id), self._uow.pagos.de_factura(factura.id)
        )

    def _factura(self, factura_id: int) -> Factura:
        factura = self._uow.facturas.obtener(factura_id)
        if factura is None:
            raise FacturaNoEncontradaError(factura_id)
        return factura
