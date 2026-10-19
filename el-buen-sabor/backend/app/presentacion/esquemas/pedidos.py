from datetime import datetime

from app.aplicacion.casos_de_uso.salon.consultar_salon import MesaDelSalon, PlatoDelMenu
from app.dominio.estados_pedido import EstadoPedido
from app.dominio.mesa import EstadoMesa
from app.dominio.pedido import DetallePedido, Pedido
from app.dominio.producto import Categoria
from app.dominio.reserva import Reserva
from app.presentacion.esquemas.base import Esquema


class ReservaBreve(Esquema):
    id: int
    nombre_cliente: str
    personas: int
    inicio: datetime

    @classmethod
    def desde(cls, reserva: Reserva | None) -> "ReservaBreve | None":
        if reserva is None:
            return None
        return cls(id=reserva.id, nombre_cliente=reserva.nombre_cliente,
                   personas=reserva.personas, inicio=reserva.inicio)


class PedidoBreve(Esquema):
    id: int
    estado: EstadoPedido
    total: int
    cantidad_platos: int


class MesaRespuesta(Esquema):
    numero: int
    capacidad: int
    estado: EstadoMesa
    reserva_que_aparta: ReservaBreve | None
    proxima_reserva: ReservaBreve | None
    pedido: PedidoBreve | None

    @classmethod
    def desde(cls, mesa: MesaDelSalon) -> "MesaRespuesta":
        vista, pedido = mesa.vista, mesa.pedido
        return cls(
            numero=vista.mesa.numero, capacidad=vista.mesa.capacidad, estado=vista.estado,
            reserva_que_aparta=ReservaBreve.desde(vista.reserva_que_aparta),
            proxima_reserva=ReservaBreve.desde(vista.proxima_reserva),
            pedido=PedidoBreve(id=pedido.id, estado=pedido.estado, total=pedido.total,
                               cantidad_platos=pedido.cantidad_de_platos) if pedido else None,
        )


class PlatoRespuesta(Esquema):
    id: int
    nombre: str
    descripcion: str
    precio: int
    categoria: Categoria
    icono: str
    porciones_disponibles: int
    disponible: bool

    @classmethod
    def desde(cls, plato: PlatoDelMenu) -> "PlatoRespuesta":
        p = plato.producto
        return cls(id=p.id, nombre=p.nombre, descripcion=p.descripcion, precio=p.precio,
                   categoria=p.categoria, icono=p.icono,
                   porciones_disponibles=plato.porciones_disponibles, disponible=plato.disponible)


class ItemPedidoSolicitud(Esquema):
    producto_id: int
    cantidad: int


class PedidoSolicitud(Esquema):
    numero_mesa: int
    items: list[ItemPedidoSolicitud]


class CancelacionSolicitud(Esquema):
    motivo: str = ""


class DetalleRespuesta(Esquema):
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: int
    subtotal: int
    preparado: bool

    @classmethod
    def desde(cls, d: DetallePedido) -> "DetalleRespuesta":
        return cls(producto_id=d.producto_id, nombre_producto=d.nombre_producto, cantidad=d.cantidad,
                   precio_unitario=d.precio_unitario, subtotal=d.subtotal, preparado=d.preparado)


class PedidoRespuesta(Esquema):
    """También es la 'comanda' que ve la cocina (IU-02)."""

    id: int
    numero_mesa: int
    fecha_hora: datetime
    estado: EstadoPedido
    detalles: list[DetalleRespuesta]
    total: int
    hora_listo: datetime | None
    motivo_cancelacion: str | None

    @classmethod
    def desde(cls, p: Pedido) -> "PedidoRespuesta":
        return cls(id=p.id, numero_mesa=p.numero_mesa, fecha_hora=p.fecha_hora, estado=p.estado,
                   detalles=[DetalleRespuesta.desde(d) for d in p.detalles], total=p.total,
                   hora_listo=p.hora_listo, motivo_cancelacion=p.motivo_cancelacion)


class PlatoPreparadoSolicitud(Esquema):
    preparado: bool
