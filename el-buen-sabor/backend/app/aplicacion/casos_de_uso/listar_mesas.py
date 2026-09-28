from app.aplicacion.puertos import UnidadDeTrabajo
from app.dominio.mesa import Mesa


class ListarMesas:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo) -> None:
        self._uow = unidad_de_trabajo

    def ejecutar(self) -> list[Mesa]:
        with self._uow:
            return self._uow.mesas.listar()
