"""Traducen entre modelos ORM y entidades de dominio, para que el dominio
no conozca nada de la base de datos."""

from app.dominio.inventario import Ingrediente
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.pedido import DetallePedido, EstadoPedido, Pedido
from app.dominio.producto import Categoria, IngredienteDeReceta, ProductoMenu
from app.infraestructura.base_de_datos.modelos import (
    DetallePedidoModelo,
    IngredienteModelo,
    MesaModelo,
    PedidoModelo,
    ProductoModelo,
)


def mesa_a_dominio(modelo: MesaModelo) -> Mesa:
    return Mesa(numero=modelo.numero, capacidad=modelo.capacidad, estado=EstadoMesa(modelo.estado))


def ingrediente_a_dominio(modelo: IngredienteModelo) -> Ingrediente:
    return Ingrediente(
        id=modelo.id,
        nombre=modelo.nombre,
        unidad=modelo.unidad,
        stock=modelo.stock,
        stock_minimo=modelo.stock_minimo,
    )


def producto_a_dominio(modelo: ProductoModelo) -> ProductoMenu:
    return ProductoMenu(
        id=modelo.id,
        nombre=modelo.nombre,
        descripcion=modelo.descripcion,
        precio=modelo.precio,
        categoria=Categoria(modelo.categoria),
        icono=modelo.icono,
        activo=modelo.activo,
        receta=[
            IngredienteDeReceta(item.ingrediente_id, item.cantidad_por_porcion)
            for item in modelo.receta
        ],
    )


def pedido_a_dominio(modelo: PedidoModelo) -> Pedido:
    return Pedido(
        id=modelo.id,
        numero_mesa=modelo.numero_mesa,
        fecha_hora=modelo.fecha_hora,
        estado=EstadoPedido(modelo.estado),
        detalles=[
            DetallePedido(
                producto_id=detalle.producto_id,
                nombre_producto=detalle.nombre_producto,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
            )
            for detalle in modelo.detalles
        ],
    )


def pedido_a_modelo(pedido: Pedido) -> PedidoModelo:
    return PedidoModelo(
        numero_mesa=pedido.numero_mesa,
        fecha_hora=pedido.fecha_hora,
        estado=pedido.estado.value,
        detalles=[
            DetallePedidoModelo(
                producto_id=detalle.producto_id,
                nombre_producto=detalle.nombre_producto,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
            )
            for detalle in pedido.detalles
        ],
    )
