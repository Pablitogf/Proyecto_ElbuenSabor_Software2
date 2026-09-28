"""Puertos (interfaces) que la capa de aplicación necesita del mundo exterior.

Los casos de uso dependen de estas abstracciones, nunca de SQLAlchemy ni de
WebSockets directamente (Principio de Inversión de Dependencias).
"""

from typing import Protocol, Self

from app.dominio.inventario import Ingrediente
from app.dominio.mesa import Mesa
from app.dominio.pedido import EstadoPedido, Pedido
from app.dominio.producto import ProductoMenu


class RepositorioMesas(Protocol):
    def listar(self) -> list[Mesa]: ...

    def obtener(self, numero: int) -> Mesa | None: ...

    def guardar(self, mesa: Mesa) -> None: ...


class RepositorioProductos(Protocol):
    def listar(self) -> list[ProductoMenu]: ...

    def obtener(self, producto_id: int) -> ProductoMenu | None: ...


class RepositorioIngredientes(Protocol):
    def listar(self) -> list[Ingrediente]: ...

    def guardar_todos(self, ingredientes: list[Ingrediente]) -> None: ...


class RepositorioPedidos(Protocol):
    def agregar(self, pedido: Pedido) -> Pedido: ...

    def listar_por_estado(self, estado: EstadoPedido) -> list[Pedido]: ...


class UnidadDeTrabajo(Protocol):
    """Agrupa los repositorios en una sola transacción: todo se guarda o nada."""

    mesas: RepositorioMesas
    productos: RepositorioProductos
    ingredientes: RepositorioIngredientes
    pedidos: RepositorioPedidos

    def __enter__(self) -> Self: ...

    def __exit__(self, *args: object) -> None: ...

    def confirmar(self) -> None: ...


class NotificadorEventos(Protocol):
    """Avisa en tiempo real a las demás pantallas (tablets y cocina)."""

    async def notificar_pedido_registrado(self, pedido: Pedido, mesa: Mesa) -> None: ...
