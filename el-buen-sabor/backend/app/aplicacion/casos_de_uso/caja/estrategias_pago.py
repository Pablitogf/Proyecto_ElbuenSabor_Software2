"""Patrón Strategy (+ Factory) para los medios de pago (F-02, RF-08).

Cada medio sabe cómo procesar su parte del cobro. Agregar "Nequi" o "Daviplata"
es crear otra estrategia y registrarla en la fábrica; el caso de uso no cambia.
"""

from typing import Protocol

from app.aplicacion.puertos import PasarelaDePagos
from app.dominio.excepciones import PagoInvalidoError, PagoRechazadoError
from app.dominio.pago import LineaPago, MetodoPago, SolicitudLineaPago


class EstrategiaDePago(Protocol):
    def procesar(self, solicitud: SolicitudLineaPago, referencia: str) -> LineaPago: ...


class PagoEnEfectivo:
    def procesar(self, solicitud: SolicitudLineaPago, referencia: str) -> LineaPago:
        recibido = solicitud.monto_recibido
        if recibido is None:
            raise PagoInvalidoError("Indica cuánto efectivo entregó el cliente.")
        if recibido < solicitud.monto:
            faltante = f"${solicitud.monto - recibido:,}".replace(",", ".")
            raise PagoInvalidoError(f"El efectivo recibido no alcanza: faltan {faltante}.")
        return LineaPago(MetodoPago.EFECTIVO, solicitud.monto, monto_recibido=recibido)


class PagoConTarjeta:
    def __init__(self, pasarela: PasarelaDePagos) -> None:
        self._pasarela = pasarela

    def procesar(self, solicitud: SolicitudLineaPago, referencia: str) -> LineaPago:
        respuesta = self._pasarela.autorizar(solicitud.monto, referencia)
        if not respuesta.aprobada:
            raise PagoRechazadoError(respuesta.motivo_rechazo or "sin motivo")
        return LineaPago(MetodoPago.TARJETA, solicitud.monto, autorizacion=respuesta.codigo_autorizacion)


class FabricaEstrategiasPago:
    def __init__(self, pasarela: PasarelaDePagos) -> None:
        self._estrategias: dict[MetodoPago, EstrategiaDePago] = {
            MetodoPago.EFECTIVO: PagoEnEfectivo(),
            MetodoPago.TARJETA: PagoConTarjeta(pasarela),
        }

    def para(self, metodo: MetodoPago) -> EstrategiaDePago:
        return self._estrategias[metodo]


def orden_de_procesamiento(solicitud: SolicitudLineaPago) -> int:
    """La tarjeta va de última: si el efectivo no cuadra, nunca se llega a cobrarla."""
    return 1 if solicitud.metodo == MetodoPago.TARJETA else 0
