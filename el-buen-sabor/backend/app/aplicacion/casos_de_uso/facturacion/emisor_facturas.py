from datetime import datetime

from app.aplicacion.puertos import UnidadDeTrabajo
from app.dominio.factura import Factura, ResolucionDIAN
from app.dominio.impuestos import CalculadoraImpuesto
from app.dominio.pedido import Pedido


class EmisorDeFacturas:
    """Fábrica de facturas: conoce la resolución DIAN y la estrategia de impuesto
    configuradas, y asigna el siguiente consecutivo de la numeración autorizada."""

    def __init__(self, resolucion: ResolucionDIAN, impuesto: CalculadoraImpuesto) -> None:
        self._resolucion = resolucion
        self._impuesto = impuesto

    def emitir(self, unidad_de_trabajo: UnidadDeTrabajo, pedido: Pedido, ahora: datetime) -> Factura:
        consecutivo = max(unidad_de_trabajo.facturas.ultimo_consecutivo() + 1, self._resolucion.desde)
        factura = Factura.emitir(pedido, consecutivo, self._resolucion, self._impuesto, ahora)
        return unidad_de_trabajo.facturas.agregar(factura)
