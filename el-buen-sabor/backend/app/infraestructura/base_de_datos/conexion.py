from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

FabricaDeSesiones = sessionmaker


class ModeloBase(DeclarativeBase):
    """Base común de todos los modelos ORM."""


def crear_motor(url_base_datos: str) -> Engine:
    es_sqlite_en_memoria = url_base_datos in ("sqlite://", "sqlite:///:memory:")
    opciones: dict = {"connect_args": {"check_same_thread": False}}
    if es_sqlite_en_memoria:
        opciones["poolclass"] = StaticPool  # Una sola conexión compartida (pruebas).
    return create_engine(url_base_datos, **opciones)


def crear_fabrica_de_sesiones(motor: Engine) -> FabricaDeSesiones:
    return sessionmaker(bind=motor, expire_on_commit=False)
