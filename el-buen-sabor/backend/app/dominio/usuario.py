"""Usuarios y Control de Acceso Basado en Roles (RBAC, RNF-04).

Los endpoints no preguntan "¿es administrador?": preguntan "¿tiene el permiso X?".
Así, cambiar quién puede hacer qué es editar una tabla, no buscar `if` por el código.
"""

from dataclasses import dataclass
from enum import Enum

from app.dominio.excepciones import PermisoDenegadoError


class Rol(str, Enum):
    MESERO = "MESERO"
    COCINERO = "COCINERO"
    CAJERO = "CAJERO"
    ADMINISTRADOR = "ADMINISTRADOR"


class Permiso(str, Enum):
    VER_SALON = "ver el salón y el menú"
    REGISTRAR_PEDIDO = "registrar pedidos"
    ATENDER_MESA = "entregar o cancelar pedidos"
    VER_COMANDAS = "ver las comandas"
    PREPARAR_PEDIDO = "cambiar el estado de preparación"
    COBRAR = "cobrar cuentas"
    VER_REGISTROS_CAJA = "ver los registros de caja"
    GESTIONAR_FACTURAS = "gestionar facturas electrónicas"
    CERRAR_CAJA = "ejecutar el cierre de caja"
    GESTIONAR_INVENTARIO = "gestionar el inventario"
    VER_RESERVAS = "consultar reservas"
    GESTIONAR_RESERVAS = "registrar y modificar reservas"
    ADMINISTRAR_SISTEMA = "administrar el sistema"


_PERMISOS_DEL_MESERO = {
    Permiso.VER_SALON,
    Permiso.REGISTRAR_PEDIDO,
    Permiso.ATENDER_MESA,
    Permiso.VER_RESERVAS,
    Permiso.GESTIONAR_RESERVAS,
}

PERMISOS_POR_ROL: dict[Rol, frozenset[Permiso]] = {
    Rol.MESERO: frozenset(_PERMISOS_DEL_MESERO),
    Rol.COCINERO: frozenset({Permiso.VER_COMANDAS, Permiso.PREPARAR_PEDIDO}),
    # RF-09: solo cajero y administrador acceden a los registros de caja.
    Rol.CAJERO: frozenset(
        {Permiso.COBRAR, Permiso.VER_REGISTROS_CAJA, Permiso.GESTIONAR_FACTURAS, Permiso.VER_SALON}
    ),
    # RF-10: el único rol que puede ejecutar el cierre de caja es el administrador.
    Rol.ADMINISTRADOR: frozenset(Permiso),
}


@dataclass
class Usuario:
    id: int
    nombre: str
    nombre_usuario: str
    rol: Rol
    hash_pin: str

    def puede(self, permiso: Permiso) -> bool:
        return permiso in PERMISOS_POR_ROL[self.rol]

    def exigir(self, permiso: Permiso) -> None:
        if not self.puede(permiso):
            raise PermisoDenegadoError(self.rol.value.lower(), permiso.value)
