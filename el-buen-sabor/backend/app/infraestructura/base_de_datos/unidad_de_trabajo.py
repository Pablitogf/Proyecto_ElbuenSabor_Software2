from typing import Self

from sqlalchemy.orm import Session, sessionmaker

from app.infraestructura.base_de_datos import repositorios as r


class UnidadDeTrabajoSQL:
    """Patrón Unit of Work. Abre una sesión por operación; si algo falla antes de
    `confirmar()`, todos los cambios se descartan (inventario, mesa y pedido intactos)."""

    def __init__(self, fabrica_de_sesiones: sessionmaker) -> None:
        self._fabrica_de_sesiones = fabrica_de_sesiones
        self._sesion: Session | None = None

    def __enter__(self) -> Self:
        self._sesion = self._fabrica_de_sesiones()
        self.mesas = r.RepositorioMesasSQL(self._sesion)
        self.productos = r.RepositorioProductosSQL(self._sesion)
        self.ingredientes = r.RepositorioIngredientesSQL(self._sesion)
        self.movimientos = r.RepositorioMovimientosSQL(self._sesion)
        self.pedidos = r.RepositorioPedidosSQL(self._sesion)
        self.pagos = r.RepositorioPagosSQL(self._sesion)
        self.facturas = r.RepositorioFacturasSQL(self._sesion)
        self.reservas = r.RepositorioReservasSQL(self._sesion)
        self.jornadas = r.RepositorioJornadasSQL(self._sesion)
        self.usuarios = r.RepositorioUsuariosSQL(self._sesion)
        return self

    def __exit__(self, *args: object) -> None:
        self._sesion.rollback()  # Sin efecto si ya se confirmó.
        self._sesion.close()

    def confirmar(self) -> None:
        self._sesion.commit()
