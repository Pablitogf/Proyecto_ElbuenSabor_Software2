from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.dominio.excepciones import CantidadInvalidaError, PedidoVacioError


class EstadoPedido(str, Enum):
    """RD-03: ciclo de vida del pedido (en este slice solo se usa REGISTRADO)."""

    REGISTRADO = "REGISTRADO"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO_PARA_SERVIR = "LISTO_PARA_SERVIR"
    ENTREGADO = "ENTREGADO"
    FACTURADO = "FACTURADO"


@dataclass(frozen=True)
class DetallePedido:
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: int

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise CantidadInvalidaError(self.cantidad)

    @property
    def subtotal(self) -> int:
        return self.cantidad * self.precio_unitario


@dataclass
class Pedido:
    numero_mesa: int
    detalles: list[DetallePedido]
    fecha_hora: datetime
    estado: EstadoPedido = EstadoPedido.REGISTRADO
    id: int | None = None

    @classmethod
    def registrar(cls, numero_mesa: int, detalles: list[DetallePedido]) -> "Pedido":
        """Contrato 1 (crearPedido): nace en estado REGISTRADO con la hora actual."""
        if not detalles:
            raise PedidoVacioError()
        return cls(numero_mesa=numero_mesa, detalles=detalles, fecha_hora=datetime.now())

    @property
    def total(self) -> int:
        return sum(detalle.subtotal for detalle in self.detalles)
