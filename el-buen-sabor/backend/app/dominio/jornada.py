"""Jornada de caja y cierre diario (F-02 · RF-10, RF-11, M-02, E-08, CU-06 9a)."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from app.dominio.excepciones import (
    CierreBloqueadoError,
    DatoInvalidoError,
    InconsistenciasSinConfirmarError,
    JornadaCerradaError,
)
from app.dominio.factura import Factura
from app.dominio.pago import MetodoPago, Pago


class EstadoJornada(str, Enum):
    ABIERTA = "ABIERTA"
    CERRADA = "CERRADA"


@dataclass(frozen=True)
class ReporteCierre:
    """RF-10: transacciones, ganancia total y ganancia por medio de pago."""

    transacciones: int
    total_ventas: int
    ventas_por_metodo: dict[str, int]
    impuesto_total: int
    facturas_emitidas: int
    pedidos_cancelados: int
    base_caja: int
    efectivo_esperado: int
    efectivo_contado: int
    inconsistencias: list[str]
    bloqueos: list[str]
    observacion: str | None = None
    comprobante_dian: str | None = None

    @property
    def diferencia_efectivo(self) -> int:
        return self.efectivo_contado - self.efectivo_esperado

    @property
    def se_puede_cerrar(self) -> bool:
        return not self.bloqueos


@dataclass
class Jornada:
    fecha_apertura: datetime
    base_caja: int
    abierta_por: int
    estado: EstadoJornada = EstadoJornada.ABIERTA
    fecha_cierre: datetime | None = None
    cerrada_por: int | None = None
    reporte: ReporteCierre | None = None
    id: int | None = None

    @classmethod
    def abrir(cls, base_caja: int, ahora: datetime, usuario_id: int) -> "Jornada":
        if base_caja < 0:
            raise DatoInvalidoError("La base de caja no puede ser negativa.")
        return cls(fecha_apertura=ahora, base_caja=base_caja, abierta_por=usuario_id)

    @property
    def esta_abierta(self) -> bool:
        return self.estado == EstadoJornada.ABIERTA

    def exigir_abierta(self) -> None:
        """M-02: con la caja cerrada no se aceptan pedidos ni cobros."""
        if not self.esta_abierta:
            raise JornadaCerradaError()

    def verificar_que_puede_cerrar(self, reporte: ReporteCierre, confirmar_inconsistencias: bool) -> None:
        self.exigir_abierta()
        if reporte.bloqueos:
            raise CierreBloqueadoError(reporte.bloqueos)
        if reporte.inconsistencias and not (confirmar_inconsistencias and reporte.observacion):
            raise InconsistenciasSinConfirmarError(len(reporte.inconsistencias))

    def cerrar(self, reporte: ReporteCierre, confirmar_inconsistencias: bool,
               ahora: datetime, usuario_id: int) -> None:
        self.verificar_que_puede_cerrar(reporte, confirmar_inconsistencias)
        self.estado = EstadoJornada.CERRADA
        self.fecha_cierre = ahora
        self.cerrada_por = usuario_id
        self.reporte = reporte


@dataclass
class CuadreDeCaja:
    """Servicio de dominio que arma el reporte y detecta bloqueos e inconsistencias."""

    jornada: Jornada
    pagos: list[Pago]
    facturas: list[Factura]
    pedidos_sin_cerrar: int
    pedidos_cancelados: int
    efectivo_contado: int
    observacion: str | None = None

    def generar_reporte(self, comprobante_dian: str | None = None) -> ReporteCierre:
        if self.efectivo_contado < 0:
            raise DatoInvalidoError("El efectivo contado no puede ser negativo.")
        ventas_por_metodo = {metodo.value: sum(p.monto_en(metodo) for p in self.pagos)
                             for metodo in MetodoPago}
        return ReporteCierre(
            transacciones=len(self.pagos),
            total_ventas=sum(pago.total for pago in self.pagos),
            ventas_por_metodo=ventas_por_metodo,
            impuesto_total=sum(factura.impuesto for factura in self.facturas),
            facturas_emitidas=len(self.facturas),
            pedidos_cancelados=self.pedidos_cancelados,
            base_caja=self.jornada.base_caja,
            efectivo_esperado=self.jornada.base_caja + ventas_por_metodo[MetodoPago.EFECTIVO.value],
            efectivo_contado=self.efectivo_contado,
            inconsistencias=self._inconsistencias(ventas_por_metodo),
            bloqueos=self._bloqueos(),
            observacion=(self.observacion or "").strip() or None,
            comprobante_dian=comprobante_dian,
        )

    def _bloqueos(self) -> list[str]:
        """Condiciones que impiden cerrar, sin importar lo que confirme el administrador."""
        bloqueos = []
        if self.pedidos_sin_cerrar:
            bloqueos.append(f"Hay {self.pedidos_sin_cerrar} mesa(s) con pedido sin cobrar.")
        pendientes = [f.numero for f in self.facturas if not f.esta_validada]
        if pendientes:
            # CU-06 9a: toda factura del día debe tener validación DIAN antes de cerrar.
            bloqueos.append(f"Facturas sin validar por la DIAN: {', '.join(pendientes)}.")
        return bloqueos

    def _inconsistencias(self, ventas_por_metodo: dict[str, int]) -> list[str]:
        """RF-11: cosas que el administrador debe revisar y confirmar una por una."""
        inconsistencias = []
        if len(self.pagos) != len(self.facturas):
            inconsistencias.append(
                f"Se registraron {len(self.pagos)} pagos pero {len(self.facturas)} facturas."
            )
        total_pagos = sum(pago.total for pago in self.pagos)
        total_facturas = sum(factura.total for factura in self.facturas)
        if total_pagos != total_facturas:
            inconsistencias.append(
                f"Los pagos suman {_pesos(total_pagos)} y las facturas {_pesos(total_facturas)}."
            )
        esperado = self.jornada.base_caja + ventas_por_metodo[MetodoPago.EFECTIVO.value]
        diferencia = self.efectivo_contado - esperado
        if diferencia:
            tipo = "Sobran" if diferencia > 0 else "Faltan"
            inconsistencias.append(
                f"{tipo} {_pesos(abs(diferencia))} en efectivo: se esperaban {_pesos(esperado)} "
                f"y se contaron {_pesos(self.efectivo_contado)}."
            )
        return inconsistencias


def _pesos(valor: int) -> str:
    return f"${valor:,}".replace(",", ".")
