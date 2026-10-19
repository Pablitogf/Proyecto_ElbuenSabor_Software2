from fastapi import APIRouter

from app.dominio.excepciones import RecursoNoEncontradoError
from app.presentacion.dependencias import ContenedorDep, UsuarioDep
from app.presentacion.esquemas.base import Esquema
from app.presentacion.esquemas.sesion import InicioSesionSolicitud, SesionRespuesta, UsuarioRespuesta

enrutador = APIRouter(prefix="/api/sesion", tags=["Sesión"])


class UsuarioDemo(Esquema):
    nombre: str
    nombre_usuario: str
    rol: str


@enrutador.post("", response_model=SesionRespuesta)
def iniciar_sesion(solicitud: InicioSesionSolicitud, contenedor: ContenedorDep):
    token, usuario = contenedor.sesion().iniciar(solicitud.nombre_usuario, solicitud.pin)
    return SesionRespuesta(token=token, usuario=UsuarioRespuesta.desde(usuario))


@enrutador.get("/yo", response_model=UsuarioRespuesta)
def usuario_actual(usuario: UsuarioDep):
    return UsuarioRespuesta.desde(usuario)


@enrutador.get("/usuarios-demo", response_model=list[UsuarioDemo])
def usuarios_de_demostracion(contenedor: ContenedorDep):
    """Solo en modo demostración: la pantalla de ingreso muestra a quién elegir."""
    if not contenedor.configuracion.modo_demostracion:
        raise RecursoNoEncontradoError("No disponible.")
    return [UsuarioDemo(nombre=u.nombre, nombre_usuario=u.nombre_usuario, rol=u.rol.value)
            for u in contenedor.sesion().usuarios()]
