"""Agenda de mesas: combina el estado físico de cada mesa con sus reservas (F-06).

Incluye el patrón Strategy para elegir mesa al reservar.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.dominio.excepciones import (
    ConflictoDeReservaError,
    MesaNoDisponibleError,
    ReservaInvalidaError,
    SinMesasParaReservaError,
)
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.reserva import DURACION_RESERVA, Reserva


class EstrategiaAsignacionMesa(Protocol):
    def elegir(self, candidatas: list[Mesa], personas: int) -> Mesa: ...


class MejorAjuste:
    """La mesa más pequeña donde caben: no se gasta una mesa de 8 en una pareja."""

    def elegir(self, candidatas: list[Mesa], personas: int) -> Mesa:
        return min(candidatas, key=lambda mesa: (mesa.capacidad, mesa.numero))


@dataclass(frozen=True)
class VistaMesa:
    mesa: Mesa
    estado: EstadoMesa
    reserva_que_aparta: Reserva | None
    proxima_reserva: Reserva | None


class AgendaDeMesas:
    def __init__(self, mesas: list[Mesa], reservas: list[Reserva], ahora: datetime,
                 estrategia: EstrategiaAsignacionMesa | None = None) -> None:
        self._mesas = {mesa.numero: mesa for mesa in mesas}
        self._reservas = [reserva for reserva in reservas if reserva.esta_pendiente]
        self._ahora = ahora
        self._estrategia = estrategia or MejorAjuste()

    # ── Estado que ve el mesero ────────────────────────────────────────────────
    def vista(self, mesa: Mesa) -> VistaMesa:
        aparta = self.reserva_que_aparta(mesa.numero)
        if mesa.esta_ocupada:
            estado = EstadoMesa.OCUPADA
        elif aparta:
            estado = EstadoMesa.RESERVADA
        else:
            estado = EstadoMesa.DISPONIBLE
        return VistaMesa(mesa, estado, aparta, self._proxima_reserva(mesa.numero))

    def reserva_que_aparta(self, numero_mesa: int) -> Reserva | None:
        return next((r for r in self._reservas_de(numero_mesa) if r.aparta_la_mesa(self._ahora)), None)

    # ── Asignación de mesa al reservar ─────────────────────────────────────────
    def asignar(self, personas: int, inicio: datetime, excluir_reserva_id: int | None = None) -> Mesa:
        """CU-05 paso 6 (y 6a si no hay mesa)."""
        candidatas = [
            mesa for mesa in self._mesas.values()
            if mesa.admite(personas) and self._libre(mesa, inicio, excluir_reserva_id)
        ]
        if not candidatas:
            raise SinMesasParaReservaError(personas, f"{inicio:%H:%M} del {inicio:%d/%m}")
        return self._estrategia.elegir(candidatas, personas)

    def validar_mesa_elegida(self, numero_mesa: int, personas: int, inicio: datetime,
                             excluir_reserva_id: int | None = None) -> Mesa:
        mesa = self._mesas.get(numero_mesa)
        if mesa is None:
            raise ReservaInvalidaError(f"La mesa {numero_mesa} no existe.")
        if not mesa.admite(personas):
            raise ReservaInvalidaError(
                f"La mesa {numero_mesa} es para {mesa.capacidad} personas; la reserva es de {personas}."
            )
        if self._ocupada_cuando_empieza(mesa, inicio):
            raise MesaNoDisponibleError(numero_mesa)
        if self._choca_con_reserva(numero_mesa, inicio, excluir_reserva_id):
            raise ConflictoDeReservaError(numero_mesa, f"{inicio:%H:%M}")
        return mesa

    # ── Internos ───────────────────────────────────────────────────────────────
    def _libre(self, mesa: Mesa, inicio: datetime, excluir_reserva_id: int | None) -> bool:
        return (not self._ocupada_cuando_empieza(mesa, inicio)
                and not self._choca_con_reserva(mesa.numero, inicio, excluir_reserva_id))

    def _ocupada_cuando_empieza(self, mesa: Mesa, inicio: datetime) -> bool:
        """RD-01: una mesa ocupada no se puede reservar para las próximas 2 horas."""
        return mesa.esta_ocupada and inicio < self._ahora + DURACION_RESERVA

    def _choca_con_reserva(self, numero_mesa: int, inicio: datetime, excluir_id: int | None) -> bool:
        return any(r.se_cruza_con(inicio) for r in self._reservas_de(numero_mesa) if r.id != excluir_id)

    def _reservas_de(self, numero_mesa: int) -> list[Reserva]:
        return [r for r in self._reservas if r.numero_mesa == numero_mesa]

    def _proxima_reserva(self, numero_mesa: int) -> Reserva | None:
        hoy = [r for r in self._reservas_de(numero_mesa)
               if r.inicio.date() == self._ahora.date() and not r.esta_vencida(self._ahora)]
        return min(hoy, key=lambda r: r.inicio, default=None)
