from dataclasses import dataclass
from enum import Enum

from app.dominio.excepciones import MesaNoDisponibleError, ReglaDeNegocioError


class EstadoMesa(str, Enum):
    """`RESERVADA` no se guarda: se calcula con la agenda de reservas (ver agenda_mesas.py)."""

    DISPONIBLE = "DISPONIBLE"
    OCUPADA = "OCUPADA"
    RESERVADA = "RESERVADA"


@dataclass
class Mesa:
    numero: int
    capacidad: int
    estado: EstadoMesa = EstadoMesa.DISPONIBLE

    @property
    def esta_ocupada(self) -> bool:
        return self.estado == EstadoMesa.OCUPADA

    def ocupar(self) -> None:
        """RD-01: solo una mesa libre puede pasar a ocupada."""
        if self.esta_ocupada:
            raise MesaNoDisponibleError(self.numero)
        self.estado = EstadoMesa.OCUPADA

    def liberar(self) -> None:
        """CU-05 paso 9: al registrar el pago la mesa queda libre."""
        if not self.esta_ocupada:
            raise ReglaDeNegocioError(f"La mesa {self.numero} ya estaba libre.")
        self.estado = EstadoMesa.DISPONIBLE

    def admite(self, personas: int) -> bool:
        return personas <= self.capacidad
