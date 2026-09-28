import math
from collections import defaultdict
from dataclasses import dataclass

from app.dominio.excepciones import StockInsuficienteError
from app.dominio.producto import ProductoMenu


@dataclass
class Ingrediente:
    id: int
    nombre: str
    unidad: str
    stock: float
    stock_minimo: float

    def alcanza_para(self, cantidad: float) -> bool:
        return self.stock >= cantidad

    def descontar(self, cantidad: float) -> None:
        if not self.alcanza_para(cantidad):
            raise StockInsuficienteError(self.nombre)
        self.stock -= cantidad


class Inventario:
    """Servicio de dominio que responde preguntas de disponibilidad (RF-03)
    y descuenta ingredientes al confirmar un pedido (RF-05)."""

    def __init__(self, ingredientes: list[Ingrediente]) -> None:
        self._ingredientes = {ingrediente.id: ingrediente for ingrediente in ingredientes}

    def porciones_disponibles(self, producto: ProductoMenu) -> int:
        """Cuántas porciones del producto se pueden preparar con el stock actual."""
        if not producto.receta:
            return 0
        return min(
            math.floor(self._ingredientes[item.ingrediente_id].stock / item.cantidad_por_porcion)
            for item in producto.receta
        )

    def consumir(self, porciones_por_producto: list[tuple[ProductoMenu, int]]) -> None:
        """Valida TODO el pedido antes de descontar, para no dejar el inventario a medias."""
        consumo_total = self._calcular_consumo_total(porciones_por_producto)
        self._verificar_existencias(consumo_total)
        for ingrediente_id, cantidad in consumo_total.items():
            self._ingredientes[ingrediente_id].descontar(cantidad)

    def ingredientes(self) -> list[Ingrediente]:
        return list(self._ingredientes.values())

    @staticmethod
    def _calcular_consumo_total(
        porciones_por_producto: list[tuple[ProductoMenu, int]],
    ) -> dict[int, float]:
        consumo: dict[int, float] = defaultdict(float)
        for producto, porciones in porciones_por_producto:
            for item in producto.receta:
                consumo[item.ingrediente_id] += item.cantidad_por_porcion * porciones
        return consumo

    def _verificar_existencias(self, consumo_total: dict[int, float]) -> None:
        for ingrediente_id, cantidad in consumo_total.items():
            ingrediente = self._ingredientes[ingrediente_id]
            if not ingrediente.alcanza_para(cantidad):
                raise StockInsuficienteError(ingrediente.nombre)
