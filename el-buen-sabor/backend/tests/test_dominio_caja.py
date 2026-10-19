"""Reglas de cobro (F-02), factura electrónica (F-03) y cierre (RF-10, RF-11)."""

from datetime import datetime

import pytest

from app.dominio.excepciones import (
    CierreBloqueadoError,
    InconsistenciasSinConfirmarError,
    JornadaCerradaError,
    PagoInvalidoError,
    ResolucionAgotadaError,
)
from app.dominio.factura import EstadoFactura, Factura, ResolucionDIAN, calcular_cufe
from app.dominio.impuestos import IMPUESTO_CONSUMO_8, IVA_19
from app.dominio.jornada import CuadreDeCaja, Jornada
from app.dominio.pago import LineaPago, MetodoPago, Pago, SolicitudLineaPago, validar_desglose
from app.dominio.pedido import DetallePedido, Pedido

AHORA = datetime(2026, 10, 19, 13, 0)
RESOLUCION = ResolucionDIAN("1876", "FEBS", 1001, 1002, "clave", "900123456", "2")


def pedido_de(total: int, pedido_id: int = 1) -> Pedido:
    pedido = Pedido.registrar(5, [DetallePedido(1, "Plato", 1, total)], AHORA, 1, 1)
    pedido.id = pedido_id
    return pedido


class TestDesgloseDelPago:
    def test_el_pago_debe_sumar_exactamente_la_cuenta(self):
        with pytest.raises(PagoInvalidoError, match="suma"):
            validar_desglose([SolicitudLineaPago(MetodoPago.EFECTIVO, 50000, 50000)], 70000)

    def test_permite_dividir_entre_efectivo_y_tarjeta(self):
        validar_desglose([SolicitudLineaPago(MetodoPago.EFECTIVO, 20000, 50000),
                          SolicitudLineaPago(MetodoPago.TARJETA, 50000)], 70000)

    def test_no_repite_medio_de_pago(self):
        with pytest.raises(PagoInvalidoError, match="una sola vez"):
            validar_desglose([SolicitudLineaPago(MetodoPago.TARJETA, 35000),
                              SolicitudLineaPago(MetodoPago.TARJETA, 35000)], 70000)

    def test_el_cambio_sale_del_efectivo_recibido(self):
        pago = Pago(1, 1, [LineaPago(MetodoPago.EFECTIVO, 70000, monto_recibido=100000)], AHORA, 3)
        assert pago.cambio == 30000


class TestImpuestos:
    def test_iva_se_desglosa_del_precio_al_publico(self):
        desglose = IVA_19.desglosar(119000)
        assert (desglose.base, desglose.impuesto) == (100000, 19000)

    def test_impuesto_al_consumo_del_8(self):
        desglose = IMPUESTO_CONSUMO_8.desglosar(108000)
        assert (desglose.base, desglose.impuesto) == (100000, 8000)

    def test_base_mas_impuesto_siempre_da_el_total(self):
        for total in (6000, 33333, 94000, 1):
            assert IVA_19.desglosar(total).total == total


class TestFactura:
    def test_toma_el_consecutivo_y_calcula_el_cufe(self):
        factura = Factura.emitir(pedido_de(119000), 1001, RESOLUCION, IVA_19, AHORA)
        assert factura.numero == "FEBS1001"
        assert factura.estado == EstadoFactura.PENDIENTE_DIAN
        assert len(factura.cufe) == 96  # SHA-384 en hexadecimal.
        assert factura.cufe == calcular_cufe("FEBS1001", AHORA, 100000, "01", 19000, 119000, RESOLUCION)

    def test_no_se_sale_del_rango_autorizado(self):
        with pytest.raises(ResolucionAgotadaError):
            Factura.emitir(pedido_de(10000), 1003, RESOLUCION, IVA_19, AHORA)


class TestCierreDeCaja:
    def jornada(self) -> Jornada:
        jornada = Jornada.abrir(200000, AHORA, 4)
        jornada.id = 1
        return jornada

    def cuadre(self, efectivo_contado: int, facturas_validadas: bool = True,
               pedidos_sin_cerrar: int = 0, observacion: str | None = None) -> CuadreDeCaja:
        factura = Factura.emitir(pedido_de(70000), 1001, RESOLUCION, IVA_19, AHORA)
        if facturas_validadas:
            factura.registrar_validacion("OK", AHORA)
        pago = Pago(1, 1, [LineaPago(MetodoPago.EFECTIVO, 70000, 100000)], AHORA, 3)
        return CuadreDeCaja(self.jornada(), [pago], [factura], pedidos_sin_cerrar, 0,
                            efectivo_contado, observacion)

    def test_reporte_con_ventas_por_medio_de_pago(self):
        reporte = self.cuadre(efectivo_contado=270000).generar_reporte()
        assert reporte.total_ventas == 70000
        assert reporte.ventas_por_metodo == {"EFECTIVO": 70000, "TARJETA": 0}
        assert reporte.efectivo_esperado == 270000
        assert reporte.inconsistencias == []

    def test_mesas_sin_cobrar_bloquean_el_cierre(self):
        jornada = self.jornada()
        reporte = self.cuadre(270000, pedidos_sin_cerrar=2).generar_reporte()
        with pytest.raises(CierreBloqueadoError, match="sin cobrar"):
            jornada.cerrar(reporte, True, AHORA, 4)

    def test_facturas_sin_cufe_validado_bloquean_el_cierre(self):
        reporte = self.cuadre(270000, facturas_validadas=False).generar_reporte()
        with pytest.raises(CierreBloqueadoError, match="DIAN"):
            self.jornada().cerrar(reporte, True, AHORA, 4)

    def test_un_faltante_de_efectivo_exige_confirmacion_y_observacion(self):
        jornada = self.jornada()
        sin_observacion = self.cuadre(260000).generar_reporte()
        assert "Faltan $10.000" in sin_observacion.inconsistencias[0]
        with pytest.raises(InconsistenciasSinConfirmarError):
            jornada.cerrar(sin_observacion, True, AHORA, 4)

        con_observacion = self.cuadre(260000, observacion="Billete falso retenido").generar_reporte()
        jornada.cerrar(con_observacion, True, AHORA, 4)
        assert not jornada.esta_abierta

    def test_con_la_caja_cerrada_no_se_opera(self):
        jornada = self.jornada()
        jornada.cerrar(self.cuadre(270000).generar_reporte(), False, AHORA, 4)
        with pytest.raises(JornadaCerradaError):
            jornada.exigir_abierta()
