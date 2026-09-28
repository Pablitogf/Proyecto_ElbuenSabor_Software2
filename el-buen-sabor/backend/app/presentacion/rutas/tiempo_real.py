from fastapi import APIRouter, WebSocket, WebSocketDisconnect

enrutador = APIRouter(tags=["Tiempo real"])


@enrutador.websocket("/ws/eventos")
async def escuchar_eventos(conexion: WebSocket) -> None:
    gestor = conexion.app.state.gestor_conexiones
    await gestor.conectar(conexion)
    try:
        while True:
            await conexion.receive_text()  # Mantiene la conexión abierta.
    except WebSocketDisconnect:
        gestor.desconectar(conexion)
