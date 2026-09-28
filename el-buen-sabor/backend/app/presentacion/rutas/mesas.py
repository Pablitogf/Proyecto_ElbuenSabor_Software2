from typing import Annotated

from fastapi import APIRouter, Depends

from app.aplicacion.casos_de_uso.listar_mesas import ListarMesas
from app.presentacion.dependencias import obtener_listar_mesas
from app.presentacion.esquemas import MesaRespuesta

enrutador = APIRouter(prefix="/api/mesas", tags=["Mesas"])


@enrutador.get("", response_model=list[MesaRespuesta])
def listar_mesas(caso_de_uso: Annotated[ListarMesas, Depends(obtener_listar_mesas)]):
    return [MesaRespuesta.desde_dominio(mesa) for mesa in caso_de_uso.ejecutar()]
