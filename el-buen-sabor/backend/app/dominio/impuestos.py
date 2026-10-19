"""Cálculo del impuesto de la factura con patrón Strategy (F-03).

Los precios del menú son precios al público con impuesto incluido (en Colombia
el precio exhibido debe incluir impuestos), así que la factura DESGLOSA la base y
el impuesto a partir del total; nunca le suma impuesto al cliente.

El documento de análisis pide IVA 19% "o según tarifa vigente". Como los
restaurantes suelen liquidar el Impuesto Nacional al Consumo (INC) del 8%, ambas
estrategias existen y se elige una por configuración (`IMPUESTO_FACTURA`).
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Desglose:
    base: int
    impuesto: int

    @property
    def total(self) -> int:
        return self.base + self.impuesto


class CalculadoraImpuesto(Protocol):
    codigo_dian: str  # Código del tributo en el anexo técnico de la DIAN.
    nombre: str
    tarifa: float

    def desglosar(self, total_con_impuesto: int) -> Desglose: ...


@dataclass(frozen=True)
class ImpuestoIncluido:
    codigo_dian: str
    nombre: str
    tarifa: float

    def desglosar(self, total_con_impuesto: int) -> Desglose:
        base = round(total_con_impuesto / (1 + self.tarifa))
        return Desglose(base=base, impuesto=total_con_impuesto - base)


IVA_19 = ImpuestoIncluido(codigo_dian="01", nombre="IVA", tarifa=0.19)
IMPUESTO_CONSUMO_8 = ImpuestoIncluido(codigo_dian="04", nombre="INC", tarifa=0.08)

CALCULADORAS: dict[str, CalculadoraImpuesto] = {"IVA_19": IVA_19, "INC_8": IMPUESTO_CONSUMO_8}
