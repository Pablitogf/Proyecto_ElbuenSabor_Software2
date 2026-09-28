"""Implementaciones SQLAlchemy de los repositorios definidos en app.aplicacion.puertos."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dominio.inventario import Ingrediente
from app.dominio.mesa import Mesa
from app.dominio.pedido import EstadoPedido, Pedido
from app.dominio.producto import ProductoMenu
from app.infraestructura.base_de_datos import mapeadores
from app.infraestructura.base_de_datos.modelos import (
    IngredienteModelo,
    MesaModelo,
    PedidoModelo,
    ProductoModelo,
)


class RepositorioMesasSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def listar(self) -> list[Mesa]:
        modelos = self._sesion.scalars(select(MesaModelo).order_by(MesaModelo.numero))
        return [mapeadores.mesa_a_dominio(modelo) for modelo in modelos]

    def obtener(self, numero: int) -> Mesa | None:
        modelo = self._sesion.get(MesaModelo, numero)
        return mapeadores.mesa_a_dominio(modelo) if modelo else None

    def guardar(self, mesa: Mesa) -> None:
        modelo = self._sesion.get_one(MesaModelo, mesa.numero)
        modelo.estado = mesa.estado.value


class RepositorioProductosSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def listar(self) -> list[ProductoMenu]:
        modelos = self._sesion.scalars(select(ProductoModelo).order_by(ProductoModelo.id))
        return [mapeadores.producto_a_dominio(modelo) for modelo in modelos]

    def obtener(self, producto_id: int) -> ProductoMenu | None:
        modelo = self._sesion.get(ProductoModelo, producto_id)
        return mapeadores.producto_a_dominio(modelo) if modelo else None


class RepositorioIngredientesSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def listar(self) -> list[Ingrediente]:
        modelos = self._sesion.scalars(select(IngredienteModelo))
        return [mapeadores.ingrediente_a_dominio(modelo) for modelo in modelos]

    def guardar_todos(self, ingredientes: list[Ingrediente]) -> None:
        for ingrediente in ingredientes:
            modelo = self._sesion.get_one(IngredienteModelo, ingrediente.id)
            modelo.stock = ingrediente.stock


class RepositorioPedidosSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion

    def agregar(self, pedido: Pedido) -> Pedido:
        modelo = mapeadores.pedido_a_modelo(pedido)
        self._sesion.add(modelo)
        self._sesion.flush()  # Asigna el id sin cerrar la transacción.
        return mapeadores.pedido_a_dominio(modelo)

    def listar_por_estado(self, estado: EstadoPedido) -> list[Pedido]:
        consulta = select(PedidoModelo).where(PedidoModelo.estado == estado.value)
        return [mapeadores.pedido_a_dominio(modelo) for modelo in self._sesion.scalars(consulta)]
