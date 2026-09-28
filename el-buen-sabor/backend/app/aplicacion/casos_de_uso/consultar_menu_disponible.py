from dataclasses import dataclass

from app.aplicacion.puertos import UnidadDeTrabajo
from app.dominio.inventario import Inventario
from app.dominio.producto import ProductoMenu


@dataclass(frozen=True)
class PlatoDelMenu:
    producto: ProductoMenu
    porciones_disponibles: int

    @property
    def disponible(self) -> bool:
        return self.producto.activo and self.porciones_disponibles > 0


class ConsultarMenuDisponible:
    """SWR-01 / RF-03: muestra el menú indicando qué platos se pueden preparar
    según el stock de ingredientes."""

    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo) -> None:
        self._uow = unidad_de_trabajo

    def ejecutar(self) -> list[PlatoDelMenu]:
        with self._uow:
            inventario = Inventario(self._uow.ingredientes.listar())
            return [
                PlatoDelMenu(producto, inventario.porciones_disponibles(producto))
                for producto in self._uow.productos.listar()
            ]
