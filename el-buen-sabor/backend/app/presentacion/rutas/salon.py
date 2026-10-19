from typing import Annotated

from fastapi import APIRouter, Depends

from app.dominio.usuario import Permiso, Usuario
from app.presentacion.dependencias import ContenedorDep, requiere
from app.presentacion.esquemas.pedidos import MesaRespuesta, PedidoRespuesta, PlatoRespuesta

enrutador = APIRouter(prefix="/api", tags=["Salón"])
PuedeVerSalon = Annotated[Usuario, Depends(requiere(Permiso.VER_SALON))]


@enrutador.get("/mesas", response_model=list[MesaRespuesta])
def listar_mesas(_: PuedeVerSalon, contenedor: ContenedorDep):
    return [MesaRespuesta.desde(mesa) for mesa in contenedor.salon().mesas()]


@enrutador.get("/mesas/{numero}/pedido", response_model=PedidoRespuesta | None)
def pedido_de_mesa(numero: int, _: PuedeVerSalon, contenedor: ContenedorDep):
    pedido = contenedor.pedidos().en_servicio_de_mesa(numero)
    return PedidoRespuesta.desde(pedido) if pedido else None


@enrutador.get("/menu", response_model=list[PlatoRespuesta])
def consultar_menu(_: PuedeVerSalon, contenedor: ContenedorDep):
    return [PlatoRespuesta.desde(plato) for plato in contenedor.salon().menu()]
