"""Errores de negocio. Cada clase nombra una regla del dominio que se violó.

La capa de presentación traduce cada familia a un código HTTP en un solo lugar
(`presentacion/manejo_de_errores.py`); el dominio nunca conoce HTTP.
"""


class ErrorDeDominio(Exception):
    """Base de todos los errores de negocio del restaurante."""


# ── Familias (cada una tiene un código HTTP asignado en presentación) ─────────
class RecursoNoEncontradoError(ErrorDeDominio):
    """Se buscó una entidad que no existe (404)."""


class DatoInvalidoError(ErrorDeDominio):
    """Un dato de entrada no cumple el formato o rango permitido (422)."""


class ReglaDeNegocioError(ErrorDeDominio):
    """La operación tiene forma válida pero viola una regla del negocio (409)."""


class AccesoDenegadoError(ErrorDeDominio):
    """El usuario autenticado no tiene permiso para la operación (403)."""


class AutenticacionError(ErrorDeDominio):
    """No hay sesión válida o las credenciales son incorrectas (401)."""


class ServicioExternoError(ErrorDeDominio):
    """Un sistema externo (DIAN, banco) no respondió como se esperaba (502)."""


# ── No encontrados ─────────────────────────────────────────────────────────────
class MesaNoEncontradaError(RecursoNoEncontradoError):
    def __init__(self, numero_mesa: int) -> None:
        super().__init__(f"La mesa {numero_mesa} no existe.")


class ProductoNoEncontradoError(RecursoNoEncontradoError):
    def __init__(self, producto_id: int) -> None:
        super().__init__(f"El producto {producto_id} no existe en el menú.")


class PedidoNoEncontradoError(RecursoNoEncontradoError):
    def __init__(self, pedido_id: int) -> None:
        super().__init__(f"El pedido {pedido_id} no existe.")


class IngredienteNoEncontradoError(RecursoNoEncontradoError):
    def __init__(self, ingrediente_id: int) -> None:
        super().__init__(f"El ingrediente {ingrediente_id} no existe.")


class ReservaNoEncontradaError(RecursoNoEncontradoError):
    def __init__(self, reserva_id: int) -> None:
        super().__init__(f"La reserva {reserva_id} no existe.")


class FacturaNoEncontradaError(RecursoNoEncontradoError):
    def __init__(self, factura_id: int) -> None:
        super().__init__(f"La factura {factura_id} no existe.")


# ── Pedidos (F-01, F-05) ───────────────────────────────────────────────────────
class MesaNoDisponibleError(ReglaDeNegocioError):
    """RD-01: una mesa ocupada no puede recibir un nuevo pedido ni una reserva inmediata."""

    def __init__(self, numero_mesa: int) -> None:
        super().__init__(f"La mesa {numero_mesa} no está disponible.")


class MesaReservadaError(ReglaDeNegocioError):
    """F-06: la mesa está apartada para una reserva que está por llegar."""

    def __init__(self, numero_mesa: int, nombre_cliente: str) -> None:
        super().__init__(
            f"La mesa {numero_mesa} está reservada para {nombre_cliente}. "
            "Confirma su llegada en Reservas antes de tomar el pedido."
        )


class PedidoVacioError(ReglaDeNegocioError):
    """RD-02: todo pedido debe tener al menos un plato."""

    def __init__(self) -> None:
        super().__init__("El pedido debe contener al menos un plato.")


class CantidadInvalidaError(DatoInvalidoError):
    def __init__(self, cantidad: float) -> None:
        super().__init__(f"La cantidad {cantidad:g} no es válida; debe ser mayor que cero.")


class ProductoInactivoError(ReglaDeNegocioError):
    """RD-02: solo se pueden pedir productos activos en el menú."""

    def __init__(self, nombre_producto: str) -> None:
        super().__init__(f"El plato '{nombre_producto}' no está activo en el menú.")


class TransicionDeEstadoInvalidaError(ReglaDeNegocioError):
    """RD-03: el ciclo de vida del pedido no permite esa acción en su estado actual."""

    def __init__(self, accion: str, estado_actual: str) -> None:
        super().__init__(f"No se puede {accion}: el pedido está '{estado_actual}'.")


class PlatosSinPrepararError(ReglaDeNegocioError):
    """F-05: un pedido solo queda listo cuando todos sus platos están preparados."""

    def __init__(self, pendientes: list[str]) -> None:
        super().__init__(f"Faltan platos por preparar: {', '.join(pendientes)}.")


class PlatoNoPerteneceAlPedidoError(RecursoNoEncontradoError):
    def __init__(self, producto_id: int, pedido_id: int) -> None:
        super().__init__(f"El plato {producto_id} no hace parte del pedido {pedido_id}.")


