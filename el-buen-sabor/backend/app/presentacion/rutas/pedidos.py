from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.aplicacion.casos_de_uso.pedidos.gestor_pedidos import ItemSolicitado
from app.dominio.usuario import Permiso, Usuario
from app.presentacion.dependencias import ContenedorDep, requiere
from app.presentacion.esquemas.base import ErrorRespuesta
from app.presentacion.esquemas.pedidos import CancelacionSolicitud, PedidoRespuesta, PedidoSolicitud

enrutador = APIRouter(prefix="/api/pedidos", tags=["Pedidos (F-01, F-05)"])
ERRORES = {404: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}}


@enrutador.post("", response_model=PedidoRespuesta, status_code=status.HTTP_201_CREATED,
                responses=ERRORES)
async def registrar_pedido(solicitud: PedidoSolicitud, contenedor: ContenedorDep,
                           mesero: Annotated[Usuario, Depends(requiere(Permiso.REGISTRAR_PEDIDO))]):
    items = [ItemSolicitado(i.producto_id, i.cantidad) for i in solicitud.items]
    pedido = await contenedor.pedidos().registrar(solicitud.numero_mesa, items, mesero)
    return PedidoRespuesta.desde(pedido)


@enrutador.get("/listos", response_model=list[PedidoRespuesta])
def pedidos_listos_para_servir(_: Annotated[Usuario, Depends(requiere(Permiso.ATENDER_MESA))],
                               contenedor: ContenedorDep):
    """RF-04: notificaciones del mesero."""
    return [PedidoRespuesta.desde(p) for p in contenedor.pedidos().listos_para_servir()]


@enrutador.post("/{pedido_id}/entregar", response_model=PedidoRespuesta, responses=ERRORES)
async def entregar_pedido(pedido_id: int, contenedor: ContenedorDep,
                          _: Annotated[Usuario, Depends(requiere(Permiso.ATENDER_MESA))]):
    return PedidoRespuesta.desde(await contenedor.pedidos().entregar(pedido_id))


@enrutador.post("/{pedido_id}/cancelar", response_model=PedidoRespuesta, responses=ERRORES)
async def cancelar_pedido(pedido_id: int, solicitud: CancelacionSolicitud, contenedor: ContenedorDep,
                          usuario: Annotated[Usuario, Depends(requiere(Permiso.ATENDER_MESA))]):
    return PedidoRespuesta.desde(await contenedor.pedidos().cancelar(pedido_id, solicitud.motivo, usuario))
