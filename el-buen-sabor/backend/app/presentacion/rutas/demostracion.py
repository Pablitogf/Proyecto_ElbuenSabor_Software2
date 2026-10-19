from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dominio.eventos import DatosReiniciados
from app.dominio.usuario import Permiso, Usuario
from app.infraestructura.base_de_datos.datos_iniciales import reiniciar_base_de_datos
from app.presentacion.dependencias import ContenedorDep, requiere
from app.presentacion.esquemas.base import Esquema

enrutador = APIRouter(prefix="/api/demostracion", tags=["Demostración"])
Administra = Annotated[Usuario, Depends(requiere(Permiso.ADMINISTRAR_SISTEMA))]


class SimuladorEsquema(Esquema):
    dian_disponible: bool
    rechazar_proxima_tarjeta: bool


@enrutador.get("/simulador", response_model=SimuladorEsquema)
def estado_simulador(_: Administra, contenedor: ContenedorDep):
    s = contenedor.simulador
    return SimuladorEsquema(dian_disponible=s.dian_disponible,
                            rechazar_proxima_tarjeta=s.rechazar_proxima_tarjeta)


@enrutador.put("/simulador", response_model=SimuladorEsquema)
def configurar_simulador(solicitud: SimuladorEsquema, _: Administra, contenedor: ContenedorDep):
    """Permite mostrar en vivo la caída de la DIAN y el rechazo de una tarjeta."""
    contenedor.simulador.dian_disponible = solicitud.dian_disponible
    contenedor.simulador.rechazar_proxima_tarjeta = solicitud.rechazar_proxima_tarjeta
    return solicitud


@enrutador.post("/reiniciar", status_code=status.HTTP_204_NO_CONTENT)
async def reiniciar_datos(_: Administra, contenedor: ContenedorDep) -> None:
    reiniciar_base_de_datos(contenedor.motor, contenedor.reloj.ahora())
    contenedor.simulador.dian_disponible = True
    contenedor.simulador.rechazar_proxima_tarjeta = False
    await contenedor.bus.publicar(DatosReiniciados())
