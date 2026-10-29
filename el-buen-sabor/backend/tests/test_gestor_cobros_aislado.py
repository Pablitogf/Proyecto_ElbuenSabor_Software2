"""GestorCobros probado con un envío a la DIAN falso (posible gracias al puerto
EnvioFacturaElectronica de la refactorización H-02)."""

import asyncio
from datetime import datetime

from app.aplicacion.casos_de_uso.caja.gestor_cobros import GestorCobros
from app.configuracion import Configuracion
from app.contenedor import Contenedor
from app.dominio.pago import MetodoPago, SolicitudLineaPago
from app.infraestructura.base_de_datos.datos_iniciales import inicializar_base_de_datos
from tests.ayudas import PEDIDO_ENTREGADO, TOTAL_PEDIDO_ENTREGADO

AHORA = datetime(2026, 10, 19, 13, 0)


class EnvioFalso:
    def __init__(self) -> None:
        self.enviadas: list[int] = []

    async def enviar_a_dian(self, factura_id: int):
        self.enviadas.append(factura_id)
        with self.uow as uow:
            return uow.facturas.obtener(factura_id)


def test_el_cobro_emite_y_pide_enviar_la_factura_sin_conocer_al_gestor_de_facturacion():
    contenedor = Contenedor(Configuracion(url_base_datos="sqlite://"))
    inicializar_base_de_datos(contenedor.motor, AHORA)
    envio = EnvioFalso()
    envio.uow = contenedor.unidad_de_trabajo()
    cajero = contenedor.sesion().usuarios()[2]
    gestor = GestorCobros(contenedor.unidad_de_trabajo(), contenedor.bus, contenedor.reloj,
                          contenedor.estrategias_pago, contenedor.emisor_facturas, envio)

    resultado = asyncio.run(gestor.cobrar(
        PEDIDO_ENTREGADO, [SolicitudLineaPago(MetodoPago.EFECTIVO, TOTAL_PEDIDO_ENTREGADO, 100_000)], cajero))

    assert envio.enviadas == [resultado.factura.id]
    assert resultado.factura.numero == "FEBS1001"
    assert resultado.pago.cambio == 20_000
