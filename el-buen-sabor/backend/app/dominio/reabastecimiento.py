"""Sugerencia de compra (RF-12) con patrón Strategy.

La política por defecto proyecta el consumo promedio de los últimos días. Si el
restaurante quiere otra forma de calcular (estacionalidad por día de la semana,
vida útil…), se agrega otra clase con el mismo método `sugerir` sin tocar el
caso de uso.
"""

import math
from dataclasses import dataclass
from typing import Protocol

from app.dominio.inventario import Ingrediente


@dataclass(frozen=True)
class SugerenciaCompra:
    ingrediente: Ingrediente
    consumo_diario: float
    dias_restantes: float | None
    cantidad_sugerida: float


class PoliticaReabastecimiento(Protocol):
    def sugerir(self, ingrediente: Ingrediente, consumo_en_periodo: float) -> SugerenciaCompra | None: ...


class CoberturaPorConsumoPromedio:
    """Comprar lo necesario para cubrir `dias_cobertura` días más el stock mínimo."""

    def __init__(self, dias_historial: int = 7, dias_cobertura: int = 3) -> None:
        self.dias_historial = dias_historial
        self.dias_cobertura = dias_cobertura

    def sugerir(self, ingrediente: Ingrediente, consumo_en_periodo: float) -> SugerenciaCompra | None:
        consumo_diario = consumo_en_periodo / self.dias_historial
        objetivo = consumo_diario * self.dias_cobertura + ingrediente.stock_minimo
        # Sin historial, al menos se repone hasta el doble del mínimo.
        objetivo = max(objetivo, ingrediente.stock_minimo * 2)
        faltante = objetivo - ingrediente.stock
        if faltante <= 0:
            return None
        dias_restantes = ingrediente.stock / consumo_diario if consumo_diario > 0 else None
        return SugerenciaCompra(
            ingrediente=ingrediente,
            consumo_diario=round(consumo_diario, 1),
            dias_restantes=round(dias_restantes, 1) if dias_restantes is not None else None,
            cantidad_sugerida=_redondear_compra(faltante, ingrediente.unidad),
        )


def _redondear_compra(cantidad: float, unidad: str) -> float:
    """Los proveedores venden en múltiplos: unidades enteras o paquetes de 100 g/ml."""
    if unidad == "und":
        return float(math.ceil(cantidad))
    return float(math.ceil(cantidad / 100) * 100)
