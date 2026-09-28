from typing import Annotated

from fastapi import APIRouter, Depends

from app.aplicacion.casos_de_uso.listar_comandas_activas import ListarComandasActivas
from app.presentacion.dependencias import obtener_listar_comandas
from app.presentacion.esquemas import PedidoRespuesta

enrutador = APIRouter(prefix="/api/comandas", tags=["Cocina"])


@enrutador.get("", response_model=list[PedidoRespuesta])
def listar_comandas_activas(
    caso_de_uso: Annotated[ListarComandasActivas, Depends(obtener_listar_comandas)],
):
    return [PedidoRespuesta.desde_dominio(pedido) for pedido in caso_de_uso.ejecutar()]
