from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class Esquema(BaseModel):
    """Contratos JSON en camelCase (convención web), código Python en snake_case."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ErrorRespuesta(Esquema):
    detalle: str
    tipo: str
    motivos: list[str] | None = None
