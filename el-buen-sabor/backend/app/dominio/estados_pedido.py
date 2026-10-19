"""Patrón State para el ciclo de vida del pedido (RD-03, diagrama de estados 3.5).

Cada estado es una clase que sabe qué transiciones admite. Pedir una transición
no permitida lanza `TransicionDeEstadoInvalidaError`, así que es imposible saltar
pasos o retroceder: la regla vive en un único lugar y no en `if` dispersos.

    Registrado ─► EnPreparacion ─► ListoParaServir ─► Entregado ─► Pagado ─► Facturado
        │
        └─► Cancelado   (solo antes de que cocina empiece: "error de digitación")

`Pagado` es un estado intermedio que agregamos al modelo de análisis: el pago ya se
registró pero la DIAN todavía no valida la factura. Así se cumple RD-05 (el pedido no
se cierra sin factura validada) sin cobrar dos veces si la DIAN está caída.
"""

from abc import ABC
from enum import Enum
from typing import ClassVar

from app.dominio.excepciones import TransicionDeEstadoInvalidaError


class EstadoPedido(str, Enum):
    REGISTRADO = "REGISTRADO"
    EN_PREPARACION = "EN_PREPARACION"
    LISTO_PARA_SERVIR = "LISTO_PARA_SERVIR"
    ENTREGADO = "ENTREGADO"
    PAGADO = "PAGADO"
    FACTURADO = "FACTURADO"
    CANCELADO = "CANCELADO"


NOMBRE_LEGIBLE: dict[EstadoPedido, str] = {
    EstadoPedido.REGISTRADO: "registrado",
    EstadoPedido.EN_PREPARACION: "en preparación",
    EstadoPedido.LISTO_PARA_SERVIR: "listo para servir",
    EstadoPedido.ENTREGADO: "entregado",
    EstadoPedido.PAGADO: "pagado",
    EstadoPedido.FACTURADO: "facturado",
    EstadoPedido.CANCELADO: "cancelado",
}

# Mientras el pedido esté en uno de estos estados la mesa sigue ocupada.
ESTADOS_EN_SERVICIO = frozenset(
    {
        EstadoPedido.REGISTRADO,
        EstadoPedido.EN_PREPARACION,
        EstadoPedido.LISTO_PARA_SERVIR,
        EstadoPedido.ENTREGADO,
    }
)
ESTADOS_EN_COCINA = frozenset(
    {EstadoPedido.REGISTRADO, EstadoPedido.EN_PREPARACION, EstadoPedido.LISTO_PARA_SERVIR}
)


class EstadoDePedido(ABC):
    """Comportamiento por defecto: ninguna transición está permitida."""

    estado: ClassVar[EstadoPedido]

    def iniciar_preparacion(self) -> EstadoPedido:
        return self._rechazar("iniciar la preparación")

    def marcar_listo(self) -> EstadoPedido:
        return self._rechazar("marcar el pedido como listo")

    def entregar(self) -> EstadoPedido:
        return self._rechazar("entregar el pedido")

    def registrar_pago(self) -> EstadoPedido:
        return self._rechazar("cobrar el pedido")

    def facturar(self) -> EstadoPedido:
        return self._rechazar("facturar el pedido")

    def cancelar(self) -> EstadoPedido:
        return self._rechazar("cancelar el pedido")

    @property
    def permite_marcar_platos(self) -> bool:
        return False

    def _rechazar(self, accion: str) -> EstadoPedido:
        raise TransicionDeEstadoInvalidaError(accion, NOMBRE_LEGIBLE[self.estado])


class Registrado(EstadoDePedido):
    estado = EstadoPedido.REGISTRADO

    def iniciar_preparacion(self) -> EstadoPedido:
        return EstadoPedido.EN_PREPARACION

    def cancelar(self) -> EstadoPedido:
        return EstadoPedido.CANCELADO


class EnPreparacion(EstadoDePedido):
    estado = EstadoPedido.EN_PREPARACION

    def marcar_listo(self) -> EstadoPedido:
        return EstadoPedido.LISTO_PARA_SERVIR

    @property
    def permite_marcar_platos(self) -> bool:
        return True


class ListoParaServir(EstadoDePedido):
    estado = EstadoPedido.LISTO_PARA_SERVIR

    def entregar(self) -> EstadoPedido:
        return EstadoPedido.ENTREGADO


class Entregado(EstadoDePedido):
    estado = EstadoPedido.ENTREGADO

    def registrar_pago(self) -> EstadoPedido:
        return EstadoPedido.PAGADO


class Pagado(EstadoDePedido):
    estado = EstadoPedido.PAGADO

    def facturar(self) -> EstadoPedido:
        return EstadoPedido.FACTURADO


class Facturado(EstadoDePedido):
    estado = EstadoPedido.FACTURADO


class Cancelado(EstadoDePedido):
    estado = EstadoPedido.CANCELADO


_COMPORTAMIENTOS: dict[EstadoPedido, EstadoDePedido] = {
    clase.estado: clase()
    for clase in (Registrado, EnPreparacion, ListoParaServir, Entregado, Pagado, Facturado, Cancelado)
}


def comportamiento_de(estado: EstadoPedido) -> EstadoDePedido:
    return _COMPORTAMIENTOS[estado]
