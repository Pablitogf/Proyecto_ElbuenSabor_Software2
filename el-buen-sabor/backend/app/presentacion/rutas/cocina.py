from typing import Annotated

from fastapi import APIRouter, Depends

from app.dominio.usuario import Permiso, Usuario
from app.presentacion.dependencias import ContenedorDep, requiere
from app.presentacion.esquemas.base import ErrorRespuesta
from app.presentacion.esquemas.pedidos import PedidoRespuesta, PlatoPreparadoSolicitud

enrutador = APIRouter(prefix="/api/comandas", tags=["Cocina (F-05)"])
PuedePreparar = Annotated[Usuario, Depends(requiere(Permiso.PREPARAR_PEDIDO))]
ERRORES = {404: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}}


@enrutador.get("", response_model=list[PedidoRespuesta])
def comandas_activas(_: Annotated[Usuario, Depends(requiere(Permiso.VER_COMANDAS))],
                     contenedor: ContenedorDep):
    return [PedidoRespuesta.desde(p) for p in contenedor.cocina().comandas_activas()]


@enrutador.post("/{pedido_id}/iniciar", response_model=PedidoRespuesta, responses=ERRORES)
async def iniciar_preparacion(pedido_id: int, _: PuedePreparar, contenedor: ContenedorDep):
    """Contrato 2: actualizarEstado(idPedido, 'En Preparación')."""
    return PedidoRespuesta.desde(await contenedor.cocina().iniciar_preparacion(pedido_id))


@enrutador.put("/{pedido_id}/platos/{producto_id}", response_model=PedidoRespuesta, responses=ERRORES)
async def marcar_plato(pedido_id: int, producto_id: int, solicitud: PlatoPreparadoSolicitud,
                       _: PuedePreparar, contenedor: ContenedorDep):
    pedido = await contenedor.cocina().marcar_plato(pedido_id, producto_id, solicitud.preparado)
    return PedidoRespuesta.desde(pedido)


@enrutador.post("/{pedido_id}/listo", response_model=PedidoRespuesta, responses=ERRORES)
async def marcar_listo(pedido_id: int, _: PuedePreparar, contenedor: ContenedorDep):
    """SWR-12 / RF-04: notifica al mesero."""
    return PedidoRespuesta.desde(await contenedor.cocina().marcar_listo(pedido_id))
