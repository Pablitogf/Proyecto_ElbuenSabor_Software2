"""F-02 · Procesar cobro y F-03 · Generar factura electrónica."""

from tests.ayudas import (
    MESA_ENTREGADA, PEDIDO_EN_PREPARACION, PEDIDO_ENTREGADO, TOTAL_PEDIDO_ENTREGADO, cobrar, efectivo,
    mesa, tarjeta,
)


def simulador(api, **cambios) -> None:
    estado = {"dianDisponible": True, "rechazarProximaTarjeta": False, **cambios}
    assert api.como("admin").put("/api/demostracion/simulador", json=estado).status_code == 200


def test_cobro_en_efectivo_con_cambio_factura_validada_y_mesa_libre(api):
    respuesta = cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO, recibido=100_000))

    assert respuesta.status_code == 200, respuesta.text
    resultado = respuesta.json()
    assert resultado["pago"]["cambio"] == 20_000
    factura = resultado["factura"]
    assert factura["numero"] == "FEBS1001"
    assert factura["estado"] == "VALIDADA"
    assert factura["base"] + factura["impuesto"] == TOTAL_PEDIDO_ENTREGADO
    assert factura["impuesto"] == 12_773  # IVA 19 % incluido en $80.000.
    assert mesa(api, MESA_ENTREGADA)["estado"] == "DISPONIBLE"

    xml = api.como("diana").get(f"/api/facturas/{factura['id']}/xml").text
    assert factura["cufe"] in xml and "FEBS1001" in xml


def test_pago_dividido_entre_efectivo_y_tarjeta(api):
    respuesta = cobrar(api, PEDIDO_ENTREGADO, efectivo(30_000, 50_000), tarjeta(50_000))
    pago = respuesta.json()["pago"]
    assert pago["metodo"] == "MIXTO"
    assert pago["cambio"] == 20_000
    assert next(l for l in pago["lineas"] if l["metodo"] == "TARJETA")["autorizacion"]


def test_el_pago_debe_cuadrar_con_la_cuenta(api):
    respuesta = cobrar(api, PEDIDO_ENTREGADO, efectivo(50_000))
    assert respuesta.status_code == 422
    assert "suma" in respuesta.json()["detalle"]


def test_solo_se_cobra_un_pedido_entregado(api):
    respuesta = cobrar(api, PEDIDO_EN_PREPARACION, efectivo(50_000))
    assert respuesta.status_code == 409


def test_tarjeta_rechazada_no_registra_nada(api):
    simulador(api, rechazarProximaTarjeta=True)
    rechazo = cobrar(api, PEDIDO_ENTREGADO, tarjeta(TOTAL_PEDIDO_ENTREGADO))
    assert rechazo.status_code == 409
    assert "rechazado" in rechazo.json()["detalle"]
    assert mesa(api, MESA_ENTREGADA)["estado"] == "OCUPADA"
    assert api.como("diana").get("/api/facturas").json() == []
    # CU-02 5a: el cajero cambia de medio de pago y continúa.
    assert cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO)).status_code == 200


def test_dian_caida_deja_la_factura_pendiente_y_se_reenvia(api):
    simulador(api, dianDisponible=False)
    factura = cobrar(api, PEDIDO_ENTREGADO, efectivo(TOTAL_PEDIDO_ENTREGADO)).json()["factura"]
    assert factura["estado"] == "PENDIENTE_DIAN"
    assert "no responde" in factura["ultimoError"]
    assert mesa(api, MESA_ENTREGADA)["estado"] == "DISPONIBLE"  # El cliente ya pagó y se fue.

    simulador(api, dianDisponible=True)
    reenviada = api.como("diana").post(f"/api/facturas/{factura['id']}/reenviar").json()
    assert reenviada["estado"] == "VALIDADA"
    assert reenviada["intentosEnvio"] == 2


def test_el_mesero_no_ve_registros_de_caja(api):
    assert api.como("laura").get("/api/facturas").status_code == 403
