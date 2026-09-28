import os
from dataclasses import dataclass, field
from pathlib import Path

CARPETA_BACKEND = Path(__file__).resolve().parent.parent
URL_BASE_DATOS_POR_DEFECTO = f"sqlite:///{CARPETA_BACKEND / 'el_buen_sabor.db'}"
ORIGENES_POR_DEFECTO = "http://localhost:5173,http://127.0.0.1:5173"


def _leer_origenes_permitidos() -> list[str]:
    return os.getenv("ORIGENES_PERMITIDOS", ORIGENES_POR_DEFECTO).split(",")


@dataclass(frozen=True)
class Configuracion:
    url_base_datos: str = field(
        default_factory=lambda: os.getenv("URL_BASE_DATOS", URL_BASE_DATOS_POR_DEFECTO)
    )
    origenes_permitidos: list[str] = field(default_factory=_leer_origenes_permitidos)
