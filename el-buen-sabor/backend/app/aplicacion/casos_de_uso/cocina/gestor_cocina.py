"""GestorCocina del diagrama de secuencia 2 (F-05, Contrato 2, RF-04)."""

from collections.abc import Callable

from app.aplicacion.puertos import PublicadorEventos, Reloj, UnidadDeTrabajo
from app.dominio.estados_pedido import ESTADOS_EN_COCINA
from app.dominio.eventos import EstadoDePedidoCambiado, PedidoListoParaServir
from app.dominio.excepciones import PedidoNoEncontradoError
from app.dominio.pedido import Pedido


class GestorCocina:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos,
                 reloj: Reloj) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj

    def comandas_activas(self) -> list[Pedido]:
        """IU-02: comandas ordenadas por hora de llegada (las listas siguen visibles
        hasta que el mesero las sirve, con el botón bloqueado)."""
        with self._uow:
            pedidos = self._uow.pedidos.listar_por_estados(ESTADOS_EN_COCINA)
        return sorted(pedidos, key=lambda pedido: pedido.fecha_hora)

    async def iniciar_preparacion(self, pedido_id: int) -> Pedido:
        return await self._aplicar(pedido_id, lambda pedido: pedido.iniciar_preparacion())

    async def marcar_plato(self, pedido_id: int, producto_id: int, preparado: bool) -> Pedido:
        return await self._aplicar(pedido_id, lambda pedido: pedido.marcar_plato(producto_id, preparado))

    async def marcar_listo(self, pedido_id: int) -> Pedido:
        pedido = await self._aplicar(pedido_id, lambda p: p.marcar_listo(self._reloj.ahora()))
        await self._eventos.publicar(PedidoListoParaServir(pedido.id, pedido.numero_mesa))
        return pedido

    async def _aplicar(self, pedido_id: int, accion: Callable[[Pedido], None]) -> Pedido:
        with self._uow:
            pedido = self._uow.pedidos.obtener(pedido_id)
            if pedido is None:
                raise PedidoNoEncontradoError(pedido_id)
            accion(pedido)
            self._uow.pedidos.guardar(pedido)
            self._uow.confirmar()
        await self._eventos.publicar(
            EstadoDePedidoCambiado(pedido.id, pedido.numero_mesa, pedido.estado.value)
        )
        return pedido
