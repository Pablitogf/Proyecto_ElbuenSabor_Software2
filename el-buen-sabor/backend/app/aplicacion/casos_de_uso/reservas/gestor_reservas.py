"""Gestión de reservas (F-06, CU-05, RF-16)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from app.aplicacion.puertos import PublicadorEventos, Reloj, UnidadDeTrabajo
from app.dominio.agenda_mesas import AgendaDeMesas, EstrategiaAsignacionMesa
from app.dominio.eventos import MesasActualizadas, ReservasActualizadas
from app.dominio.excepciones import ErrorDeDominio, ReservaNoEncontradaError
from app.dominio.mesa import Mesa
from app.dominio.reserva import Reserva
from app.dominio.usuario import Usuario


@dataclass(frozen=True)
class DatosReserva:
    nombre_cliente: str
    telefono: str
    personas: int
    inicio: datetime
    numero_mesa: int | None = None  # Vacío: el sistema elige la mejor mesa.
    notas: str = ""


@dataclass(frozen=True)
class ReservaEnAgenda:
    reserva: Reserva
    vencida: bool
    puede_confirmarse: bool


class GestorReservas:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos, reloj: Reloj,
                 estrategia: EstrategiaAsignacionMesa) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj
        self._estrategia = estrategia

    def del_dia(self, dia: date) -> list[ReservaEnAgenda]:
        ahora = self._reloj.ahora()
        inicio_dia = datetime.combine(dia, time.min)
        with self._uow:
            reservas = self._uow.reservas.listar_entre(inicio_dia, inicio_dia + timedelta(days=1))
        return [
            ReservaEnAgenda(r, r.esta_vencida(ahora), r.aparta_la_mesa(ahora))
            for r in sorted(reservas, key=lambda r: (r.inicio, r.numero_mesa))
        ]

    async def crear(self, datos: DatosReserva, usuario: Usuario) -> Reserva:
        """CU-05 pasos 5-6: valida políticas, evita choques y asigna mesa (Strategy)."""
        ahora = self._reloj.ahora()
        with self._uow:
            agenda = self._agenda(ahora)
            mesa = self._elegir_mesa(agenda, datos.numero_mesa, datos.personas, datos.inicio)
            reserva = self._uow.reservas.agregar(Reserva.crear(
                datos.nombre_cliente, datos.telefono, datos.personas, datos.inicio,
                mesa.numero, usuario.id, ahora, datos.notas,
            ))
            self._uow.confirmar()
        await self._avisar(reserva.numero_mesa)
        return reserva

    async def modificar(self, reserva_id: int, inicio: datetime, personas: int,
                        numero_mesa: int | None) -> Reserva:
        """Si la mesa actual sigue sirviendo se conserva; si no, se reasigna."""
        ahora = self._reloj.ahora()
        with self._uow:
            reserva = self._reserva(reserva_id)
            mesa_anterior = reserva.numero_mesa
            agenda = self._agenda(ahora)
            mesa = self._elegir_mesa(agenda, numero_mesa, personas, inicio, reserva.id,
                                     preferida=mesa_anterior)
            reserva.reprogramar(inicio, personas, mesa.numero, ahora)
            self._uow.reservas.guardar(reserva)
            self._uow.confirmar()
        await self._avisar(mesa_anterior, reserva.numero_mesa)
        return reserva

    async def confirmar_llegada(self, reserva_id: int) -> Reserva:
        return await self._cambiar(reserva_id, lambda r: r.confirmar_llegada(self._reloj.ahora()))

    async def cancelar(self, reserva_id: int) -> Reserva:
        return await self._cambiar(reserva_id, lambda r: r.cancelar())

    async def marcar_no_asistio(self, reserva_id: int) -> Reserva:
        return await self._cambiar(reserva_id, lambda r: r.marcar_no_asistio(self._reloj.ahora()))

    # ── Internos ───────────────────────────────────────────────────────────────
    def _elegir_mesa(self, agenda: AgendaDeMesas, numero_mesa: int | None, personas: int,
                     inicio: datetime, excluir_id: int | None = None,
                     preferida: int | None = None) -> Mesa:
        if numero_mesa is not None:
            return agenda.validar_mesa_elegida(numero_mesa, personas, inicio, excluir_id)
        if preferida is not None:
            try:
                return agenda.validar_mesa_elegida(preferida, personas, inicio, excluir_id)
            except ErrorDeDominio:  # La mesa anterior ya no sirve: se busca otra.
                pass
        return agenda.asignar(personas, inicio, excluir_id)

    def _agenda(self, ahora: datetime) -> AgendaDeMesas:
        return AgendaDeMesas(self._uow.mesas.listar(), self._uow.reservas.listar_pendientes(),
                             ahora, self._estrategia)

    async def _cambiar(self, reserva_id: int, accion: Callable[[Reserva], None]) -> Reserva:
        with self._uow:
            reserva = self._reserva(reserva_id)
            accion(reserva)
            self._uow.reservas.guardar(reserva)
            self._uow.confirmar()
        await self._avisar(reserva.numero_mesa)
        return reserva

    async def _avisar(self, *mesas: int) -> None:
        await self._eventos.publicar(ReservasActualizadas(), MesasActualizadas(tuple(set(mesas))))

    def _reserva(self, reserva_id: int) -> Reserva:
        reserva = self._uow.reservas.obtener(reserva_id)
        if reserva is None:
            raise ReservaNoEncontradaError(reserva_id)
        return reserva
