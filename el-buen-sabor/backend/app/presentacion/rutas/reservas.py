from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dominio.usuario import Permiso, Usuario
from app.presentacion.dependencias import ContenedorDep, requiere
from app.presentacion.esquemas.base import ErrorRespuesta
from app.presentacion.esquemas.reservas import (
    ReprogramacionSolicitud,
    ReservaRespuesta,
    ReservaSolicitud,
)

enrutador = APIRouter(prefix="/api/reservas", tags=["Reservas (F-06)"])
Gestiona = Annotated[Usuario, Depends(requiere(Permiso.GESTIONAR_RESERVAS))]
ERRORES = {404: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta}, 422: {"model": ErrorRespuesta}}


@enrutador.get("", response_model=list[ReservaRespuesta])
def reservas_del_dia(fecha: date, _: Annotated[Usuario, Depends(requiere(Permiso.VER_RESERVAS))],
                     contenedor: ContenedorDep):
    return [ReservaRespuesta.en_agenda(a) for a in contenedor.reservas().del_dia(fecha)]


@enrutador.post("", response_model=ReservaRespuesta, status_code=status.HTTP_201_CREATED,
                responses=ERRORES)
async def crear_reserva(solicitud: ReservaSolicitud, usuario: Gestiona, contenedor: ContenedorDep):
    return ReservaRespuesta.desde(await contenedor.reservas().crear(solicitud.a_datos(), usuario))


@enrutador.put("/{reserva_id}", response_model=ReservaRespuesta, responses=ERRORES)
async def reprogramar_reserva(reserva_id: int, solicitud: ReprogramacionSolicitud, _: Gestiona,
                              contenedor: ContenedorDep):
    inicio = solicitud.inicio.replace(tzinfo=None, second=0, microsecond=0)
    reserva = await contenedor.reservas().modificar(
        reserva_id, inicio, solicitud.personas, solicitud.numero_mesa)
    return ReservaRespuesta.desde(reserva)


@enrutador.post("/{reserva_id}/llegada", response_model=ReservaRespuesta, responses=ERRORES)
async def confirmar_llegada(reserva_id: int, _: Gestiona, contenedor: ContenedorDep):
    return ReservaRespuesta.desde(await contenedor.reservas().confirmar_llegada(reserva_id))


@enrutador.post("/{reserva_id}/cancelar", response_model=ReservaRespuesta, responses=ERRORES)
async def cancelar_reserva(reserva_id: int, _: Gestiona, contenedor: ContenedorDep):
    return ReservaRespuesta.desde(await contenedor.reservas().cancelar(reserva_id))


@enrutador.post("/{reserva_id}/no-asistio", response_model=ReservaRespuesta, responses=ERRORES)
async def marcar_no_asistio(reserva_id: int, _: Gestiona, contenedor: ContenedorDep):
    return ReservaRespuesta.desde(await contenedor.reservas().marcar_no_asistio(reserva_id))
