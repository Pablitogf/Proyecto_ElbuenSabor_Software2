import pytest
from fastapi.testclient import TestClient

from app.configuracion import Configuracion
from app.main import crear_aplicacion


@pytest.fixture
def cliente() -> TestClient:
    """Aplicación completa con una base SQLite en memoria, nueva en cada prueba."""
    configuracion = Configuracion(url_base_datos="sqlite://", origenes_permitidos=[])
    with TestClient(crear_aplicacion(configuracion)) as cliente_de_prueba:
        yield cliente_de_prueba
