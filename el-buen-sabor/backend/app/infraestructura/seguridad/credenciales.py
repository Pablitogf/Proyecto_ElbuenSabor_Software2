"""Hash de PIN (PBKDF2) y tokens de sesión firmados con HMAC (RNF-04).

El token es `datos.firma`: si alguien modifica los datos, la firma deja de
coincidir. No guarda sesiones en memoria, así que sobrevive a reinicios.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time

from app.dominio.usuario import Usuario

ITERACIONES = 120_000
DURACION_SESION_SEGUNDOS = 12 * 60 * 60  # Un turno.


def generar_hash_pin(pin: str) -> str:
    sal = secrets.token_hex(16)
    derivado = hashlib.pbkdf2_hmac("sha256", pin.encode(), sal.encode(), ITERACIONES).hex()
    return f"pbkdf2_sha256${ITERACIONES}${sal}${derivado}"


class ServicioDeCredencialesHMAC:
    def __init__(self, clave_secreta: str) -> None:
        self._clave = clave_secreta.encode()

    def verificar_pin(self, pin: str, hash_pin: str) -> bool:
        _, iteraciones, sal, esperado = hash_pin.split("$")
        derivado = hashlib.pbkdf2_hmac("sha256", pin.encode(), sal.encode(), int(iteraciones)).hex()
        return hmac.compare_digest(derivado, esperado)

    def emitir_token(self, usuario: Usuario) -> str:
        datos = {"uid": usuario.id, "exp": int(time.time()) + DURACION_SESION_SEGUNDOS}
        cuerpo = base64.urlsafe_b64encode(json.dumps(datos).encode()).decode().rstrip("=")
        return f"{cuerpo}.{self._firmar(cuerpo)}"

    def leer_token(self, token: str) -> int | None:
        try:
            cuerpo, firma = token.split(".")
            if not hmac.compare_digest(firma, self._firmar(cuerpo)):
                return None
            datos = json.loads(base64.urlsafe_b64decode(cuerpo + "=" * (-len(cuerpo) % 4)))
        except (ValueError, json.JSONDecodeError):
            return None
        return datos["uid"] if datos.get("exp", 0) > time.time() else None

    def _firmar(self, cuerpo: str) -> str:
        return hmac.new(self._clave, cuerpo.encode(), hashlib.sha256).hexdigest()
