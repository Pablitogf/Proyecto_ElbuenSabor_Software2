"""Adaptador de la pasarela bancaria (IS-01).

En producción esta clase haría una petición REST/TLS 1.3 al banco. Para el
prototipo responde localmente con las mismas reglas que un datáfono: aprueba,
o rechaza por fondos insuficientes o por superar el cupo.
"""

import secrets

from app.aplicacion.puertos import RespuestaPasarela
from app.infraestructura.integraciones.simulador import EstadoDelSimulador

CUPO_MAXIMO_POR_TRANSACCION = 3_000_000


class PasarelaBancariaSimulada:
    def __init__(self, simulador: EstadoDelSimulador) -> None:
        self._simulador = simulador

    def autorizar(self, monto: int, referencia: str) -> RespuestaPasarela:
        if self._simulador.rechazar_proxima_tarjeta:
            self._simulador.rechazar_proxima_tarjeta = False  # Solo la siguiente.
            return RespuestaPasarela(aprobada=False, motivo_rechazo="fondos insuficientes")
        if monto > CUPO_MAXIMO_POR_TRANSACCION:
            return RespuestaPasarela(aprobada=False, motivo_rechazo="supera el cupo por transacción")
        return RespuestaPasarela(aprobada=True, codigo_autorizacion=f"{secrets.randbelow(10**6):06d}")
