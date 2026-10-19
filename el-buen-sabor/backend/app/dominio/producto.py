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
    """Cantidad de un ingrediente que consume UNA porción del producto (RF-05)."""

    ingrediente_id: int
    cantidad_por_porcion: float


@dataclass
class ProductoMenu:
    id: int
    nombre: str
    descripcion: str
    precio: int  # Pesos colombianos, impuestos incluidos (precio al público).
    categoria: Categoria
    icono: str
    activo: bool = True
    receta: list[IngredienteDeReceta] = field(default_factory=list)
