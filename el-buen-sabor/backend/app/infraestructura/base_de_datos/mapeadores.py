"""Patrón Data Mapper: traduce entre modelos ORM y entidades de dominio, para que
el dominio no sepa nada de la base de datos."""

from dataclasses import asdict

from app.dominio.estados_pedido import EstadoPedido
from app.dominio.factura import EstadoFactura, Factura
from app.dominio.inventario import Ingrediente, MotivoMerma, MovimientoInventario, TipoMovimiento
from app.dominio.jornada import EstadoJornada, Jornada, ReporteCierre
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.pago import LineaPago, MetodoPago, Pago
from app.dominio.pedido import DetallePedido, Pedido
from app.dominio.producto import Categoria, IngredienteDeReceta, ProductoMenu
from app.dominio.reserva import EstadoReserva, Reserva
from app.dominio.usuario import Rol, Usuario
from app.infraestructura.base_de_datos.modelos import (
    DetallePedidoModelo,
    FacturaModelo,
    IngredienteModelo,
    JornadaModelo,
    LineaPagoModelo,
    MesaModelo,
    MovimientoInventarioModelo,
    PagoModelo,
    PedidoModelo,
    ProductoModelo,
    ReservaModelo,
    UsuarioModelo,
)


# ── Usuarios y jornada ────────────────────────────────────────────────────────
def usuario_a_dominio(m: UsuarioModelo) -> Usuario:
    return Usuario(m.id, m.nombre, m.nombre_usuario, Rol(m.rol), m.hash_pin)


def jornada_a_dominio(m: JornadaModelo) -> Jornada:
    return Jornada(
        id=m.id, fecha_apertura=m.fecha_apertura, base_caja=m.base_caja, abierta_por=m.abierta_por,
        estado=EstadoJornada(m.estado), fecha_cierre=m.fecha_cierre, cerrada_por=m.cerrada_por,
        reporte=ReporteCierre(**m.reporte) if m.reporte else None,
    )


def jornada_a_modelo(j: Jornada, m: JornadaModelo | None = None) -> JornadaModelo:
    m = m or JornadaModelo()
    m.fecha_apertura, m.base_caja, m.abierta_por = j.fecha_apertura, j.base_caja, j.abierta_por
    m.estado, m.fecha_cierre, m.cerrada_por = j.estado.value, j.fecha_cierre, j.cerrada_por
    m.reporte = asdict(j.reporte) if j.reporte else None
    return m


# ── Salón e inventario ─────────────────────────────────────────────────────────
def mesa_a_dominio(m: MesaModelo) -> Mesa:
    return Mesa(numero=m.numero, capacidad=m.capacidad, estado=EstadoMesa(m.estado))


def ingrediente_a_dominio(m: IngredienteModelo) -> Ingrediente:
    return Ingrediente(m.id, m.nombre, m.unidad, m.stock, m.stock_minimo)


def movimiento_a_dominio(m: MovimientoInventarioModelo) -> MovimientoInventario:
    return MovimientoInventario(
        id=m.id, ingrediente_id=m.ingrediente_id, tipo=TipoMovimiento(m.tipo), cantidad=m.cantidad,
        fecha_hora=m.fecha_hora, usuario_id=m.usuario_id, proveedor=m.proveedor,
        motivo=MotivoMerma(m.motivo) if m.motivo else None, detalle=m.detalle, pedido_id=m.pedido_id,
    )


def movimiento_a_modelo(mv: MovimientoInventario) -> MovimientoInventarioModelo:
    return MovimientoInventarioModelo(
        ingrediente_id=mv.ingrediente_id, tipo=mv.tipo.value, cantidad=mv.cantidad,
        fecha_hora=mv.fecha_hora, usuario_id=mv.usuario_id, proveedor=mv.proveedor,
        motivo=mv.motivo.value if mv.motivo else None, detalle=mv.detalle, pedido_id=mv.pedido_id,
    )


def producto_a_dominio(m: ProductoModelo) -> ProductoMenu:
    return ProductoMenu(
        id=m.id, nombre=m.nombre, descripcion=m.descripcion, precio=m.precio,
        categoria=Categoria(m.categoria), icono=m.icono, activo=m.activo,
        receta=[IngredienteDeReceta(r.ingrediente_id, r.cantidad_por_porcion) for r in m.receta],
    )


