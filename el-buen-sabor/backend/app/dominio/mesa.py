from dataclasses import dataclass
from enum import Enum

from app.dominio.excepciones import MesaNoDisponibleError


class EstadoMesa(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    OCUPADA = "OCUPADA"
    RESERVADA = "RESERVADA"


@dataclass
class Mesa:
    numero: int
    capacidad: int
    estado: EstadoMesa = EstadoMesa.DISPONIBLE

    @property
    def esta_disponible(self) -> bool:
        return self.estado == EstadoMesa.DISPONIBLE

    def ocupar(self) -> None:
        """RD-01: solo una mesa disponible puede pasar a ocupada."""
        if not self.esta_disponible:
            raise MesaNoDisponibleError(self.numero)
        self.estado = EstadoMesa.OCUPADA
