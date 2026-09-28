"""Modelos ORM: cómo se guardan las entidades en tablas relacionales (IS-03)."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infraestructura.base_de_datos.conexion import ModeloBase


class MesaModelo(ModeloBase):
    __tablename__ = "mesas"

    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    capacidad: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))


class IngredienteModelo(ModeloBase):
    __tablename__ = "ingredientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    unidad: Mapped[str] = mapped_column(String(10))
    stock: Mapped[float] = mapped_column(Float)
    stock_minimo: Mapped[float] = mapped_column(Float)


class ProductoModelo(ModeloBase):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str] = mapped_column(String(200))
    precio: Mapped[int] = mapped_column(Integer)
    categoria: Mapped[str] = mapped_column(String(30))
    icono: Mapped[str] = mapped_column(String(8))
    activo: Mapped[bool] = mapped_column(default=True)
    receta: Mapped[list["RecetaModelo"]] = relationship(lazy="selectin")


class RecetaModelo(ModeloBase):
    __tablename__ = "recetas"

    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), primary_key=True)
    ingrediente_id: Mapped[int] = mapped_column(ForeignKey("ingredientes.id"), primary_key=True)
    cantidad_por_porcion: Mapped[float] = mapped_column(Float)


class PedidoModelo(ModeloBase):
    __tablename__ = "pedidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_mesa: Mapped[int] = mapped_column(ForeignKey("mesas.numero"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime)
    estado: Mapped[str] = mapped_column(String(20))
    detalles: Mapped[list["DetallePedidoModelo"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )


class DetallePedidoModelo(ModeloBase):
    __tablename__ = "detalles_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    nombre_producto: Mapped[str] = mapped_column(String(80))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[int] = mapped_column(Integer)
