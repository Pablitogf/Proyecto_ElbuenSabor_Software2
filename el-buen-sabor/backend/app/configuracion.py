"""Configuración leída de variables de entorno, con valores por defecto para la demo."""

import os
from dataclasses import dataclass, field
from pathlib import Path

CARPETA_BACKEND = Path(__file__).resolve().parent.parent
URL_BASE_DATOS_POR_DEFECTO = f"sqlite:///{CARPETA_BACKEND / 'el_buen_sabor_v2.db'}"
ORIGENES_POR_DEFECTO = "http://localhost:5173,http://127.0.0.1:5173"
CLAVE_SOLO_DESARROLLO = "clave-de-desarrollo-cambiar-en-produccion"


def _entorno(nombre: str, por_defecto: str) -> str:
    return os.getenv(nombre, por_defecto)


@dataclass(frozen=True)
class Configuracion:
    url_base_datos: str = field(default_factory=lambda: _entorno("URL_BASE_DATOS", URL_BASE_DATOS_POR_DEFECTO))
    origenes_permitidos: list[str] = field(
        default_factory=lambda: _entorno("ORIGENES_PERMITIDOS", ORIGENES_POR_DEFECTO).split(","))
    clave_secreta: str = field(default_factory=lambda: _entorno("CLAVE_SECRETA", CLAVE_SOLO_DESARROLLO))
    modo_demostracion: bool = field(
        default_factory=lambda: _entorno("MODO_DEMOSTRACION", "1") == "1")

    # Facturación electrónica (F-03). IVA_19 según el documento de análisis; INC_8 disponible.
    impuesto_factura: str = field(default_factory=lambda: _entorno("IMPUESTO_FACTURA", "IVA_19"))
    razon_social: str = "Restaurante El Buen Sabor S.A.S."
    nit_emisor: str = field(default_factory=lambda: _entorno("NIT_EMISOR", "900123456"))
    resolucion_numero: str = "18760000001"
    resolucion_prefijo: str = "FEBS"
    resolucion_desde: int = 1001
    resolucion_hasta: int = 5000
    clave_tecnica_dian: str = field(
        default_factory=lambda: _entorno("CLAVE_TECNICA_DIAN", "fc8eac422eba16e22ffd8c6f94b3f40a6e38162c"))
    ambiente_dian: str = "2"  # Pruebas.
