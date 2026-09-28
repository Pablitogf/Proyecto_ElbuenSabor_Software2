import logging

from fastapi import WebSocket

registro = logging.getLogger(__name__)


class GestorConexiones:
    """Mantiene las pantallas conectadas (tablets y cocina) y les difunde eventos."""

    def __init__(self) -> None:
        self._conexiones: set[WebSocket] = set()

    async def conectar(self, conexion: WebSocket) -> None:
        await conexion.accept()
        self._conexiones.add(conexion)

    def desconectar(self, conexion: WebSocket) -> None:
        self._conexiones.discard(conexion)

    async def difundir(self, tipo: str, datos: dict) -> None:
        mensaje = {"tipo": tipo, "datos": datos}
        for conexion in list(self._conexiones):
            try:
                await conexion.send_json(mensaje)
            except Exception:  # Pantalla cerrada sin avisar: se descarta.
                registro.info("Se descartó una conexión WebSocket inactiva.")
                self.desconectar(conexion)
