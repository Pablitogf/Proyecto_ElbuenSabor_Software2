"""Suscriptor del bus de eventos que reenvía cada evento a las pantallas (RF-02, RNF-02).

Ejemplo de mensaje: {"tipo": "PedidoListoParaServir", "datos": {"pedido_id": 7, "numero_mesa": 3}}
"""

from dataclasses import asdict

from app.dominio.eventos import EventoDeDominio
from app.presentacion.tiempo_real.gestor_conexiones import GestorConexiones


class DifusorDeEventos:
    def __init__(self, conexiones: GestorConexiones) -> None:
        self._conexiones = conexiones

    async def __call__(self, evento: EventoDeDominio) -> None:
        await self._conexiones.difundir({"tipo": evento.tipo, "datos": asdict(evento)})
