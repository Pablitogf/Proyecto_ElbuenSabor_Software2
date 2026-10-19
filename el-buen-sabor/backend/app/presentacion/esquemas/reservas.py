from datetime import datetime

from app.aplicacion.casos_de_uso.reservas.gestor_reservas import DatosReserva, ReservaEnAgenda
from app.dominio.reserva import EstadoReserva, Reserva
from app.presentacion.esquemas.base import Esquema


class ReservaSolicitud(Esquema):
    nombre_cliente: str
    telefono: str
    personas: int
    inicio: datetime
    numero_mesa: int | None = None
    notas: str = ""

    def a_datos(self) -> DatosReserva:
        return DatosReserva(self.nombre_cliente, self.telefono, self.personas,
                            self.inicio.replace(tzinfo=None, second=0, microsecond=0),
                            self.numero_mesa, self.notas)


class ReprogramacionSolicitud(Esquema):
    inicio: datetime
    personas: int
    numero_mesa: int | None = None


class ReservaRespuesta(Esquema):
    id: int
    nombre_cliente: str
    telefono: str
    personas: int
    inicio: datetime
    fin: datetime
    numero_mesa: int
    estado: EstadoReserva
    notas: str | None
    vencida: bool = False
    puede_confirmarse: bool = False

    @classmethod
    def desde(cls, r: Reserva, vencida: bool = False, puede_confirmarse: bool = False) -> "ReservaRespuesta":
        return cls(id=r.id, nombre_cliente=r.nombre_cliente, telefono=r.telefono, personas=r.personas,
                   inicio=r.inicio, fin=r.fin, numero_mesa=r.numero_mesa, estado=r.estado,
                   notas=r.notas, vencida=vencida, puede_confirmarse=puede_confirmarse)

    @classmethod
    def en_agenda(cls, a: ReservaEnAgenda) -> "ReservaRespuesta":
        return cls.desde(a.reserva, a.vencida, a.puede_confirmarse)
