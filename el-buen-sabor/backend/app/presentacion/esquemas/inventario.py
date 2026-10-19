from datetime import datetime

from app.aplicacion.casos_de_uso.inventario.gestor_inventario import MovimientoConNombre
from app.dominio.inventario import Ingrediente, MotivoMerma, TipoMovimiento
from app.dominio.reabastecimiento import SugerenciaCompra
from app.presentacion.esquemas.base import Esquema


class IngredienteRespuesta(Esquema):
    id: int
    nombre: str
    unidad: str
    stock: float
    stock_minimo: float
    bajo_minimo: bool

    @classmethod
    def desde(cls, i: Ingrediente) -> "IngredienteRespuesta":
        return cls(id=i.id, nombre=i.nombre, unidad=i.unidad, stock=i.stock,
                   stock_minimo=i.stock_minimo, bajo_minimo=i.esta_bajo_minimo)


class NuevoIngredienteSolicitud(Esquema):
    nombre: str
    unidad: str
    stock_minimo: float


class EntradaSolicitud(Esquema):
    cantidad: float
    proveedor: str


class MermaSolicitud(Esquema):
    cantidad: float
    motivo: MotivoMerma
    detalle: str = ""


class MinimoSolicitud(Esquema):
    stock_minimo: float


class MovimientoRespuesta(Esquema):
    id: int
    ingrediente: str
    unidad: str
    tipo: TipoMovimiento
    cantidad: float
    fecha_hora: datetime
    proveedor: str | None
    motivo: MotivoMerma | None
    detalle: str | None
    pedido_id: int | None

    @classmethod
    def desde(cls, m: MovimientoConNombre) -> "MovimientoRespuesta":
        mv = m.movimiento
        return cls(id=mv.id, ingrediente=m.ingrediente, unidad=m.unidad, tipo=mv.tipo,
                   cantidad=mv.cantidad, fecha_hora=mv.fecha_hora, proveedor=mv.proveedor,
                   motivo=mv.motivo, detalle=mv.detalle, pedido_id=mv.pedido_id)


class SugerenciaRespuesta(Esquema):
    ingrediente: IngredienteRespuesta
    consumo_diario: float
    dias_restantes: float | None
    cantidad_sugerida: float

    @classmethod
    def desde(cls, s: SugerenciaCompra) -> "SugerenciaRespuesta":
        return cls(ingrediente=IngredienteRespuesta.desde(s.ingrediente), consumo_diario=s.consumo_diario,
                   dias_restantes=s.dias_restantes, cantidad_sugerida=s.cantidad_sugerida)
