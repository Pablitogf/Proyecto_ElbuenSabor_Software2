from app.dominio.mesa import Mesa
from app.dominio.pedido import Pedido
from app.presentacion.esquemas import MesaRespuesta, PedidoRespuesta
from app.presentacion.tiempo_real.eventos import TipoEvento
from app.presentacion.tiempo_real.gestor_conexiones import GestorConexiones


class NotificadorWebSocket:
    """Implementa el puerto NotificadorEventos usando WebSockets (RF-02)."""

    def __init__(self, gestor: GestorConexiones) -> None:
        self._gestor = gestor

    async def notificar_pedido_registrado(self, pedido: Pedido, mesa: Mesa) -> None:
        await self._gestor.difundir(
            TipoEvento.PEDIDO_REGISTRADO,
            {
                "comanda": PedidoRespuesta.desde_dominio(pedido).model_dump(mode="json"),
                "mesa": MesaRespuesta.desde_dominio(mesa).model_dump(mode="json"),
            },
        )
