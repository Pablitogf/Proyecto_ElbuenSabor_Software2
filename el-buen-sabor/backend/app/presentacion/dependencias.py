"""Dependencias de FastAPI: contenedor, usuario autenticado y RBAC por permiso."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.contenedor import Contenedor
from app.dominio.usuario import Permiso, Usuario

_esquema_bearer = HTTPBearer(auto_error=False)


def obtener_contenedor(request: Request) -> Contenedor:
    return request.app.state.contenedor


ContenedorDep = Annotated[Contenedor, Depends(obtener_contenedor)]


def usuario_actual(
    contenedor: ContenedorDep,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_esquema_bearer)],
) -> Usuario:
    """RF-01: toda operación exige un usuario autenticado."""
    return contenedor.sesion().usuario_de(credenciales.credentials if credenciales else None)


UsuarioDep = Annotated[Usuario, Depends(usuario_actual)]


def requiere(permiso: Permiso) -> Callable[..., Usuario]:
    """RNF-04: se usa como `usuario: Annotated[Usuario, Depends(requiere(Permiso.COBRAR))]`."""

    def verificar(usuario: UsuarioDep) -> Usuario:
        usuario.exigir(permiso)
        return usuario

    return verificar
