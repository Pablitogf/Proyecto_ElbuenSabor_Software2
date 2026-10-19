"""Modelos ORM: cómo se guardan las entidades en tablas relacionales (IS-03)."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infraestructura.base_de_datos.conexion import ModeloBase


class UsuarioModelo(ModeloBase):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    nombre_usuario: Mapped[str] = mapped_column(String(40), unique=True)
    rol: Mapped[str] = mapped_column(String(20))
    hash_pin: Mapped[str] = mapped_column(String(200))


class JornadaModelo(ModeloBase):
    __tablename__ = "jornadas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fecha_apertura: Mapped[datetime] = mapped_column(DateTime)
    base_caja: Mapped[int] = mapped_column(Integer)
    abierta_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    estado: Mapped[str] = mapped_column(String(10))
    fecha_cierre: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cerrada_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    reporte: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class MesaModelo(ModeloBase):
    __tablename__ = "mesas"

    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    capacidad: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(20))


class IngredienteModelo(ModeloBase):
    __tablename__ = "ingredientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    unidad: Mapped[str] = mapped_column(String(10))
    stock: Mapped[float] = mapped_column(Float)
    stock_minimo: Mapped[float] = mapped_column(Float)


class MovimientoInventarioModelo(ModeloBase):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingrediente_id: Mapped[int] = mapped_column(ForeignKey("ingredientes.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    cantidad: Mapped[float] = mapped_column(Float)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, index=True)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    proveedor: Mapped[str | None] = mapped_column(String(80), nullable=True)
    motivo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    detalle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pedido_id: Mapped[int | None] = mapped_column(ForeignKey("pedidos.id"), nullable=True, index=True)


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
    numero_mesa: Mapped[int] = mapped_column(ForeignKey("mesas.numero"), index=True)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    mesero_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    hora_listo: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    motivo_cancelacion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    detalles: Mapped[list["DetallePedidoModelo"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", order_by="DetallePedidoModelo.id"
    )


class DetallePedidoModelo(ModeloBase):
    __tablename__ = "detalles_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    nombre_producto: Mapped[str] = mapped_column(String(80))
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[int] = mapped_column(Integer)
    preparado: Mapped[bool] = mapped_column(default=False)


class FacturaModelo(ModeloBase):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    consecutivo: Mapped[int] = mapped_column(Integer, unique=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), unique=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    fecha_emision: Mapped[datetime] = mapped_column(DateTime)
    base: Mapped[int] = mapped_column(Integer)
    impuesto: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    nombre_impuesto: Mapped[str] = mapped_column(String(10))
    codigo_impuesto: Mapped[str] = mapped_column(String(4))
    tarifa_impuesto: Mapped[float] = mapped_column(Float)
    cufe: Mapped[str] = mapped_column(String(96))
    estado: Mapped[str] = mapped_column(String(20))
    intentos_envio: Mapped[int] = mapped_column(Integer, default=0)
    ultimo_error: Mapped[str | None] = mapped_column(String(300), nullable=True)
    codigo_validacion: Mapped[str | None] = mapped_column(String(80), nullable=True)
    fecha_validacion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    xml: Mapped[str | None] = mapped_column(Text, nullable=True)


class PagoModelo(ModeloBase):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"), unique=True)
    jornada_id: Mapped[int] = mapped_column(ForeignKey("jornadas.id"), index=True)
    factura_id: Mapped[int | None] = mapped_column(ForeignKey("facturas.id"), nullable=True)
    cajero_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime)
    lineas: Mapped[list["LineaPagoModelo"]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", order_by="LineaPagoModelo.id"
    )


class LineaPagoModelo(ModeloBase):
    __tablename__ = "lineas_pago"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pago_id: Mapped[int] = mapped_column(ForeignKey("pagos.id"))
    metodo: Mapped[str] = mapped_column(String(20))
    monto: Mapped[int] = mapped_column(Integer)
    monto_recibido: Mapped[int | None] = mapped_column(Integer, nullable=True)
    autorizacion: Mapped[str | None] = mapped_column(String(40), nullable=True)


class ReservaModelo(ModeloBase):
    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_cliente: Mapped[str] = mapped_column(String(80))
    telefono: Mapped[str] = mapped_column(String(15))
    personas: Mapped[int] = mapped_column(Integer)
    inicio: Mapped[datetime] = mapped_column(DateTime, index=True)
    numero_mesa: Mapped[int] = mapped_column(ForeignKey("mesas.numero"))
    creada_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    estado: Mapped[str] = mapped_column(String(15), index=True)
    notas: Mapped[str | None] = mapped_column(String(200), nullable=True)