# ── Inventario (F-04) ──────────────────────────────────────────────────────────
class StockInsuficienteError(ReglaDeNegocioError):
    """RF-03: no hay ingredientes suficientes."""

    def __init__(self, nombre_ingrediente: str) -> None:
        self.nombre_ingrediente = nombre_ingrediente
        super().__init__(f"No hay suficiente '{nombre_ingrediente}' en inventario.")


class IngredienteDuplicadoError(ReglaDeNegocioError):
    def __init__(self, nombre: str) -> None:
        super().__init__(f"Ya existe un ingrediente llamado '{nombre}'.")


# ── Caja y facturación (F-02, F-03) ────────────────────────────────────────────
class PagoInvalidoError(DatoInvalidoError):
    """El desglose del pago no cuadra con la cuenta."""


class PagoRechazadoError(ReglaDeNegocioError):
    """RF-08 / CU-02 5a: la entidad bancaria rechazó la tarjeta."""

    def __init__(self, motivo: str) -> None:
        super().__init__(f"Pago con tarjeta rechazado: {motivo}. Intenta con otro medio de pago.")


class ResolucionAgotadaError(ReglaDeNegocioError):
    """La numeración autorizada por la DIAN se agotó."""

    def __init__(self, hasta: int) -> None:
        super().__init__(
            f"Se agotó el rango de numeración autorizado por la DIAN (hasta {hasta}). "
            "Solicita una nueva resolución."
        )


class FacturaYaValidadaError(ReglaDeNegocioError):
    def __init__(self, numero: str) -> None:
        super().__init__(f"La factura {numero} ya fue validada por la DIAN.")


# ── Jornada / cierre de caja (F-02, RF-10, RF-11) ──────────────────────────────
class JornadaCerradaError(ReglaDeNegocioError):
    """M-02 / E-08: con la caja cerrada no se aceptan pedidos ni cobros."""

    def __init__(self) -> None:
        super().__init__("La caja está cerrada. El administrador debe abrir una nueva jornada.")


class JornadaYaAbiertaError(ReglaDeNegocioError):
    def __init__(self) -> None:
        super().__init__("Ya hay una jornada abierta.")


class CierreBloqueadoError(ReglaDeNegocioError):
    """CU-02 9a / CU-06 9a: hay condiciones que impiden cerrar la caja."""

    def __init__(self, motivos: list[str]) -> None:
        self.motivos = motivos
        super().__init__("No se puede cerrar la caja: " + " ".join(motivos))


class InconsistenciasSinConfirmarError(ReglaDeNegocioError):
    """RF-11: el administrador debe revisar y confirmar cada inconsistencia."""

    def __init__(self, cantidad: int) -> None:
        super().__init__(
            f"Hay {cantidad} inconsistencia(s) en el cuadre. Revísalas, escribe una "
            "observación y confirma para cerrar."
        )


# ── Reservas (F-06) ────────────────────────────────────────────────────────────
class ReservaInvalidaError(DatoInvalidoError):
    """Datos de la reserva fuera de las políticas del restaurante."""


class SinMesasParaReservaError(ReglaDeNegocioError):
    """CU-05 6a: no hay mesa libre para ese horario y número de personas."""

    def __init__(self, personas: int, hora: str) -> None:
        super().__init__(f"No hay mesas libres para {personas} persona(s) a las {hora}.")


class ConflictoDeReservaError(ReglaDeNegocioError):
    """RF-16: no puede haber dos reservas en la misma mesa a la misma hora."""

    def __init__(self, numero_mesa: int, hora: str) -> None:
        super().__init__(f"La mesa {numero_mesa} ya tiene una reserva que se cruza con las {hora}.")


class AccionDeReservaInvalidaError(ReglaDeNegocioError):
    """La reserva no está en un estado o momento que permita la acción."""


# ── Seguridad (RNF-04) ─────────────────────────────────────────────────────────
class CredencialesInvalidasError(AutenticacionError):
    def __init__(self) -> None:
        super().__init__("Usuario o PIN incorrectos.")


class SesionInvalidaError(AutenticacionError):
    def __init__(self) -> None:
        super().__init__("Tu sesión expiró o no es válida. Vuelve a ingresar.")


class PermisoDenegadoError(AccesoDenegadoError):
    def __init__(self, rol: str, accion: str) -> None:
        super().__init__(f"El rol {rol} no tiene permiso para {accion}.")


# ── Integraciones ──────────────────────────────────────────────────────────────
class PasarelaNoDisponibleError(ServicioExternoError):
    def __init__(self) -> None:
        super().__init__("La pasarela bancaria no responde. Intenta de nuevo o cobra en efectivo.")
