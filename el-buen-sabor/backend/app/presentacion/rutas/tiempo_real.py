from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.dominio.excepciones import AutenticacionError

enrutador = APIRouter(tags=["Tiempo real"])


@enrutador.websocket("/ws/eventos")
async def escuchar_eventos(conexion: WebSocket, token: str = "") -> None:
    """Las pantallas se suscriben con su token: sin sesión no hay eventos."""
    contenedor = conexion.app.state.contenedor
    try:
        contenedor.sesion().usuario_de(token)
    except AutenticacionError:
        await conexion.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    gestor = conexion.app.state.conexiones
    await gestor.conectar(conexion)
    try:
        while True:
            await conexion.receive_text()  # Mantiene la conexión abierta.
    except WebSocketDisconnect:
        gestor.desconectar(conexion)
