"""Eventos de dominio (patrón Observer / Publicar-Suscribir).

Los casos de uso publican "qué pasó" sin saber quién escucha. Hoy los escucha el
adaptador de WebSockets para refrescar las pantallas; mañana podría escucharlos
un servicio de correo o de analítica sin tocar los casos de uso.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventoDeDominio:
    @property
    def tipo(self) -> str:
        return type(self).__name__


@dataclass(frozen=True)
class PedidoRegistrado(EventoDeDominio):
    pedido_id: int
    numero_mesa: int


@dataclass(frozen=True)
class EstadoDePedidoCambiado(EventoDeDominio):
    pedido_id: int
    numero_mesa: int
    estado: str


@dataclass(frozen=True)
class PedidoListoParaServir(EventoDeDominio):
    """RF-04: el mesero debe recibir la notificación."""

    pedido_id: int
    numero_mesa: int


@dataclass(frozen=True)
class MesasActualizadas(EventoDeDominio):
    numeros: tuple[int, ...]


@dataclass(frozen=True)
class StockBajoMinimo(EventoDeDominio):
    """RF-14: alerta al administrador."""

    ingrediente_id: int
    nombre: str
    stock: float
    stock_minimo: float
    unidad: str


@dataclass(frozen=True)
class InventarioActualizado(EventoDeDominio):
    pass


@dataclass(frozen=True)
class CuentaCobrada(EventoDeDominio):
    pedido_id: int
    numero_mesa: int
    total: int


@dataclass(frozen=True)
class FacturaActualizada(EventoDeDominio):
    factura_id: int
    numero: str
    estado: str


@dataclass(frozen=True)
class ReservasActualizadas(EventoDeDominio):
    pass


@dataclass(frozen=True)
class JornadaActualizada(EventoDeDominio):
    estado: str


@dataclass(frozen=True)
class DatosReiniciados(EventoDeDominio):
    pass
