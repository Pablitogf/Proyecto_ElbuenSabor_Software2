"""Contratos JSON de la API. Traducen entidades de dominio a respuestas HTTP."""

from datetime import datetime

from pydantic import BaseModel

from app.aplicacion.casos_de_uso.consultar_menu_disponible import PlatoDelMenu
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.pedido import DetallePedido, EstadoPedido, Pedido
from app.dominio.producto import Categoria


class MesaRespuesta(BaseModel):
    numero: int
    capacidad: int
    estado: EstadoMesa

    @classmethod
    def desde_dominio(cls, mesa: Mesa) -> "MesaRespuesta":
        return cls(numero=mesa.numero, capacidad=mesa.capacidad, estado=mesa.estado)


class PlatoRespuesta(BaseModel):
    id: int
    nombre: str
    descripcion: str
    precio: int
    categoria: Categoria
    icono: str
    porciones_disponibles: int
    disponible: bool

    @classmethod
    def desde_dominio(cls, plato: PlatoDelMenu) -> "PlatoRespuesta":
        producto = plato.producto
        return cls(
            id=producto.id,
            nombre=producto.nombre,
            descripcion=producto.descripcion,
            precio=producto.precio,
            categoria=producto.categoria,
            icono=producto.icono,
            porciones_disponibles=plato.porciones_disponibles,
            disponible=plato.disponible,
        )


class ItemPedidoSolicitud(BaseModel):
    producto_id: int
    cantidad: int


class PedidoSolicitud(BaseModel):
    numero_mesa: int
    items: list[ItemPedidoSolicitud]


class DetallePedidoRespuesta(BaseModel):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: int
    subtotal: int

    @classmethod
    def desde_dominio(cls, detalle: DetallePedido) -> "DetallePedidoRespuesta":
        return cls(
            producto_id=detalle.producto_id,
            nombre_producto=detalle.nombre_producto,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario,
            subtotal=detalle.subtotal,
        )


class PedidoRespuesta(BaseModel):
    """También es la 'comanda' que ve la cocina (IU-02)."""

    id: int
    numero_mesa: int
    fecha_hora: datetime
    estado: EstadoPedido
    detalles: list[DetallePedidoRespuesta]
    total: int

    @classmethod
    def desde_dominio(cls, pedido: Pedido) -> "PedidoRespuesta":
        return cls(
            id=pedido.id,
            numero_mesa=pedido.numero_mesa,
            fecha_hora=pedido.fecha_hora,
            estado=pedido.estado,
            detalles=[DetallePedidoRespuesta.desde_dominio(d) for d in pedido.detalles],
            total=pedido.total,
        )


class ErrorRespuesta(BaseModel):
    detalle: str
