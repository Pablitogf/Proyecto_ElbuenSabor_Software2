"""GestorPedidos del diagrama de secuencia 1 (F-01, CU-01)."""

from collections import Counter
from dataclasses import dataclass

from app.aplicacion.puertos import PublicadorEventos, Reloj, UnidadDeTrabajo
from app.dominio.agenda_mesas import AgendaDeMesas
from app.dominio.estados_pedido import EstadoPedido
from app.dominio.eventos import (
    EstadoDePedidoCambiado,
    EventoDeDominio,
    InventarioActualizado,
    MesasActualizadas,
    PedidoRegistrado,
    StockBajoMinimo,
)
from app.dominio.excepciones import (
    MesaNoEncontradaError,
    MesaReservadaError,
    PedidoNoEncontradoError,
    ProductoInactivoError,
    ProductoNoEncontradoError,
)
from app.dominio.inventario import Inventario, MovimientoInventario, TipoMovimiento
from app.dominio.mesa import Mesa
from app.dominio.pedido import DetallePedido, Pedido
from app.dominio.producto import ProductoMenu
from app.dominio.usuario import Usuario


@dataclass(frozen=True)
class ItemSolicitado:
    producto_id: int
    cantidad: int


class GestorPedidos:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos,
                 reloj: Reloj) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj

    # ── Registrar (Contrato 1: crearPedido) ────────────────────────────────────
    async def registrar(self, numero_mesa: int, items: list[ItemSolicitado], mesero: Usuario) -> Pedido:
        """1. Caja abierta (M-02). 2. Mesa libre y no apartada (RD-01, F-06).
        3. Platos activos (RD-02). 4. Stock re-consultado y descontado (RF-03, RF-05).
        5. Pedido + mesa ocupada + kardex en UNA transacción. 6. Comanda a cocina (RF-02)."""
        ahora = self._reloj.ahora()
        with self._uow:
            jornada = self._uow.jornadas.actual()
            jornada.exigir_abierta()
            mesa = self._mesa_sin_reserva_encima(numero_mesa)
            productos = self._productos_activos(items)

            pedido = Pedido.registrar(numero_mesa, self._detalles(productos), ahora, mesero.id, jornada.id)
            inventario = Inventario(self._uow.ingredientes.listar())
            resultado = inventario.consumir(productos)
            mesa.ocupar()

            pedido = self._uow.pedidos.agregar(pedido)
            self._uow.mesas.guardar(mesa)
            for ingrediente in inventario.ingredientes():
                self._uow.ingredientes.guardar(ingrediente)
            for ingrediente_id, cantidad in resultado.consumo_por_ingrediente.items():
                self._uow.movimientos.agregar(MovimientoInventario(
                    ingrediente_id, TipoMovimiento.SALIDA_PEDIDO, cantidad, ahora,
                    usuario_id=mesero.id, pedido_id=pedido.id,
                ))
            self._uow.confirmar()

        eventos: list[EventoDeDominio] = [
            PedidoRegistrado(pedido.id, numero_mesa),
            MesasActualizadas((numero_mesa,)),
            InventarioActualizado(),
        ]
        eventos += [
            StockBajoMinimo(i.id, i.nombre, i.stock, i.stock_minimo, i.unidad)
            for i in resultado.ingredientes_que_cruzaron_minimo
        ]
        await self._eventos.publicar(*eventos)
        return pedido

    # ── Consultas ──────────────────────────────────────────────────────────────
    def en_servicio_de_mesa(self, numero_mesa: int) -> Pedido | None:
        with self._uow:
            return self._uow.pedidos.en_servicio_de_mesa(numero_mesa)

    def listos_para_servir(self) -> list[Pedido]:
        """RF-04: notificaciones pendientes del mesero, la más antigua primero."""
        with self._uow:
            pedidos = self._uow.pedidos.listar_por_estados(frozenset({EstadoPedido.LISTO_PARA_SERVIR}))
        return sorted(pedidos, key=lambda p: p.hora_listo or p.fecha_hora)

    # ── Acciones del mesero ────────────────────────────────────────────────────
    async def entregar(self, pedido_id: int) -> Pedido:
        """RF-04: la notificación desaparece cuando el mesero marca el pedido servido."""
        with self._uow:
            pedido = self._pedido(pedido_id)
            pedido.entregar()
            self._uow.pedidos.guardar(pedido)
            self._uow.confirmar()
        await self._eventos.publicar(
            EstadoDePedidoCambiado(pedido.id, pedido.numero_mesa, pedido.estado.value),
            MesasActualizadas((pedido.numero_mesa,)),
        )
        return pedido

    async def cancelar(self, pedido_id: int, motivo: str, usuario: Usuario) -> Pedido:
        """Error de digitación: solo antes de que cocina empiece. Devuelve los
        ingredientes al inventario y libera la mesa."""
        ahora = self._reloj.ahora()
        with self._uow:
            pedido = self._pedido(pedido_id)
            pedido.cancelar(motivo)
            consumo = self._uow.movimientos.salidas_del_pedido(pedido.id)
            inventario = Inventario(self._uow.ingredientes.listar())
            inventario.devolver(consumo)
            mesa = self._uow.mesas.obtener(pedido.numero_mesa)
            mesa.liberar()

            self._uow.pedidos.guardar(pedido)
            self._uow.mesas.guardar(mesa)
            for ingrediente in inventario.ingredientes():
                self._uow.ingredientes.guardar(ingrediente)
            for ingrediente_id, cantidad in consumo.items():
                self._uow.movimientos.agregar(MovimientoInventario(
                    ingrediente_id, TipoMovimiento.DEVOLUCION, cantidad, ahora,
                    usuario_id=usuario.id, pedido_id=pedido.id, detalle="Pedido cancelado",
                ))
            self._uow.confirmar()
        await self._eventos.publicar(
            EstadoDePedidoCambiado(pedido.id, pedido.numero_mesa, pedido.estado.value),
            MesasActualizadas((pedido.numero_mesa,)),
            InventarioActualizado(),
        )
        return pedido

    # ── Internos ───────────────────────────────────────────────────────────────
    def _mesa_sin_reserva_encima(self, numero_mesa: int) -> Mesa:
        mesa = self._uow.mesas.obtener(numero_mesa)
        if mesa is None:
            raise MesaNoEncontradaError(numero_mesa)
        agenda = AgendaDeMesas([mesa], self._uow.reservas.listar_pendientes(), self._reloj.ahora())
        reserva = agenda.reserva_que_aparta(numero_mesa)
        if reserva and not mesa.esta_ocupada:
            raise MesaReservadaError(numero_mesa, reserva.nombre_cliente)
        return mesa

    def _productos_activos(self, items: list[ItemSolicitado]) -> list[tuple[ProductoMenu, int]]:
        cantidades: Counter[int] = Counter()
        for item in items:  # El mismo plato dos veces se suma en un solo renglón.
            cantidades[item.producto_id] += item.cantidad
        return [(self._producto_activo(pid), cantidad) for pid, cantidad in cantidades.items()]

    def _producto_activo(self, producto_id: int) -> ProductoMenu:
        producto = self._uow.productos.obtener(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(producto_id)
        if not producto.activo:
            raise ProductoInactivoError(producto.nombre)
        return producto

    @staticmethod
    def _detalles(productos: list[tuple[ProductoMenu, int]]) -> list[DetallePedido]:
        return [DetallePedido(p.id, p.nombre, cantidad, p.precio) for p, cantidad in productos]

    def _pedido(self, pedido_id: int) -> Pedido:
        pedido = self._uow.pedidos.obtener(pedido_id)
        if pedido is None:
            raise PedidoNoEncontradoError(pedido_id)
        return pedido
