"""Prueba de integración del vertical slice F-01 (Pasos 1 a 5), de la API a la base de datos."""

BANDEJA_PAISA, LOMO_SALTADO, MOJARRA_FRITA, TORTA_TRES_LECHES = 7, 8, 10, 14
MESA_LIBRE, MESA_OCUPADA = 5, 3


def estado_de_mesa(cliente, numero: int) -> str:
    mesas = cliente.get("/api/mesas").json()
    return next(mesa["estado"] for mesa in mesas if mesa["numero"] == numero)


def plato(cliente, producto_id: int) -> dict:
    return next(p for p in cliente.get("/api/menu").json() if p["id"] == producto_id)


def test_flujo_completo_mesa_menu_pedido_cocina(cliente):
    # Paso 1: la mesa 5 está disponible.
    assert estado_de_mesa(cliente, MESA_LIBRE) == "DISPONIBLE"

    # Paso 2: el menú marca como no disponibles los platos sin ingredientes.
    assert plato(cliente, MOJARRA_FRITA)["disponible"] is False
    assert plato(cliente, BANDEJA_PAISA)["disponible"] is True
    porciones_antes = plato(cliente, BANDEJA_PAISA)["porciones_disponibles"]

    with cliente.websocket_connect("/ws/eventos") as pantalla_cocina:
        # Pasos 3 y 4: se confirma el pedido con dos platos.
        respuesta = cliente.post("/api/pedidos", json={
            "numero_mesa": MESA_LIBRE,
            "items": [
                {"producto_id": BANDEJA_PAISA, "cantidad": 2},
                {"producto_id": LOMO_SALTADO, "cantidad": 1},
            ],
        })
        evento = pantalla_cocina.receive_json()

    assert respuesta.status_code == 201
    pedido = respuesta.json()
    assert pedido["total"] == 2 * 32000 + 30000
    assert pedido["estado"] == "REGISTRADO"

    # Paso 5: la mesa pasa a ocupada y la comanda llega a la cocina.
    assert estado_de_mesa(cliente, MESA_LIBRE) == "OCUPADA"
    assert evento["tipo"] == "PEDIDO_REGISTRADO"
    assert evento["datos"]["comanda"]["id"] == pedido["id"]
    assert evento["datos"]["mesa"]["estado"] == "OCUPADA"
    comandas = cliente.get("/api/comandas").json()
    assert pedido["id"] in [comanda["id"] for comanda in comandas]

    # RF-05: el inventario se descontó.
    assert plato(cliente, BANDEJA_PAISA)["porciones_disponibles"] < porciones_antes


def test_no_se_puede_pedir_en_una_mesa_ocupada(cliente):
    respuesta = cliente.post("/api/pedidos", json={
        "numero_mesa": MESA_OCUPADA,
        "items": [{"producto_id": LOMO_SALTADO, "cantidad": 1}],
    })

    assert respuesta.status_code == 409
    assert "no está disponible" in respuesta.json()["detalle"]


def test_sin_stock_se_rechaza_y_la_mesa_sigue_libre(cliente):
    respuesta = cliente.post("/api/pedidos", json={
        "numero_mesa": MESA_LIBRE,
        "items": [{"producto_id": TORTA_TRES_LECHES, "cantidad": 3}],
    })

    assert respuesta.status_code == 409
    assert estado_de_mesa(cliente, MESA_LIBRE) == "DISPONIBLE"
    assert plato(cliente, TORTA_TRES_LECHES)["porciones_disponibles"] == 2


def test_un_pedido_vacio_se_rechaza(cliente):
    respuesta = cliente.post("/api/pedidos", json={"numero_mesa": MESA_LIBRE, "items": []})

    assert respuesta.status_code == 409


def test_una_mesa_inexistente_responde_404(cliente):
    respuesta = cliente.post("/api/pedidos", json={
        "numero_mesa": 99,
        "items": [{"producto_id": LOMO_SALTADO, "cantidad": 1}],
    })

    assert respuesta.status_code == 404
