from datetime import datetime

from app.aplicacion.casos_de_uso.caja.gestor_cobros import ResultadoCobro
from app.aplicacion.casos_de_uso.caja.gestor_jornada import ResumenDelDia
from app.aplicacion.casos_de_uso.facturacion.gestor_facturacion import FacturaConDetalle
from app.dominio.factura import EstadoFactura, Factura
from app.dominio.jornada import EstadoJornada, Jornada, ReporteCierre
from app.dominio.pago import LineaPago, MetodoPago, Pago, SolicitudLineaPago
from app.presentacion.esquemas.base import Esquema
from app.presentacion.esquemas.inventario import IngredienteRespuesta


class LineaPagoSolicitud(Esquema):
    metodo: MetodoPago
    monto: int
    monto_recibido: int | None = None

    def a_dominio(self) -> SolicitudLineaPago:
        return SolicitudLineaPago(self.metodo, self.monto, self.monto_recibido)


class CobroSolicitud(Esquema):
    pedido_id: int
    pagos: list[LineaPagoSolicitud]


class LineaPagoRespuesta(Esquema):
    metodo: MetodoPago
    monto: int
    monto_recibido: int | None
    autorizacion: str | None
    cambio: int

    @classmethod
    def desde(cls, l: LineaPago) -> "LineaPagoRespuesta":
        return cls(metodo=l.metodo, monto=l.monto, monto_recibido=l.monto_recibido,
                   autorizacion=l.autorizacion, cambio=l.cambio)


class PagoRespuesta(Esquema):
    id: int
    total: int
    cambio: int
    metodo: str
    fecha_hora: datetime
    lineas: list[LineaPagoRespuesta]

    @classmethod
    def desde(cls, p: Pago) -> "PagoRespuesta":
        return cls(id=p.id, total=p.total, cambio=p.cambio, metodo=p.metodo_resumido,
                   fecha_hora=p.fecha_hora, lineas=[LineaPagoRespuesta.desde(l) for l in p.lineas])


class FacturaRespuesta(Esquema):
    id: int
    numero: str
    numero_mesa: int | None = None
    fecha_emision: datetime
    base: int
    impuesto: int
    nombre_impuesto: str
    tarifa_impuesto: float
    total: int
    cufe: str
    estado: EstadoFactura
    intentos_envio: int
    ultimo_error: str | None
    codigo_validacion: str | None
    metodo_pago: str | None = None

    @classmethod
    def desde(cls, f: Factura, numero_mesa: int | None = None,
              pago: Pago | None = None) -> "FacturaRespuesta":
        return cls(id=f.id, numero=f.numero, numero_mesa=numero_mesa, fecha_emision=f.fecha_emision,
                   base=f.base, impuesto=f.impuesto, nombre_impuesto=f.nombre_impuesto,
                   tarifa_impuesto=f.tarifa_impuesto, total=f.total, cufe=f.cufe, estado=f.estado,
                   intentos_envio=f.intentos_envio, ultimo_error=f.ultimo_error,
                   codigo_validacion=f.codigo_validacion,
                   metodo_pago=pago.metodo_resumido if pago else None)

    @classmethod
    def con_detalle(cls, d: FacturaConDetalle) -> "FacturaRespuesta":
        return cls.desde(d.factura, d.pedido.numero_mesa, d.pago)


class CobroRespuesta(Esquema):
    pago: PagoRespuesta
    factura: FacturaRespuesta

    @classmethod
    def desde(cls, r: ResultadoCobro, numero_mesa: int) -> "CobroRespuesta":
        return cls(pago=PagoRespuesta.desde(r.pago),
                   factura=FacturaRespuesta.desde(r.factura, numero_mesa, r.pago))


# ── Jornada y cierre ───────────────────────────────────────────────────────────
class ReporteCierreRespuesta(Esquema):
    transacciones: int
    total_ventas: int
    ventas_por_metodo: dict[str, int]
    impuesto_total: int
    facturas_emitidas: int
    pedidos_cancelados: int
    base_caja: int
    efectivo_esperado: int
    efectivo_contado: int
    diferencia_efectivo: int
    inconsistencias: list[str]
    bloqueos: list[str]
    se_puede_cerrar: bool
    observacion: str | None
    comprobante_dian: str | None

    @classmethod
    def desde(cls, r: ReporteCierre) -> "ReporteCierreRespuesta":
        return cls(**{campo: getattr(r, campo) for campo in cls.model_fields})


class JornadaRespuesta(Esquema):
    id: int
    estado: EstadoJornada
    fecha_apertura: datetime
    fecha_cierre: datetime | None
    base_caja: int
    reporte: ReporteCierreRespuesta | None

    @classmethod
    def desde(cls, j: Jornada) -> "JornadaRespuesta":
        return cls(id=j.id, estado=j.estado, fecha_apertura=j.fecha_apertura,
                   fecha_cierre=j.fecha_cierre, base_caja=j.base_caja,
                   reporte=ReporteCierreRespuesta.desde(j.reporte) if j.reporte else None)


class ResumenDelDiaRespuesta(Esquema):
    jornada: JornadaRespuesta
    ventas_totales: int
    pedidos_procesados: int
    ticket_promedio: int
    facturas_validadas: int
    facturas_emitidas: int
    mesas_en_servicio: int
    alertas_inventario: list[IngredienteRespuesta]

    @classmethod
    def desde(cls, r: ResumenDelDia) -> "ResumenDelDiaRespuesta":
        return cls(
            jornada=JornadaRespuesta.desde(r.jornada), ventas_totales=r.ventas_totales,
            pedidos_procesados=r.pedidos_procesados, ticket_promedio=r.ticket_promedio,
            facturas_validadas=r.facturas_validadas, facturas_emitidas=r.facturas_emitidas,
            mesas_en_servicio=r.mesas_en_servicio,
            alertas_inventario=[IngredienteRespuesta.desde(i) for i in r.alertas_inventario],
        )


class CierreSolicitud(Esquema):
    efectivo_contado: int
    observacion: str | None = None
    confirmar_inconsistencias: bool = False


class AperturaSolicitud(Esquema):
    base_caja: int
