from dataclasses import dataclass, field
from enum import Enum


class Categoria(str, Enum):
    BEBIDAS = "BEBIDAS"
    ENTRADAS = "ENTRADAS"
    PLATOS_PRINCIPALES = "PLATOS_PRINCIPALES"
    POSTRES = "POSTRES"
    LICORES = "LICORES"


@dataclass(frozen=True)
class IngredienteDeReceta:
    """Cantidad de un ingrediente que consume UNA porción del producto."""

    ingrediente_id: int
    cantidad_por_porcion: float


@dataclass
class ProductoMenu:
    id: int
    nombre: str
    descripcion: str
    precio: int  # Pesos colombianos (COP), sin decimales.
    categoria: Categoria
    icono: str
    activo: bool = True
    receta: list[IngredienteDeReceta] = field(default_factory=list)
