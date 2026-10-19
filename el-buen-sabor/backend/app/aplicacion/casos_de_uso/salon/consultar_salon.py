from dataclasses import dataclass

from app.aplicacion.puertos import Reloj, UnidadDeTrabajo
from app.dominio.agenda_mesas import AgendaDeMesas, VistaMesa
from app.dominio.inventario import Inventario
from app.dominio.pedido import Pedido
from app.dominio.producto import ProductoMenu


@dataclass(frozen=True)
class PlatoDelMenu:
    producto: ProductoMenu
    porciones_disponibles: int

    @property
    def disponible(self) -> bool:
        return self.producto.activo and self.porciones_disponibles > 0


@dataclass(frozen=True)
class MesaDelSalon:
    vista: VistaMesa
    pedido: Pedido | None


class ConsultarSalon:
    """IU-01: lo que el mesero ve en la tablet (RF-15 estado de mesas, RF-03 menú)."""

    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, reloj: Reloj) -> None:
        self._uow = unidad_de_trabajo
        self._reloj = reloj

    def mesas(self) -> list[MesaDelSalon]:
        with self._uow:
            mesas = self._uow.mesas.listar()
            agenda = AgendaDeMesas(mesas, self._uow.reservas.listar_pendientes(), self._reloj.ahora())
            return [
                MesaDelSalon(agenda.vista(mesa), self._uow.pedidos.en_servicio_de_mesa(mesa.numero))
                for mesa in mesas
            ]

    def menu(self) -> list[PlatoDelMenu]:
        with self._uow:
            inventario = Inventario(self._uow.ingredientes.listar())
            return [
                PlatoDelMenu(producto, inventario.porciones_disponibles(producto))
                for producto in self._uow.productos.listar()
            ]
