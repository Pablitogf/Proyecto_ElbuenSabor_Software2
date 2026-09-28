from typing import Self

from sqlalchemy.orm import Session

from app.infraestructura.base_de_datos.conexion import FabricaDeSesiones
from app.infraestructura.base_de_datos.repositorios import (
    RepositorioIngredientesSQL,
    RepositorioMesasSQL,
    RepositorioPedidosSQL,
    RepositorioProductosSQL,
)


class UnidadDeTrabajoSQL:
    """Abre una sesión por operación. Si algo falla antes de `confirmar()`,
    todos los cambios se descartan (el inventario y la mesa quedan intactos)."""

    def __init__(self, fabrica_de_sesiones: FabricaDeSesiones) -> None:
        self._fabrica_de_sesiones = fabrica_de_sesiones
        self._sesion: Session | None = None

    def __enter__(self) -> Self:
        self._sesion = self._fabrica_de_sesiones()
        self.mesas = RepositorioMesasSQL(self._sesion)
        self.productos = RepositorioProductosSQL(self._sesion)
        self.ingredientes = RepositorioIngredientesSQL(self._sesion)
        self.pedidos = RepositorioPedidosSQL(self._sesion)
        return self

    def __exit__(self, *args: object) -> None:
        self._sesion.rollback()  # Sin efecto si ya se confirmó.
        self._sesion.close()

    def confirmar(self) -> None:
        self._sesion.commit()
