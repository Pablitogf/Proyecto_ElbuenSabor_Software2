"""Adaptador del web service de la DIAN (IS-02).

En producción enviaría el XML firmado por SOAP sobre TLS 1.3. Aquí simula a la
DIAN: recalcula el CUFE con la clave técnica y rechaza el documento si no
coincide, igual que la validación real. Con el simulador se puede "apagar".
"""

import hashlib

from app.aplicacion.puertos import RespuestaDIAN
from app.dominio.factura import Factura, ResolucionDIAN, calcular_cufe
from app.dominio.jornada import Jornada
from app.dominio.pedido import Pedido
from app.infraestructura.integraciones.dian.constructor_xml_factura import ConstructorXMLFactura
from app.infraestructura.integraciones.simulador import EstadoDelSimulador

MENSAJE_SIN_SERVICIO = "El web service de la DIAN no responde (tiempo de espera agotado)"


class ServicioDIANSimulado:
    def __init__(self, simulador: EstadoDelSimulador, resolucion: ResolucionDIAN,
                 razon_social: str) -> None:
        self._simulador = simulador
        self._resolucion = resolucion
        self._razon_social = razon_social

    def enviar_factura(self, factura: Factura, pedido: Pedido) -> RespuestaDIAN:
        xml = (ConstructorXMLFactura()
               .con_encabezado(factura, self._resolucion.ambiente)
               .con_emisor(self._resolucion.nit_emisor, self._razon_social)
               .con_consumidor_final()
               .con_impuesto(factura)
               .con_totales(factura)
               .con_lineas(pedido)
               .construir())
        if not self._simulador.dian_disponible:
            return RespuestaDIAN(aceptada=False, mensaje=MENSAJE_SIN_SERVICIO, xml_enviado=xml)
        if not self._cufe_es_valido(factura):
            return RespuestaDIAN(aceptada=False, mensaje="CUFE inválido", xml_enviado=xml)
        return RespuestaDIAN(aceptada=True, codigo=_acuse(factura.cufe), xml_enviado=xml)

    def enviar_reporte_diario(self, jornada: Jornada, total_ventas: int, facturas: int) -> RespuestaDIAN:
        if not self._simulador.dian_disponible:
            return RespuestaDIAN(aceptada=False, mensaje=MENSAJE_SIN_SERVICIO)
        return RespuestaDIAN(aceptada=True, codigo=_acuse(f"{jornada.id}-{total_ventas}-{facturas}"))

    def _cufe_es_valido(self, factura: Factura) -> bool:
        esperado = calcular_cufe(factura.numero, factura.fecha_emision, factura.base,
                                 factura.codigo_impuesto, factura.impuesto, factura.total,
                                 self._resolucion)
        return esperado == factura.cufe


def _acuse(semilla: str) -> str:
    return "DIAN-" + hashlib.sha256(semilla.encode()).hexdigest()[:12].upper()
