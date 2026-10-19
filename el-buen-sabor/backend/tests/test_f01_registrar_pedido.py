"""F-01 · Registrar pedido (vertical slice de la primera entrega, ahora con RBAC y reservas)."""

from tests.ayudas import (
    BANDEJA_PAISA, LOMO_SALTADO, MESA_EN_PREPARACION, MESA_LIBRE, MESA_RESERVADA, MOJARRA_FRITA,
    TORTA_TRES_LECHES, mesa, plato, registrar,
)


def test_flujo_completo_mesa_menu_pedido_cocina(api):
    assert mesa(api, MESA_LIBRE)["estado"] == "DISPONIBLE"
    assert plato(api, MOJARRA_FRITA)["disponible"] is False
    porciones_antes = plato(api, BANDEJA_PAISA)["porcionesDisponibles"]

    token_cocina = api.como("carlos").token
    with api.http.websocket_connect(f"/ws/eventos?token={token_cocina}") as pantalla_cocina:
        respuesta = registrar(api, MESA_LIBRE, (BANDEJA_PAISA, 2), (LOMO_SALTADO, 1))
        evento = pantalla_cocina.receive_json()

    assert respuesta.status_code == 201, respuesta.text
    pedido = respuesta.json()
    assert pedido["total"] == 2 * 32000 + 30000
    assert evento == {"tipo": "PedidoRegistrado", "datos": {"pedido_id": pedido["id"], "numero_mesa": 5}}
    assert mesa(api, MESA_LIBRE)["estado"] == "OCUPADA"
    assert pedido["id"] in [c["id"] for c in api.como("carlos").get("/api/comandas").json()]
    assert plato(api, BANDEJA_PAISA)["porcionesDisponibles"] < porciones_antes


def test_mesa_ocupada_rechaza_otro_pedido(api):
    assert registrar(api, MESA_EN_PREPARACION, (LOMO_SALTADO, 1)).status_code == 409


def test_mesa_apartada_por_reserva_exige_confirmar_llegada(api):
    respuesta = registrar(api, MESA_RESERVADA, (LOMO_SALTADO, 1))
    assert respuesta.status_code == 409
    assert "Familia Ramírez" in respuesta.json()["detalle"]


def test_sin_stock_se_rechaza_y_no_se_toca_nada(api):
    respuesta = registrar(api, MESA_LIBRE, (TORTA_TRES_LECHES, 3))
    assert respuesta.status_code == 409
    assert mesa(api, MESA_LIBRE)["estado"] == "DISPONIBLE"
    assert plato(api, TORTA_TRES_LECHES)["porcionesDisponibles"] == 2


def test_exige_sesion_y_permiso(api):
    sin_sesion = api.http.post("/api/pedidos", json={"numeroMesa": 5, "items": []})
    assert sin_sesion.status_code == 401
    cocinero = api.como("carlos").post("/api/pedidos", json={
        "numeroMesa": 5, "items": [{"productoId": LOMO_SALTADO, "cantidad": 1}]})
    assert cocinero.status_code == 403


def test_pin_incorrecto(api):
    respuesta = api.http.post("/api/sesion", json={"nombreUsuario": "laura", "pin": "9999"})
    assert respuesta.status_code == 401
