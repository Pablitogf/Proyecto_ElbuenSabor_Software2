"""Pruebas de caracterización del cobro (taller de refactorización, hallazgo H-02).

Se escribieron ANTES de refactorizar para fijar el comportamiento observable de
F-02/F-03 que la refactorización no puede cambiar: numeración consecutiva de
facturas, que un cobro fallido no consume número, y la respuesta del endpoint.
"""

from tests.ayudas import (
    MESA_ENTREGADA, PEDIDO_ENTREGADO, PEDIDO_LISTO, TOTAL_PEDIDO_ENTREGADO, cobrar, efectivo,
    llevar_hasta_entregado, mesa, tarjeta,
)


def test_cobros_sucesivos_toman_consecutivos_seguidos(api):
    primera = cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO)).json()["factura"]
    llevar_hasta_entregado(api, PEDIDO_LISTO)
    total = next(c["total"] for c in api.como("diana").get("/api/caja/cuentas").json()
                 if c["id"] == PEDIDO_LISTO)
    segunda = cobrar(api, PEDIDO_LISTO, efectivo(total)).json()["factura"]

    assert (primera["numero"], segunda["numero"]) == ("FEBS1001", "FEBS1002")


def test_un_cobro_rechazado_no_consume_numero_de_factura(api):
    api.como("admin").put("/api/demostracion/simulador",
                          json={"dianDisponible": True, "rechazarProximaTarjeta": True})
    assert cobrar(api, PEDIDO_ENTREGADO, tarjeta(TOTAL_PEDIDO_ENTREGADO)).status_code == 409

    factura = cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO)).json()["factura"]
    assert factura["numero"] == "FEBS1001"


def test_respuesta_completa_del_cobro(api):
    respuesta = cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO, recibido=100_000))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["pago"]["total"] == TOTAL_PEDIDO_ENTREGADO
    assert cuerpo["pago"]["cambio"] == 20_000
    assert cuerpo["pago"]["metodo"] == "EFECTIVO"
    assert cuerpo["factura"]["numeroMesa"] == MESA_ENTREGADA
    assert cuerpo["factura"]["total"] == TOTAL_PEDIDO_ENTREGADO
    assert cuerpo["factura"]["estado"] == "VALIDADA"
    assert cuerpo["factura"]["metodoPago"] == "EFECTIVO"
    assert mesa(api, MESA_ENTREGADA)["pedido"] is None  # El pedido salió de servicio (Facturado).


def test_con_la_dian_caida_el_pedido_queda_pagado_y_bloquea_el_cierre(api):
    api.como("admin").put("/api/demostracion/simulador",
                          json={"dianDisponible": False, "rechazarProximaTarjeta": False})
    factura = cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO)).json()["factura"]

    previa = api.como("admin").post("/api/jornada/previsualizar-cierre",
                                    json={"efectivoContado": 0}).json()
    assert any(factura["numero"] in bloqueo for bloqueo in previa["bloqueos"])
