"""Errores de negocio. Cada uno expresa una regla del dominio que se violó."""


class ErrorDeDominio(Exception):
    """Base de todos los errores de negocio del restaurante."""


class RecursoNoEncontradoError(ErrorDeDominio):
    """Se buscó una entidad que no existe."""


class ReglaDeNegocioError(ErrorDeDominio):
    """La operación es válida en forma, pero viola una regla del negocio."""


class MesaNoEncontradaError(RecursoNoEncontradoError):
    def __init__(self, numero_mesa: int) -> None:
        super().__init__(f"La mesa {numero_mesa} no existe.")


class ProductoNoEncontradoError(RecursoNoEncontradoError):
    def __init__(self, producto_id: int) -> None:
        super().__init__(f"El producto {producto_id} no existe en el menú.")


class MesaNoDisponibleError(ReglaDeNegocioError):
    """RD-01: una mesa ocupada no puede recibir un nuevo pedido."""

    def __init__(self, numero_mesa: int) -> None:
        super().__init__(f"La mesa {numero_mesa} no está disponible para un nuevo pedido.")


class PedidoVacioError(ReglaDeNegocioError):
    """RD-02: todo pedido debe tener al menos un plato."""

    def __init__(self) -> None:
        super().__init__("El pedido debe contener al menos un plato.")


class CantidadInvalidaError(ReglaDeNegocioError):
    def __init__(self, cantidad: int) -> None:
        super().__init__(f"La cantidad {cantidad} no es válida; debe ser mayor que cero.")


class ProductoInactivoError(ReglaDeNegocioError):
    """RD-02: solo se pueden pedir productos activos en el menú."""

    def __init__(self, nombre_producto: str) -> None:
        super().__init__(f"El plato '{nombre_producto}' no está activo en el menú.")


class StockInsuficienteError(ReglaDeNegocioError):
    """RF-03: no hay ingredientes suficientes para preparar el pedido."""

    def __init__(self, nombre_ingrediente: str) -> None:
        self.nombre_ingrediente = nombre_ingrediente
        super().__init__(
            f"No hay suficiente '{nombre_ingrediente}' en inventario para preparar el pedido."
        )
