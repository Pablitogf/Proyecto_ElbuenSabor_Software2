from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from app.infraestructura.base_de_datos.datos_iniciales import reiniciar_base_de_datos
from app.presentacion.dependencias import obtener_gestor_conexiones
from app.presentacion.tiempo_real.eventos import TipoEvento
from app.presentacion.tiempo_real.gestor_conexiones import GestorConexiones

enrutador = APIRouter(prefix="/api/demostracion", tags=["Demostración"])


@enrutador.post("/reiniciar", status_code=status.HTTP_204_NO_CONTENT)
async def reiniciar_datos(
    request: Request,
    gestor: Annotated[GestorConexiones, Depends(obtener_gestor_conexiones)],
) -> None:
    """Solo para presentar el prototipo: deja mesas, inventario y comandas como al inicio."""
    reiniciar_base_de_datos(request.app.state.motor)
    await gestor.difundir(TipoEvento.DATOS_REINICIADOS, {})
