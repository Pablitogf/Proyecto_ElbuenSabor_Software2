from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.aplicacion.casos_de_uso.registrar_pedido import ItemSolicitado, RegistrarPedido
from app.presentacion.dependencias import obtener_registrar_pedido
from app.presentacion.esquemas import ErrorRespuesta, PedidoRespuesta, PedidoSolicitud

enrutador = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


@enrutador.post(
    "",
    response_model=PedidoRespuesta,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}},
)
async def registrar_pedido(
    solicitud: PedidoSolicitud,
    caso_de_uso: Annotated[RegistrarPedido, Depends(obtener_registrar_pedido)],
):
    items = [ItemSolicitado(item.producto_id, item.cantidad) for item in solicitud.items]
    pedido = await caso_de_uso.ejecutar(solicitud.numero_mesa, items)
    return PedidoRespuesta.desde_dominio(pedido)
