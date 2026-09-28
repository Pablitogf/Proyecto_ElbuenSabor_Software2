from typing import Annotated

from fastapi import APIRouter, Depends

from app.aplicacion.casos_de_uso.consultar_menu_disponible import ConsultarMenuDisponible
from app.presentacion.dependencias import obtener_consultar_menu
from app.presentacion.esquemas import PlatoRespuesta

enrutador = APIRouter(prefix="/api/menu", tags=["Menú"])


@enrutador.get("", response_model=list[PlatoRespuesta])
def consultar_menu(
    caso_de_uso: Annotated[ConsultarMenuDisponible, Depends(obtener_consultar_menu)],
):
    return [PlatoRespuesta.desde_dominio(plato) for plato in caso_de_uso.ejecutar()]
