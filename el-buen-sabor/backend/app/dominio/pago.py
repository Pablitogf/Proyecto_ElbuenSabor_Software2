"""Pago de una cuenta (F-02, RF-06, RF-08, RF-09, CU-02 4a)."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.dominio.excepciones import PagoInvalidoError


class MetodoPago(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"


@dataclass(frozen=True)
class SolicitudLineaPago:
    """Lo que el cajero digita: cuánto se cubre con cada medio."""

    metodo: MetodoPago
    monto: int
    monto_recibido: int | None = None  # Solo efectivo: lo que entregó el cliente.


@dataclass(frozen=True)
class LineaPago:
    """Una parte del pago ya procesada (efectivo contado o tarjeta autorizada)."""

    metodo: MetodoPago
    monto: int
    monto_recibido: int | None = None
    autorizacion: str | None = None

    @property
    def cambio(self) -> int:
        if self.metodo != MetodoPago.EFECTIVO or self.monto_recibido is None:
            return 0
        return self.monto_recibido - self.monto


def validar_desglose(lineas: list[SolicitudLineaPago], total_cuenta: int) -> None:
    """Reglas del cobro. Se validan TODAS antes de pasar cualquier tarjeta."""
    if not lineas:
        raise PagoInvalidoError("Indica al menos un medio de pago.")
    metodos = [linea.metodo for linea in lineas]
    if len(metodos) != len(set(metodos)):
        raise PagoInvalidoError("Usa cada medio de pago una sola vez (efectivo y/o tarjeta).")
    for linea in lineas:
        if linea.monto <= 0:
            raise PagoInvalidoError("Cada parte del pago debe ser mayor que cero.")
    cubierto = sum(linea.monto for linea in lineas)
    if cubierto != total_cuenta:
        raise PagoInvalidoError(
            f"El pago suma ${cubierto:,} pero la cuenta es de ${total_cuenta:,}.".replace(",", ".")
        )


@dataclass
class Pago:
    pedido_id: int
    jornada_id: int
    lineas: list[LineaPago]
    fecha_hora: datetime
    cajero_id: int
    factura_id: int | None = None
    id: int | None = None

    @property
    def total(self) -> int:
        return sum(linea.monto for linea in self.lineas)

    @property
    def cambio(self) -> int:
        return sum(linea.cambio for linea in self.lineas)

    def monto_en(self, metodo: MetodoPago) -> int:
        return sum(linea.monto for linea in self.lineas if linea.metodo == metodo)

    @property
    def metodo_resumido(self) -> str:
        metodos = {linea.metodo for linea in self.lineas}
        return "MIXTO" if len(metodos) > 1 else next(iter(metodos)).value
