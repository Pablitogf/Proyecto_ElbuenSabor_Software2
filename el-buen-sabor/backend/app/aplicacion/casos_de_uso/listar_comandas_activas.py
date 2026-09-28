from app.aplicacion.puertos import UnidadDeTrabajo
from app.dominio.pedido import EstadoPedido, Pedido


class ListarComandasActivas:
    """IU-02: la cocina ve los pedidos registrados, del más antiguo al más reciente."""

    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo) -> None:
        self._uow = unidad_de_trabajo

    def ejecutar(self) -> list[Pedido]:
        with self._uow:
            pedidos = self._uow.pedidos.listar_por_estado(EstadoPedido.REGISTRADO)
        return sorted(pedidos, key=lambda pedido: pedido.fecha_hora)
