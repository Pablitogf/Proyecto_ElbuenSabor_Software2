from dataclasses import dataclass
from datetime import datetime

from app.dominio.estados_pedido import (
    ESTADOS_EN_SERVICIO,
    NOMBRE_LEGIBLE,
    EstadoDePedido,
    EstadoPedido,
    comportamiento_de,
)
from app.dominio.excepciones import (
    CantidadInvalidaError,
    PedidoVacioError,
    PlatoNoPerteneceAlPedidoError,
    PlatosSinPrepararError,
    TransicionDeEstadoInvalidaError,
)


@dataclass
class DetallePedido:
    producto_id: int
    nombre_producto: str
    cantidad: int
    precio_unitario: int
    preparado: bool = False

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise CantidadInvalidaError(self.cantidad)

    @property
    def subtotal(self) -> int:
        return self.cantidad * self.precio_unitario


@dataclass
class Pedido:
    """Raíz de agregado. Toda mutación pasa por sus métodos, que delegan en el
    patrón State (`estados_pedido.py`) para validar la transición."""

    numero_mesa: int
    detalles: list[DetallePedido]
    fecha_hora: datetime
    mesero_id: int
    jornada_id: int
    estado: EstadoPedido = EstadoPedido.REGISTRADO
    hora_listo: datetime | None = None
    motivo_cancelacion: str | None = None
    id: int | None = None

    # ── Creación (Factory Method, Contrato 1: crearPedido) ─────────────────────
    @classmethod
    def registrar(
        cls,
        numero_mesa: int,
        detalles: list[DetallePedido],
        ahora: datetime,
        mesero_id: int,
        jornada_id: int,
    ) -> "Pedido":
        if not detalles:
            raise PedidoVacioError()
        return cls(
            numero_mesa=numero_mesa,
            detalles=detalles,
            fecha_hora=ahora,
            mesero_id=mesero_id,
            jornada_id=jornada_id,
        )

    # ── Consultas ──────────────────────────────────────────────────────────────
    @property
    def total(self) -> int:
        """RF-06: el total siempre se calcula, nunca se guarda a mano."""
        return sum(detalle.subtotal for detalle in self.detalles)

    @property
    def cantidad_de_platos(self) -> int:
        return sum(detalle.cantidad for detalle in self.detalles)

    @property
    def esta_en_servicio(self) -> bool:
        return self.estado in ESTADOS_EN_SERVICIO

    @property
    def platos_pendientes(self) -> list[str]:
        return [detalle.nombre_producto for detalle in self.detalles if not detalle.preparado]

    # ── Transiciones (F-05 cocina / mesero) ────────────────────────────────────
    def iniciar_preparacion(self) -> None:
        """Contrato 2: actualizarEstado(idPedido, 'En Preparación')."""
        self.estado = self._comportamiento.iniciar_preparacion()

    def marcar_plato(self, producto_id: int, preparado: bool) -> None:
        if not self._comportamiento.permite_marcar_platos:
            raise TransicionDeEstadoInvalidaError("marcar platos", NOMBRE_LEGIBLE[self.estado])
        self._detalle(producto_id).preparado = preparado

    def marcar_listo(self, ahora: datetime) -> None:
        """Regla: la cocina no puede despachar un pedido con platos sin preparar."""
        if self.estado == EstadoPedido.EN_PREPARACION and self.platos_pendientes:
            raise PlatosSinPrepararError(self.platos_pendientes)
        self.estado = self._comportamiento.marcar_listo()
        self.hora_listo = ahora

    def entregar(self) -> None:
        """RF-04: el mesero confirma que sirvió; la notificación desaparece."""
        self.estado = self._comportamiento.entregar()

    def cancelar(self, motivo: str) -> None:
        """Solo antes de que cocina empiece (error de digitación)."""
        self.estado = self._comportamiento.cancelar()
        self.motivo_cancelacion = motivo.strip() or "Sin motivo"

    # ── Transiciones (F-02 / F-03 caja) ────────────────────────────────────────
    def registrar_pago(self) -> None:
        """Contrato 3, precondición: solo se cobra un pedido entregado."""
        self.estado = self._comportamiento.registrar_pago()

    def facturar(self) -> None:
        """RD-05: el pedido se cierra solo cuando la DIAN valida la factura."""
        self.estado = self._comportamiento.facturar()

    # ── Internos ───────────────────────────────────────────────────────────────
    @property
    def _comportamiento(self) -> EstadoDePedido:
        return comportamiento_de(self.estado)

    def _detalle(self, producto_id: int) -> DetallePedido:
        for detalle in self.detalles:
            if detalle.producto_id == producto_id:
                return detalle
        raise PlatoNoPerteneceAlPedidoError(producto_id, self.id or 0)
