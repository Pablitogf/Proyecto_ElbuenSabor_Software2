"""Inventario de ingredientes (F-04, RF-03, RF-05, RF-14, RF-17)."""

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.dominio.excepciones import (
    CantidadInvalidaError,
    DatoInvalidoError,
    StockInsuficienteError,
)
from app.dominio.producto import ProductoMenu

UNIDADES_PERMITIDAS = ("g", "ml", "und")


class TipoMovimiento(str, Enum):
    ENTRADA = "ENTRADA"                # Llegó mercancía del proveedor.
    SALIDA_PEDIDO = "SALIDA_PEDIDO"    # Consumo automático al confirmar un pedido.
    DEVOLUCION = "DEVOLUCION"          # Reingreso al cancelar un pedido.
    MERMA = "MERMA"                    # Pérdida: vencimiento, daño, derrame…


class MotivoMerma(str, Enum):
    VENCIMIENTO = "VENCIMIENTO"
    DANO = "DANO"
    DERRAME = "DERRAME"
    OTRO = "OTRO"


@dataclass
class Ingrediente:
    id: int | None
    nombre: str
    unidad: str
    stock: float
    stock_minimo: float

    @classmethod
    def crear(cls, nombre: str, unidad: str, stock_minimo: float) -> "Ingrediente":
        nombre_limpio = " ".join(nombre.split())
        if not nombre_limpio:
            raise DatoInvalidoError("El ingrediente necesita un nombre.")
        if unidad not in UNIDADES_PERMITIDAS:
            raise DatoInvalidoError(f"Unidad '{unidad}' no válida. Usa: {', '.join(UNIDADES_PERMITIDAS)}.")
        ingrediente = cls(id=None, nombre=nombre_limpio, unidad=unidad, stock=0, stock_minimo=0)
        ingrediente.cambiar_minimo(stock_minimo)
        return ingrediente

    @property
    def esta_bajo_minimo(self) -> bool:
        """RF-14: se alerta cuando el stock llega (o baja de) el mínimo."""
        return self.stock <= self.stock_minimo

    def alcanza_para(self, cantidad: float) -> bool:
        return self.stock >= cantidad

    def descontar(self, cantidad: float) -> None:
        if not self.alcanza_para(cantidad):
            raise StockInsuficienteError(self.nombre)
        self.stock -= cantidad

    def reponer(self, cantidad: float) -> None:
        _exigir_positiva(cantidad)
        self.stock += cantidad

    def registrar_merma(self, cantidad: float) -> None:
        """No se puede perder más de lo que hay."""
        _exigir_positiva(cantidad)
        self.descontar(cantidad)

    def cambiar_minimo(self, nuevo_minimo: float) -> None:
        if nuevo_minimo < 0:
            raise DatoInvalidoError("El nivel mínimo no puede ser negativo.")
        self.stock_minimo = nuevo_minimo


@dataclass
class MovimientoInventario:
    """Kardex: cada cambio de stock queda registrado con fecha y causa (RF-17)."""

    ingrediente_id: int
    tipo: TipoMovimiento
    cantidad: float
    fecha_hora: datetime
    usuario_id: int | None = None
    proveedor: str | None = None
    motivo: MotivoMerma | None = None
    detalle: str | None = None
    pedido_id: int | None = None
    id: int | None = None

    @classmethod
    def entrada(cls, ingrediente_id: int, cantidad: float, proveedor: str, ahora: datetime,
                usuario_id: int) -> "MovimientoInventario":
        """RF-17: cada entrada debe tener ingrediente, cantidad, fecha y proveedor."""
        _exigir_positiva(cantidad)
        proveedor_limpio = proveedor.strip()
        if not proveedor_limpio:
            raise DatoInvalidoError("Indica el proveedor de la entrada.")
        return cls(ingrediente_id, TipoMovimiento.ENTRADA, cantidad, ahora,
                   usuario_id=usuario_id, proveedor=proveedor_limpio)

    @classmethod
    def merma(cls, ingrediente_id: int, cantidad: float, motivo: MotivoMerma, detalle: str,
              ahora: datetime, usuario_id: int) -> "MovimientoInventario":
        _exigir_positiva(cantidad)
        if motivo == MotivoMerma.OTRO and not detalle.strip():
            raise DatoInvalidoError("Describe la causa de la pérdida cuando el motivo es 'Otro'.")
        return cls(ingrediente_id, TipoMovimiento.MERMA, cantidad, ahora,
                   usuario_id=usuario_id, motivo=motivo, detalle=detalle.strip() or None)


@dataclass(frozen=True)
class ResultadoConsumo:
    consumo_por_ingrediente: dict[int, float]
    ingredientes_que_cruzaron_minimo: list[Ingrediente]


class Inventario:
    """Servicio de dominio sobre el conjunto de ingredientes."""

    def __init__(self, ingredientes: list[Ingrediente]) -> None:
        self._ingredientes = {ingrediente.id: ingrediente for ingrediente in ingredientes}

    def porciones_disponibles(self, producto: ProductoMenu) -> int:
        """RF-03: cuántas porciones se pueden preparar con el stock actual."""
        if not producto.receta:
            return 0
        return min(
            math.floor(self._ingredientes[item.ingrediente_id].stock / item.cantidad_por_porcion)
            for item in producto.receta
        )

    def consumir(self, porciones_por_producto: list[tuple[ProductoMenu, int]]) -> ResultadoConsumo:
        """RF-05. Valida TODO antes de descontar, para no dejar el inventario a medias."""
        consumo = self._calcular_consumo(porciones_por_producto)
        self._verificar_existencias(consumo)
        cruzaron: list[Ingrediente] = []
        for ingrediente_id, cantidad in consumo.items():
            ingrediente = self._ingredientes[ingrediente_id]
            estaba_bien = not ingrediente.esta_bajo_minimo
            ingrediente.descontar(cantidad)
            if estaba_bien and ingrediente.esta_bajo_minimo:
                cruzaron.append(ingrediente)
        return ResultadoConsumo(consumo, cruzaron)

    def devolver(self, consumo: dict[int, float]) -> None:
        """Al cancelar un pedido, los ingredientes vuelven al inventario."""
        for ingrediente_id, cantidad in consumo.items():
            self._ingredientes[ingrediente_id].reponer(cantidad)

    def ingredientes(self) -> list[Ingrediente]:
        return list(self._ingredientes.values())

    @staticmethod
    def _calcular_consumo(porciones_por_producto: list[tuple[ProductoMenu, int]]) -> dict[int, float]:
        consumo: dict[int, float] = defaultdict(float)
        for producto, porciones in porciones_por_producto:
            for item in producto.receta:
                consumo[item.ingrediente_id] += item.cantidad_por_porcion * porciones
        return dict(consumo)

    def _verificar_existencias(self, consumo: dict[int, float]) -> None:
        for ingrediente_id, cantidad in consumo.items():
            ingrediente = self._ingredientes[ingrediente_id]
            if not ingrediente.alcanza_para(cantidad):
                raise StockInsuficienteError(ingrediente.nombre)


def _exigir_positiva(cantidad: float) -> None:
    """CU-04 4a: una cantidad cero o negativa es un error."""
    if cantidad <= 0:
        raise CantidadInvalidaError(cantidad)
