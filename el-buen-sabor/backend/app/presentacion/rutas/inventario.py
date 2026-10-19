from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dominio.usuario import Permiso, Usuario
from app.presentacion.dependencias import ContenedorDep, requiere
from app.presentacion.esquemas.base import ErrorRespuesta
from app.presentacion.esquemas.inventario import (
    EntradaSolicitud,
    IngredienteRespuesta,
    MermaSolicitud,
    MinimoSolicitud,
    MovimientoRespuesta,
    NuevoIngredienteSolicitud,
    SugerenciaRespuesta,
)

enrutador = APIRouter(prefix="/api/inventario", tags=["Inventario (F-04)"])
Administra = Annotated[Usuario, Depends(requiere(Permiso.GESTIONAR_INVENTARIO))]
ERRORES = {404: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}, 422: {"model": ErrorRespuesta}}


@enrutador.get("/ingredientes", response_model=list[IngredienteRespuesta])
def listar_ingredientes(_: Administra, contenedor: ContenedorDep):
    return [IngredienteRespuesta.desde(i) for i in contenedor.inventario().ingredientes()]


@enrutador.post("/ingredientes", response_model=IngredienteRespuesta,
                status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def crear_ingrediente(solicitud: NuevoIngredienteSolicitud, _: Administra, contenedor: ContenedorDep):
    ingrediente = await contenedor.inventario().crear_ingrediente(
        solicitud.nombre, solicitud.unidad, solicitud.stock_minimo)
    return IngredienteRespuesta.desde(ingrediente)


@enrutador.post("/ingredientes/{ingrediente_id}/entradas", response_model=IngredienteRespuesta,
                responses=ERRORES)
async def registrar_entrada(ingrediente_id: int, solicitud: EntradaSolicitud, usuario: Administra,
                            contenedor: ContenedorDep):
    ingrediente = await contenedor.inventario().registrar_entrada(
        ingrediente_id, solicitud.cantidad, solicitud.proveedor, usuario)
    return IngredienteRespuesta.desde(ingrediente)


@enrutador.post("/ingredientes/{ingrediente_id}/mermas", response_model=IngredienteRespuesta,
                responses=ERRORES)
async def registrar_merma(ingrediente_id: int, solicitud: MermaSolicitud, usuario: Administra,
                          contenedor: ContenedorDep):
    ingrediente = await contenedor.inventario().registrar_merma(
        ingrediente_id, solicitud.cantidad, solicitud.motivo, solicitud.detalle, usuario)
    return IngredienteRespuesta.desde(ingrediente)


@enrutador.put("/ingredientes/{ingrediente_id}/minimo", response_model=IngredienteRespuesta,
               responses=ERRORES)
async def cambiar_minimo(ingrediente_id: int, solicitud: MinimoSolicitud, _: Administra,
                         contenedor: ContenedorDep):
    return IngredienteRespuesta.desde(
        await contenedor.inventario().cambiar_minimo(ingrediente_id, solicitud.stock_minimo))


@enrutador.get("/movimientos", response_model=list[MovimientoRespuesta])
def movimientos_recientes(_: Administra, contenedor: ContenedorDep):
    return [MovimientoRespuesta.desde(m) for m in contenedor.inventario().movimientos()]


@enrutador.get("/sugerencias", response_model=list[SugerenciaRespuesta])
def sugerencias_de_compra(_: Administra, contenedor: ContenedorDep):
    """RF-12."""
    return [SugerenciaRespuesta.desde(s) for s in contenedor.inventario().sugerencias_de_compra()]