# ── Pedidos ────────────────────────────────────────────────────────────────────
def pedido_a_dominio(m: PedidoModelo) -> Pedido:
    return Pedido(
        id=m.id, numero_mesa=m.numero_mesa, fecha_hora=m.fecha_hora, estado=EstadoPedido(m.estado),
        mesero_id=m.mesero_id, jornada_id=m.jornada_id, hora_listo=m.hora_listo,
        motivo_cancelacion=m.motivo_cancelacion,
        detalles=[
            DetallePedido(d.producto_id, d.nombre_producto, d.cantidad, d.precio_unitario, d.preparado)
            for d in m.detalles
        ],
    )


def pedido_a_modelo(p: Pedido) -> PedidoModelo:
    modelo = PedidoModelo(
        numero_mesa=p.numero_mesa, fecha_hora=p.fecha_hora, mesero_id=p.mesero_id,
        jornada_id=p.jornada_id,
        detalles=[
            DetallePedidoModelo(producto_id=d.producto_id, nombre_producto=d.nombre_producto,
                                cantidad=d.cantidad, precio_unitario=d.precio_unitario)
            for d in p.detalles
        ],
    )
    actualizar_pedido(modelo, p)
    return modelo


def actualizar_pedido(m: PedidoModelo, p: Pedido) -> None:
    """Solo cambian el estado y lo que el ciclo de vida toca; los platos son fijos."""
    m.estado, m.hora_listo, m.motivo_cancelacion = p.estado.value, p.hora_listo, p.motivo_cancelacion
    preparados = {d.producto_id: d.preparado for d in p.detalles}
    for detalle in m.detalles:
        detalle.preparado = preparados[detalle.producto_id]


# ── Caja y facturación ─────────────────────────────────────────────────────────
def pago_a_dominio(m: PagoModelo) -> Pago:
    return Pago(
        id=m.id, pedido_id=m.pedido_id, jornada_id=m.jornada_id, fecha_hora=m.fecha_hora,
        cajero_id=m.cajero_id, factura_id=m.factura_id,
        lineas=[LineaPago(MetodoPago(l.metodo), l.monto, l.monto_recibido, l.autorizacion)
                for l in m.lineas],
    )


def pago_a_modelo(p: Pago) -> PagoModelo:
    return PagoModelo(
        pedido_id=p.pedido_id, jornada_id=p.jornada_id, factura_id=p.factura_id,
        cajero_id=p.cajero_id, fecha_hora=p.fecha_hora,
        lineas=[LineaPagoModelo(metodo=l.metodo.value, monto=l.monto, monto_recibido=l.monto_recibido,
                                autorizacion=l.autorizacion) for l in p.lineas],
    )


_CAMPOS_FACTURA = (
    "numero", "consecutivo", "pedido_id", "jornada_id", "fecha_emision", "base", "impuesto", "total",
    "nombre_impuesto", "codigo_impuesto", "tarifa_impuesto", "cufe", "intentos_envio",
    "ultimo_error", "codigo_validacion", "fecha_validacion", "xml",
)


def factura_a_dominio(m: FacturaModelo) -> Factura:
    datos = {campo: getattr(m, campo) for campo in _CAMPOS_FACTURA}
    return Factura(id=m.id, estado=EstadoFactura(m.estado), **datos)


def factura_a_modelo(f: Factura, m: FacturaModelo | None = None) -> FacturaModelo:
    m = m or FacturaModelo()
    for campo in _CAMPOS_FACTURA:
        setattr(m, campo, getattr(f, campo))
    m.estado = f.estado.value
    return m


# ── Reservas ───────────────────────────────────────────────────────────────────
def reserva_a_dominio(m: ReservaModelo) -> Reserva:
    return Reserva(
        id=m.id, nombre_cliente=m.nombre_cliente, telefono=m.telefono, personas=m.personas,
        inicio=m.inicio, numero_mesa=m.numero_mesa, creada_por=m.creada_por,
        estado=EstadoReserva(m.estado), notas=m.notas,
    )


def reserva_a_modelo(r: Reserva, m: ReservaModelo | None = None) -> ReservaModelo:
    m = m or ReservaModelo()
    m.nombre_cliente, m.telefono, m.personas = r.nombre_cliente, r.telefono, r.personas
    m.inicio, m.numero_mesa, m.creada_por = r.inicio, r.numero_mesa, r.creada_por
    m.estado, m.notas = r.estado.value, r.notas
    return m
