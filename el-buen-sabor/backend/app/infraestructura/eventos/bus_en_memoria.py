"""Patrón Observer: bus de eventos en memoria.

Los casos de uso publican; los suscriptores (hoy, el difusor de WebSockets)
reaccionan. Si un suscriptor falla, no tumba la operación que ya se confirmó.
"""

import logging
from collections.abc import Awaitable, Callable

from app.dominio.eventos import EventoDeDominio

ManejadorDeEvento = Callable[[EventoDeDominio], Awaitable[None]]
registro = logging.getLogger(__name__)


class BusDeEventosEnMemoria:
    def __init__(self) -> None:
        self._suscriptores: list[ManejadorDeEvento] = []

    def suscribir(self, manejador: ManejadorDeEvento) -> None:
        self._suscriptores.append(manejador)

    async def publicar(self, *eventos: EventoDeDominio) -> None:
        for evento in eventos:
            for manejador in self._suscriptores:
                try:
                    await manejador(evento)
                except Exception:
                    registro.exception("Un suscriptor falló al procesar %s", evento.tipo)
