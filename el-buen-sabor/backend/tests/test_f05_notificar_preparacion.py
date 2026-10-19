"""F-05 · Notificar preparación: cocina avanza el pedido y el mesero recibe el aviso."""

from tests.ayudas import (
    ARROZ, BANDEJA_PAISA, LIMONADA, MESA_LIBRE, PEDIDO_EN_PREPARACION, PEDIDO_LISTO, ingrediente,
    mesa, registrar,
)


def test_cocina_inicia_marca_platos_y_despacha(api):
    pedido = registrar(api, MESA_LIBRE, (BANDEJA_PAISA, 1), (LIMONADA, 1)).json()
    cocina = api.como("carlos")
    url = f"/api/comandas/{pedido['id']}"

    assert cocina.post(f"{url}/iniciar").json()["estado"] == "EN_PREPARACION"
    cocina.put(f"{url}/platos/{BANDEJA_PAISA}", json={"preparado": True})
    incompleto = cocina.post(f"{url}/listo")
    assert incompleto.status_code == 409
    assert "Limonada" in incompleto.json()["detalle"]

    cocina.put(f"{url}/platos/{LIMONADA}", json={"preparado": True})
    with api.http.websocket_connect(f"/ws/eventos?token={api.como('laura').token}") as tablet:
        assert cocina.post(f"{url}/listo").json()["estado"] == "LISTO_PARA_SERVIR"
        tipos = {tablet.receive_json()["tipo"], tablet.receive_json()["tipo"]}
    assert "PedidoListoParaServir" in tipos
    assert pedido["id"] in [p["id"] for p in api.como("laura").get("/api/pedidos/listos").json()]


def test_el_mesero_sirve_y_la_notificacion_desaparece(api):
    mesero = api.como("laura")
    assert mesero.post(f"/api/pedidos/{PEDIDO_LISTO}/entregar").json()["estado"] == "ENTREGADO"
    assert PEDIDO_LISTO not in [p["id"] for p in mesero.get("/api/pedidos/listos").json()]


def test_no_se_entrega_lo_que_cocina_no_ha_terminado(api):
    respuesta = api.como("laura").post(f"/api/pedidos/{PEDIDO_EN_PREPARACION}/entregar")
    assert respuesta.status_code == 409


def test_cancelar_devuelve_ingredientes_y_libera_la_mesa(api):
    arroz_antes = ingrediente(api, ARROZ)["stock"]
    pedido = registrar(api, MESA_LIBRE, (BANDEJA_PAISA, 2)).json()
    assert ingrediente(api, ARROZ)["stock"] == arroz_antes - 300

    cancelado = api.como("laura").post(f"/api/pedidos/{pedido['id']}/cancelar",
                                       json={"motivo": "Error de digitación"})
    assert cancelado.json()["estado"] == "CANCELADO"
    assert ingrediente(api, ARROZ)["stock"] == arroz_antes
    assert mesa(api, MESA_LIBRE)["estado"] == "DISPONIBLE"


def test_no_se_cancela_si_cocina_ya_empezo(api):
    respuesta = api.como("laura").post(f"/api/pedidos/{PEDIDO_EN_PREPARACION}/cancelar", json={})
    assert respuesta.status_code == 409
