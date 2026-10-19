"""Reservas de mesa (F-06, RF-16, CU-05)."""

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum

from app.dominio.excepciones import AccionDeReservaInvalidaError, ReservaInvalidaError

DURACION_RESERVA = timedelta(hours=2)
BLOQUEO_PREVIO = timedelta(minutes=30)       # La mesa se aparta 30 min antes.
TOLERANCIA_LLEGADA = timedelta(minutes=15)   # Después de esto es "no asistió".
ANTICIPACION_MINIMA = timedelta(minutes=15)
ANTICIPACION_MAXIMA = timedelta(days=30)
HORA_APERTURA = time(11, 0)                  # RNF-05: atención de 11:00 a 22:00.
ULTIMA_RESERVA = time(20, 0)                 # Para que la reserva termine al cierre.
MAXIMO_PERSONAS = 12
_TELEFONO_VALIDO = re.compile(r"^\d{7,10}$")


class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"
    CUMPLIDA = "CUMPLIDA"        # El cliente llegó y se le entregó la mesa.
    CANCELADA = "CANCELADA"
    NO_ASISTIO = "NO_ASISTIO"


@dataclass
class Reserva:
    nombre_cliente: str
    telefono: str
    personas: int
    inicio: datetime
    numero_mesa: int
    creada_por: int
    estado: EstadoReserva = EstadoReserva.PENDIENTE
    notas: str | None = None
    id: int | None = None

    # ── Creación y cambios ─────────────────────────────────────────────────────
    @classmethod
    def crear(cls, nombre_cliente: str, telefono: str, personas: int, inicio: datetime,
              numero_mesa: int, creada_por: int, ahora: datetime, notas: str = "") -> "Reserva":
        nombre = " ".join(nombre_cliente.split())
        telefono_limpio = re.sub(r"[\s-]", "", telefono)
        if len(nombre) < 3:
            raise ReservaInvalidaError("Escribe el nombre del cliente (mínimo 3 letras).")
        if not _TELEFONO_VALIDO.match(telefono_limpio):
            raise ReservaInvalidaError("El teléfono debe tener entre 7 y 10 dígitos.")
        validar_horario_y_personas(inicio, personas, ahora)
        return cls(nombre, telefono_limpio, personas, inicio, numero_mesa, creada_por,
                   notas=notas.strip() or None)

    def reprogramar(self, inicio: datetime, personas: int, numero_mesa: int, ahora: datetime) -> None:
        self._exigir_pendiente("modificar")
        validar_horario_y_personas(inicio, personas, ahora)
        self.inicio, self.personas, self.numero_mesa = inicio, personas, numero_mesa

    # ── Ciclo de vida ──────────────────────────────────────────────────────────
    def confirmar_llegada(self, ahora: datetime) -> None:
        """CU-05 paso 7: solo dentro de la ventana [inicio − 30 min, inicio + 15 min]."""
        self._exigir_pendiente("confirmar la llegada de")
        if ahora < self.inicio - BLOQUEO_PREVIO:
            raise AccionDeReservaInvalidaError(
                f"Es muy temprano: la reserva es a las {self.inicio:%H:%M}. "
                "Se puede confirmar desde 30 minutos antes."
            )
        if ahora > self.inicio + TOLERANCIA_LLEGADA:
            raise AccionDeReservaInvalidaError(
                "Pasaron más de 15 minutos de la hora reservada. Márcala como 'no asistió' "
                "y asigna una mesa libre."
            )
        self.estado = EstadoReserva.CUMPLIDA

    def cancelar(self) -> None:
        self._exigir_pendiente("cancelar")
        self.estado = EstadoReserva.CANCELADA

    def marcar_no_asistio(self, ahora: datetime) -> None:
        """CU-05 7a: solo cuando ya pasó la tolerancia de llegada."""
        self._exigir_pendiente("marcar como no asistida")
        if ahora <= self.inicio + TOLERANCIA_LLEGADA:
            raise AccionDeReservaInvalidaError("Aún está dentro de los 15 minutos de tolerancia.")
        self.estado = EstadoReserva.NO_ASISTIO

    # ── Consultas ──────────────────────────────────────────────────────────────
    @property
    def fin(self) -> datetime:
        return self.inicio + DURACION_RESERVA

    @property
    def esta_pendiente(self) -> bool:
        return self.estado == EstadoReserva.PENDIENTE

    def se_cruza_con(self, inicio: datetime) -> bool:
        """RF-16: dos reservas de 2 h en la misma mesa no pueden solaparse."""
        return self.esta_pendiente and inicio < self.fin and self.inicio < inicio + DURACION_RESERVA

    def aparta_la_mesa(self, ahora: datetime) -> bool:
        """La mesa se ve 'Reservada' desde 30 min antes hasta la tolerancia de llegada."""
        return (self.esta_pendiente
                and self.inicio - BLOQUEO_PREVIO <= ahora <= self.inicio + TOLERANCIA_LLEGADA)

    def esta_vencida(self, ahora: datetime) -> bool:
        return self.esta_pendiente and ahora > self.inicio + TOLERANCIA_LLEGADA

    def _exigir_pendiente(self, accion: str) -> None:
        if not self.esta_pendiente:
            raise AccionDeReservaInvalidaError(
                f"No se puede {accion} una reserva {self.estado.value.lower().replace('_', ' ')}."
            )


def validar_horario_y_personas(inicio: datetime, personas: int, ahora: datetime) -> None:
    if not 1 <= personas <= MAXIMO_PERSONAS:
        raise ReservaInvalidaError(f"El número de personas debe estar entre 1 y {MAXIMO_PERSONAS}.")
    if inicio < ahora + ANTICIPACION_MINIMA:
        raise ReservaInvalidaError("La reserva debe hacerse con al menos 15 minutos de anticipación.")
    if inicio > ahora + ANTICIPACION_MAXIMA:
        raise ReservaInvalidaError("Solo se reciben reservas hasta 30 días adelante.")
    if not HORA_APERTURA <= inicio.time() <= ULTIMA_RESERVA:
        raise ReservaInvalidaError(
            f"Las reservas se reciben entre las {HORA_APERTURA:%H:%M} y las {ULTIMA_RESERVA:%H:%M}."
        )
