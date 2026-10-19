"""Implementaciones SQLAlchemy de los repositorios (app.aplicacion.puertos)."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominio.estados_pedido import ESTADOS_EN_SERVICIO, EstadoPedido
from app.dominio.factura import Factura
from app.dominio.inventario import Ingrediente, MovimientoInventario, TipoMovimiento
from app.dominio.jornada import Jornada
from app.dominio.mesa import Mesa
from app.dominio.pago import Pago
from app.dominio.pedido import Pedido
from app.dominio.producto import ProductoMenu
from app.dominio.reserva import EstadoReserva, Reserva
from app.dominio.usuario import Usuario
from app.infraestructura.base_de_datos import mapeadores as mp
from app.infraestructura.base_de_datos.modelos import (
    FacturaModelo,
    IngredienteModelo,
    JornadaModelo,
    MesaModelo,
    MovimientoInventarioModelo,
    PagoModelo,
    PedidoModelo,
    ProductoModelo,
    ReservaModelo,
    UsuarioModelo,
)


class _RepositorioSQL:
    def __init__(self, sesion: Session) -> None:
        self._sesion = sesion


class RepositorioMesasSQL(_RepositorioSQL):
    def listar(self) -> list[Mesa]:
        modelos = self._sesion.scalars(select(MesaModelo).order_by(MesaModelo.numero))
        return [mp.mesa_a_dominio(m) for m in modelos]

    def obtener(self, numero: int) -> Mesa | None:
        modelo = self._sesion.get(MesaModelo, numero)
        return mp.mesa_a_dominio(modelo) if modelo else None

    def guardar(self, mesa: Mesa) -> None:
        self._sesion.get_one(MesaModelo, mesa.numero).estado = mesa.estado.value


class RepositorioProductosSQL(_RepositorioSQL):
    def listar(self) -> list[ProductoMenu]:
        modelos = self._sesion.scalars(select(ProductoModelo).order_by(ProductoModelo.id))
        return [mp.producto_a_dominio(m) for m in modelos]

    def obtener(self, producto_id: int) -> ProductoMenu | None:
        modelo = self._sesion.get(ProductoModelo, producto_id)
        return mp.producto_a_dominio(modelo) if modelo else None


class RepositorioIngredientesSQL(_RepositorioSQL):
    def listar(self) -> list[Ingrediente]:
        modelos = self._sesion.scalars(select(IngredienteModelo).order_by(IngredienteModelo.id))
        return [mp.ingrediente_a_dominio(m) for m in modelos]

    def obtener(self, ingrediente_id: int) -> Ingrediente | None:
        modelo = self._sesion.get(IngredienteModelo, ingrediente_id)
        return mp.ingrediente_a_dominio(modelo) if modelo else None

    def existe_con_nombre(self, nombre: str) -> bool:
        consulta = select(IngredienteModelo.id).where(
            func.lower(IngredienteModelo.nombre) == nombre.lower())
        return self._sesion.scalar(consulta) is not None

    def agregar(self, ingrediente: Ingrediente) -> Ingrediente:
        modelo = IngredienteModelo(nombre=ingrediente.nombre, unidad=ingrediente.unidad,
                                   stock=ingrediente.stock, stock_minimo=ingrediente.stock_minimo)
        self._sesion.add(modelo)
        self._sesion.flush()
        return mp.ingrediente_a_dominio(modelo)

    def guardar(self, ingrediente: Ingrediente) -> None:
        modelo = self._sesion.get_one(IngredienteModelo, ingrediente.id)
        modelo.stock, modelo.stock_minimo = ingrediente.stock, ingrediente.stock_minimo


class RepositorioMovimientosSQL(_RepositorioSQL):
    def agregar(self, movimiento: MovimientoInventario) -> None:
        self._sesion.add(mp.movimiento_a_modelo(movimiento))

    def listar_recientes(self, limite: int) -> list[MovimientoInventario]:
        consulta = (select(MovimientoInventarioModelo)
                    .order_by(MovimientoInventarioModelo.fecha_hora.desc(),
                              MovimientoInventarioModelo.id.desc())
                    .limit(limite))
        return [mp.movimiento_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def consumo_desde(self, desde: datetime) -> dict[int, float]:
        """Salidas por pedido menos devoluciones, por ingrediente (para RF-12)."""
        consumo: dict[int, float] = {}
        for tipo, signo in ((TipoMovimiento.SALIDA_PEDIDO, 1), (TipoMovimiento.DEVOLUCION, -1)):
            for ingrediente_id, total in self._sumar_por_ingrediente(tipo, desde=desde):
                consumo[ingrediente_id] = consumo.get(ingrediente_id, 0.0) + signo * total
        return consumo

    def salidas_del_pedido(self, pedido_id: int) -> dict[int, float]:
        return dict(self._sumar_por_ingrediente(TipoMovimiento.SALIDA_PEDIDO, pedido_id=pedido_id))

    def _sumar_por_ingrediente(self, tipo: TipoMovimiento, desde: datetime | None = None,
                               pedido_id: int | None = None):
        m = MovimientoInventarioModelo
        consulta = select(m.ingrediente_id, func.sum(m.cantidad)).where(m.tipo == tipo.value)
        if desde is not None:
            consulta = consulta.where(m.fecha_hora >= desde)
        if pedido_id is not None:
            consulta = consulta.where(m.pedido_id == pedido_id)
        return self._sesion.execute(consulta.group_by(m.ingrediente_id)).all()


class RepositorioPedidosSQL(_RepositorioSQL):
    def agregar(self, pedido: Pedido) -> Pedido:
        modelo = mp.pedido_a_modelo(pedido)
        self._sesion.add(modelo)
        self._sesion.flush()  # Asigna el id sin cerrar la transacción.
        return mp.pedido_a_dominio(modelo)

    def obtener(self, pedido_id: int) -> Pedido | None:
        modelo = self._sesion.get(PedidoModelo, pedido_id)
        return mp.pedido_a_dominio(modelo) if modelo else None

    def guardar(self, pedido: Pedido) -> None:
        mp.actualizar_pedido(self._sesion.get_one(PedidoModelo, pedido.id), pedido)

    def listar_por_estados(self, estados: frozenset[EstadoPedido]) -> list[Pedido]:
        consulta = select(PedidoModelo).where(PedidoModelo.estado.in_([e.value for e in estados]))
        return [mp.pedido_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def en_servicio_de_mesa(self, numero_mesa: int) -> Pedido | None:
        consulta = (select(PedidoModelo)
                    .where(PedidoModelo.numero_mesa == numero_mesa,
                           PedidoModelo.estado.in_([e.value for e in ESTADOS_EN_SERVICIO]))
                    .order_by(PedidoModelo.fecha_hora.desc()).limit(1))
        modelo = self._sesion.scalar(consulta)
        return mp.pedido_a_dominio(modelo) if modelo else None

    def contar_por_jornada_y_estados(self, jornada_id: int, estados: frozenset[EstadoPedido]) -> int:
        consulta = select(func.count(PedidoModelo.id)).where(
            PedidoModelo.jornada_id == jornada_id,
            PedidoModelo.estado.in_([e.value for e in estados]))
        return self._sesion.scalar(consulta) or 0


class RepositorioPagosSQL(_RepositorioSQL):
    def agregar(self, pago: Pago) -> Pago:
        modelo = mp.pago_a_modelo(pago)
        self._sesion.add(modelo)
        self._sesion.flush()
        return mp.pago_a_dominio(modelo)

    def listar_por_jornada(self, jornada_id: int) -> list[Pago]:
        consulta = select(PagoModelo).where(PagoModelo.jornada_id == jornada_id)
        return [mp.pago_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def de_factura(self, factura_id: int) -> Pago | None:
        modelo = self._sesion.scalar(select(PagoModelo).where(PagoModelo.factura_id == factura_id))
        return mp.pago_a_dominio(modelo) if modelo else None


class RepositorioFacturasSQL(_RepositorioSQL):
    def agregar(self, factura: Factura) -> Factura:
        modelo = mp.factura_a_modelo(factura)
        self._sesion.add(modelo)
        self._sesion.flush()
        return mp.factura_a_dominio(modelo)

    def obtener(self, factura_id: int) -> Factura | None:
        modelo = self._sesion.get(FacturaModelo, factura_id)
        return mp.factura_a_dominio(modelo) if modelo else None

    def guardar(self, factura: Factura) -> None:
        mp.factura_a_modelo(factura, self._sesion.get_one(FacturaModelo, factura.id))

    def ultimo_consecutivo(self) -> int:
        return self._sesion.scalar(select(func.max(FacturaModelo.consecutivo))) or 0

    def listar_por_jornada(self, jornada_id: int) -> list[Factura]:
        consulta = select(FacturaModelo).where(FacturaModelo.jornada_id == jornada_id)
        return [mp.factura_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def listar_recientes(self, limite: int) -> list[Factura]:
        consulta = select(FacturaModelo).order_by(FacturaModelo.consecutivo.desc()).limit(limite)
        return [mp.factura_a_dominio(m) for m in self._sesion.scalars(consulta)]


class RepositorioReservasSQL(_RepositorioSQL):
    def agregar(self, reserva: Reserva) -> Reserva:
        modelo = mp.reserva_a_modelo(reserva)
        self._sesion.add(modelo)
        self._sesion.flush()
        return mp.reserva_a_dominio(modelo)

    def obtener(self, reserva_id: int) -> Reserva | None:
        modelo = self._sesion.get(ReservaModelo, reserva_id)
        return mp.reserva_a_dominio(modelo) if modelo else None

    def guardar(self, reserva: Reserva) -> None:
        mp.reserva_a_modelo(reserva, self._sesion.get_one(ReservaModelo, reserva.id))

    def listar_pendientes(self) -> list[Reserva]:
        consulta = select(ReservaModelo).where(ReservaModelo.estado == EstadoReserva.PENDIENTE.value)
        return [mp.reserva_a_dominio(m) for m in self._sesion.scalars(consulta)]

    def listar_entre(self, desde: datetime, hasta: datetime) -> list[Reserva]:
        consulta = select(ReservaModelo).where(ReservaModelo.inicio >= desde, ReservaModelo.inicio < hasta)
        return [mp.reserva_a_dominio(m) for m in self._sesion.scalars(consulta)]


class RepositorioJornadasSQL(_RepositorioSQL):
    def actual(self) -> Jornada:
        """La jornada más reciente (abierta o recién cerrada). Siempre existe una."""
        modelo = self._sesion.scalar(select(JornadaModelo).order_by(JornadaModelo.id.desc()).limit(1))
        return mp.jornada_a_dominio(modelo)

    def agregar(self, jornada: Jornada) -> Jornada:
        modelo = mp.jornada_a_modelo(jornada)
        self._sesion.add(modelo)
        self._sesion.flush()
        return mp.jornada_a_dominio(modelo)

    def guardar(self, jornada: Jornada) -> None:
        mp.jornada_a_modelo(jornada, self._sesion.get_one(JornadaModelo, jornada.id))


class RepositorioUsuariosSQL(_RepositorioSQL):
    def por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None:
        modelo = self._sesion.scalar(
            select(UsuarioModelo).where(UsuarioModelo.nombre_usuario == nombre_usuario))
        return mp.usuario_a_dominio(modelo) if modelo else None

    def obtener(self, usuario_id: int) -> Usuario | None:
        modelo = self._sesion.get(UsuarioModelo, usuario_id)
        return mp.usuario_a_dominio(modelo) if modelo else None

    def listar(self) -> list[Usuario]:
        return [mp.usuario_a_dominio(m)
                for m in self._sesion.scalars(select(UsuarioModelo).order_by(UsuarioModelo.id))]
