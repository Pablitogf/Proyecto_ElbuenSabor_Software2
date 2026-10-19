from app.dominio.usuario import PERMISOS_POR_ROL, Rol, Usuario
from app.presentacion.esquemas.base import Esquema


class InicioSesionSolicitud(Esquema):
    nombre_usuario: str
    pin: str


class UsuarioRespuesta(Esquema):
    id: int
    nombre: str
    nombre_usuario: str
    rol: Rol
    permisos: list[str]

    @classmethod
    def desde(cls, usuario: Usuario) -> "UsuarioRespuesta":
        return cls(id=usuario.id, nombre=usuario.nombre, nombre_usuario=usuario.nombre_usuario,
                   rol=usuario.rol, permisos=sorted(p.name for p in PERMISOS_POR_ROL[usuario.rol]))


class SesionRespuesta(Esquema):
    token: str
    usuario: UsuarioRespuesta
