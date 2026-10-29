"""Factura electrónica (F-03, RF-07, RD-05, Contrato 3)."""

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.dominio.excepciones import FacturaYaValidadaError, ResolucionAgotadaError
from app.dominio.impuestos import CalculadoraImpuesto
from app.dominio.pedido import Pedido

NIT_CONSUMIDOR_FINAL = "222222222222"
HUSO_HORARIO_COLOMBIA = "-05:00"


@dataclass(frozen=True)
class ResolucionDIAN:
    """Rango de numeración que la DIAN autoriza al restaurante."""

    numero: str
    prefijo: str
    desde: int
    hasta: int
    clave_tecnica: str
    nit_emisor: str
    ambiente: str  # "1" producción, "2" pruebas.

    def numero_para(self, consecutivo: int) -> str:
        if not self.desde <= consecutivo <= self.hasta:
            raise ResolucionAgotadaError(self.hasta)
        return f"{self.prefijo}{consecutivo}"

    def siguiente_consecutivo(self, ultimo_emitido: int) -> int:
        """La numeración arranca en `desde` aunque aún no se haya emitido ninguna."""
        return max(ultimo_emitido + 1, self.desde)


class EstadoFactura(str, Enum):
    PENDIENTE_DIAN = "PENDIENTE_DIAN"  # Emitida; la DIAN aún no la valida (contingencia).
    VALIDADA = "VALIDADA"


@dataclass
class Factura:
    numero: str
    consecutivo: int
    pedido_id: int
    jornada_id: int
    fecha_emision: datetime
    base: int
    impuesto: int
    total: int
    nombre_impuesto: str
    codigo_impuesto: str
    tarifa_impuesto: float
    cufe: str
    estado: EstadoFactura = EstadoFactura.PENDIENTE_DIAN
    intentos_envio: int = 0
    ultimo_error: str | None = None
    codigo_validacion: str | None = None
    fecha_validacion: datetime | None = None
    xml: str | None = None
    id: int | None = None

    @classmethod
    def emitir(cls, pedido: Pedido, consecutivo: int, resolucion: ResolucionDIAN,
               impuesto: CalculadoraImpuesto, ahora: datetime) -> "Factura":
        """Contrato 3: subtotal, impuesto y total salen del consolidado del pedido."""
        numero = resolucion.numero_para(consecutivo)
        desglose = impuesto.desglosar(pedido.total)
        cufe = calcular_cufe(numero, ahora, desglose.base, impuesto.codigo_dian,
                             desglose.impuesto, desglose.total, resolucion)
        return cls(
            numero=numero, consecutivo=consecutivo, pedido_id=pedido.id, jornada_id=pedido.jornada_id,
            fecha_emision=ahora, base=desglose.base, impuesto=desglose.impuesto, total=desglose.total,
            nombre_impuesto=impuesto.nombre, codigo_impuesto=impuesto.codigo_dian,
            tarifa_impuesto=impuesto.tarifa, cufe=cufe,
        )

    @property
    def esta_validada(self) -> bool:
        return self.estado == EstadoFactura.VALIDADA

    def registrar_validacion(self, codigo: str, ahora: datetime) -> None:
        if self.esta_validada:
            raise FacturaYaValidadaError(self.numero)
        self.intentos_envio += 1
        self.estado = EstadoFactura.VALIDADA
        self.codigo_validacion = codigo
        self.fecha_validacion = ahora
        self.ultimo_error = None

    def registrar_fallo_envio(self, motivo: str) -> None:
        if self.esta_validada:
            raise FacturaYaValidadaError(self.numero)
        self.intentos_envio += 1
        self.ultimo_error = motivo


def calcular_cufe(numero: str, fecha: datetime, base: int, codigo_impuesto: str, impuesto: int,
                  total: int, resolucion: ResolucionDIAN) -> str:
    """CUFE: SHA-384 de los campos que fija el anexo técnico de la DIAN.

    Lo calcula el EMISOR; la DIAN solo lo valida. Los tres tributos (01 IVA, 04 INC,
    03 ICA) siempre van en la cadena, con 0.00 los que no aplican.
    """
    valores_impuesto = {"01": 0, "04": 0, "03": 0}
    valores_impuesto[codigo_impuesto] = impuesto
    cadena = "".join(
        [
            numero,
            fecha.strftime("%Y-%m-%d"),
            fecha.strftime("%H:%M:%S") + HUSO_HORARIO_COLOMBIA,
            _decimal(base),
            *(codigo + _decimal(valor) for codigo, valor in valores_impuesto.items()),
            _decimal(total),
            resolucion.nit_emisor,
            NIT_CONSUMIDOR_FINAL,
            resolucion.clave_tecnica,
            resolucion.ambiente,
        ]
    )
    return hashlib.sha384(cadena.encode("utf-8")).hexdigest()


def _decimal(valor: int) -> str:
    return f"{valor:.2f}"


class EmisorDeFacturas:
    """Fábrica de dominio (patrón Factory): con la resolución DIAN y la estrategia de
    impuesto configuradas, arma la factura de un pedido.

    Es pura: no lee ni guarda nada. Quien la usa le entrega el último consecutivo
    emitido y decide cuándo persistir la factura dentro de su propia transacción.
    """

    def __init__(self, resolucion: ResolucionDIAN, impuesto: CalculadoraImpuesto) -> None:
        self._resolucion = resolucion
        self._impuesto = impuesto

    def emitir(self, pedido: Pedido, ultimo_consecutivo: int, ahora: datetime) -> Factura:
        consecutivo = self._resolucion.siguiente_consecutivo(ultimo_consecutivo)
        return Factura.emitir(pedido, consecutivo, self._resolucion, self._impuesto, ahora)
