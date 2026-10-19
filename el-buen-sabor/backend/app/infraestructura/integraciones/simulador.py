from dataclasses import dataclass


@dataclass
class EstadoDelSimulador:
    """Interruptores para demostrar los cursos alternos sin depender de la DIAN ni
    del banco reales: caída del web service (CU-06 9a) y tarjeta rechazada (CU-02 5a)."""

    dian_disponible: bool = True
    rechazar_proxima_tarjeta: bool = False
