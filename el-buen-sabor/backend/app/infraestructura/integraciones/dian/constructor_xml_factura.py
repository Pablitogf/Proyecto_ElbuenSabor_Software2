"""Patrón Builder para el XML de la factura (SWR-07: formato DIAN).

Arma una versión simplificada del estándar UBL 2.1 que exige la DIAN: emisor,
adquirente, totales, impuesto, líneas y CUFE. Cada sección se agrega con un
método encadenable y `construir()` devuelve el documento final.
"""

import xml.etree.ElementTree as ET

from app.dominio.factura import NIT_CONSUMIDOR_FINAL, Factura
from app.dominio.pedido import Pedido

NS_FACTURA = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"


def _cbc(padre: ET.Element, etiqueta: str, texto: str, **atributos: str) -> ET.Element:
    elemento = ET.SubElement(padre, f"{{{NS_CBC}}}{etiqueta}", atributos)
    elemento.text = texto
    return elemento


def _cac(padre: ET.Element, etiqueta: str) -> ET.Element:
    return ET.SubElement(padre, f"{{{NS_CAC}}}{etiqueta}")


def _valor(monto: int) -> str:
    return f"{monto:.2f}"


class ConstructorXMLFactura:
    def __init__(self) -> None:
        ET.register_namespace("", NS_FACTURA)
        ET.register_namespace("cbc", NS_CBC)
        ET.register_namespace("cac", NS_CAC)
        self._raiz = ET.Element(f"{{{NS_FACTURA}}}Invoice")
        _cbc(self._raiz, "UBLVersionID", "UBL 2.1")
        _cbc(self._raiz, "CustomizationID", "10")  # Factura de venta nacional.

    def con_encabezado(self, factura: Factura, ambiente: str) -> "ConstructorXMLFactura":
        _cbc(self._raiz, "ProfileExecutionID", ambiente)
        _cbc(self._raiz, "ID", factura.numero)
        _cbc(self._raiz, "UUID", factura.cufe, schemeName="CUFE-SHA384")
        _cbc(self._raiz, "IssueDate", factura.fecha_emision.strftime("%Y-%m-%d"))
        _cbc(self._raiz, "IssueTime", factura.fecha_emision.strftime("%H:%M:%S-05:00"))
        _cbc(self._raiz, "InvoiceTypeCode", "01")
        _cbc(self._raiz, "DocumentCurrencyCode", "COP")
        return self

    def con_emisor(self, nit: str, razon_social: str) -> "ConstructorXMLFactura":
        parte = _cac(_cac(self._raiz, "AccountingSupplierParty"), "Party")
        _cbc(_cac(parte, "PartyName"), "Name", razon_social)
        _cbc(_cac(parte, "PartyTaxScheme"), "CompanyID", nit, schemeName="31")
        return self

    def con_consumidor_final(self) -> "ConstructorXMLFactura":
        parte = _cac(_cac(self._raiz, "AccountingCustomerParty"), "Party")
        _cbc(_cac(parte, "PartyName"), "Name", "Consumidor final")
        _cbc(_cac(parte, "PartyTaxScheme"), "CompanyID", NIT_CONSUMIDOR_FINAL, schemeName="13")
        return self

    def con_impuesto(self, factura: Factura) -> "ConstructorXMLFactura":
        total = _cac(self._raiz, "TaxTotal")
        _cbc(total, "TaxAmount", _valor(factura.impuesto), currencyID="COP")
        detalle = _cac(total, "TaxSubtotal")
        _cbc(detalle, "TaxableAmount", _valor(factura.base), currencyID="COP")
        _cbc(detalle, "TaxAmount", _valor(factura.impuesto), currencyID="COP")
        categoria = _cac(detalle, "TaxCategory")
        _cbc(categoria, "Percent", f"{factura.tarifa_impuesto * 100:.2f}")
        esquema = _cac(categoria, "TaxScheme")
        _cbc(esquema, "ID", factura.codigo_impuesto)
        _cbc(esquema, "Name", factura.nombre_impuesto)
        return self

    def con_totales(self, factura: Factura) -> "ConstructorXMLFactura":
        totales = _cac(self._raiz, "LegalMonetaryTotal")
        _cbc(totales, "LineExtensionAmount", _valor(factura.base), currencyID="COP")
        _cbc(totales, "TaxInclusiveAmount", _valor(factura.total), currencyID="COP")
        _cbc(totales, "PayableAmount", _valor(factura.total), currencyID="COP")
        return self

    def con_lineas(self, pedido: Pedido) -> "ConstructorXMLFactura":
        for numero, detalle in enumerate(pedido.detalles, start=1):
            linea = _cac(self._raiz, "InvoiceLine")
            _cbc(linea, "ID", str(numero))
            _cbc(linea, "InvoicedQuantity", str(detalle.cantidad), unitCode="94")
            _cbc(linea, "LineExtensionAmount", _valor(detalle.subtotal), currencyID="COP")
            _cbc(_cac(linea, "Item"), "Description", detalle.nombre_producto)
            _cbc(_cac(linea, "Price"), "PriceAmount", _valor(detalle.precio_unitario), currencyID="COP")
        return self

    def construir(self) -> str:
        ET.indent(self._raiz)
        return ET.tostring(self._raiz, encoding="unicode", xml_declaration=True)
