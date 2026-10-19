from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.configuracion import Configuracion
from app.main import crear_aplicacion

AHORA = datetime(2026, 10, 19, 13, 0)  # Lunes a la 1 p. m., dentro del horario de atención.
PIN_POR_USUARIO = {"laura": "1111", "carlos": "2222", "diana": "3333", "admin": "0000"}


class RelojFijo:
    def __init__(self, ahora: datetime) -> None:
        self.actual = ahora

    def ahora(self) -> datetime:
        return self.actual

    def avanzar(self, **delta) -> None:
        self.actual += timedelta(**delta)


class ClienteRestaurante:
    """Cliente HTTP con sesión por rol: `api.como("diana").post(...)`."""

    def __init__(self, cliente: TestClient, reloj: RelojFijo) -> None:
        self.http = cliente
        self.reloj = reloj
        self._tokens: dict[str, str] = {}

    def como(self, usuario: str) -> "SesionDePrueba":
        if usuario not in self._tokens:
            respuesta = self.http.post("/api/sesion", json={"nombreUsuario": usuario,
                                                             "pin": PIN_POR_USUARIO[usuario]})
            assert respuesta.status_code == 200, respuesta.text
            self._tokens[usuario] = respuesta.json()["token"]
        return SesionDePrueba(self.http, self._tokens[usuario])


class SesionDePrueba:
    def __init__(self, cliente: TestClient, token: str) -> None:
        self._cliente = cliente
        self.token = token
        self._cabeceras = {"Authorization": f"Bearer {token}"}

    def get(self, url: str, **kw):
        return self._cliente.get(url, headers=self._cabeceras, **kw)

    def post(self, url: str, json=None, **kw):
        return self._cliente.post(url, json=json, headers=self._cabeceras, **kw)

    def put(self, url: str, json=None, **kw):
        return self._cliente.put(url, json=json, headers=self._cabeceras, **kw)


@pytest.fixture
def reloj() -> RelojFijo:
    return RelojFijo(AHORA)


@pytest.fixture
def api(reloj: RelojFijo) -> ClienteRestaurante:
    """Aplicación completa con SQLite en memoria, nueva en cada prueba."""
    configuracion = Configuracion(url_base_datos="sqlite://", origenes_permitidos=[])
    with TestClient(crear_aplicacion(configuracion, reloj)) as cliente:
        yield ClienteRestaurante(cliente, reloj)
