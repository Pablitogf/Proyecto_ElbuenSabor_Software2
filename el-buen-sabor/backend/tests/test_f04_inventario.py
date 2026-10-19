"""F-04 · Gestionar inventario."""

from tests.ayudas import ARROZ, ingrediente


def test_entrada_suma_stock_y_queda_en_el_kardex(api):
    admin = api.como("admin")
    antes = ingrediente(api, ARROZ)["stock"]
    respuesta = admin.post(f"/api/inventario/ingredientes/{ARROZ}/entradas",
                           json={"cantidad": 2000, "proveedor": "Molino Roa"})
    assert respuesta.json()["stock"] == antes + 2000
    ultimo = admin.get("/api/inventario/movimientos").json()[0]
    assert (ultimo["tipo"], ultimo["proveedor"]) == ("ENTRADA", "Molino Roa")


def test_entrada_invalida(api):
    respuesta = api.como("admin").post(f"/api/inventario/ingredientes/{ARROZ}/entradas",
                                       json={"cantidad": 0, "proveedor": "Molino Roa"})
    assert respuesta.status_code == 422


def test_merma_que_cruza_el_minimo_genera_alerta(api):
    admin = api.como("admin")
    stock = ingrediente(api, ARROZ)["stock"]
    with api.http.websocket_connect(f"/ws/eventos?token={admin.token}") as panel:
        admin.post(f"/api/inventario/ingredientes/{ARROZ}/mermas",
                   json={"cantidad": stock - 500, "motivo": "DANO", "detalle": "Se mojó el bulto"})
        tipos = {panel.receive_json()["tipo"], panel.receive_json()["tipo"]}
    assert "StockBajoMinimo" in tipos
    alertas = admin.get("/api/jornada/resumen").json()["alertasInventario"]
    assert "Arroz" in [a["nombre"] for a in alertas]


def test_subir_el_minimo_por_encima_del_stock_alerta(api):
    admin = api.como("admin")
    stock = ingrediente(api, ARROZ)["stock"]
    respuesta = admin.put(f"/api/inventario/ingredientes/{ARROZ}/minimo", json={"stockMinimo": stock + 1})
    assert respuesta.json()["bajoMinimo"] is True


def test_no_se_duplican_ingredientes(api):
    admin = api.como("admin")
    nuevo = {"nombre": "Cilantro", "unidad": "g", "stockMinimo": 100}
    assert admin.post("/api/inventario/ingredientes", json=nuevo).status_code == 201
    assert admin.post("/api/inventario/ingredientes", json={**nuevo, "nombre": "cilantro"}).status_code == 409


def test_sugerencia_de_compra_prioriza_lo_que_se_acaba_primero(api):
    sugerencias = api.como("admin").get("/api/inventario/sugerencias").json()
    assert sugerencias, "Con el historial de demostración siempre hay algo que comprar"
    nombres = [s["ingrediente"]["nombre"] for s in sugerencias]
    assert "Mojarra" in nombres  # Stock en cero.


def test_el_mesero_no_administra_inventario(api):
    assert api.como("laura").get("/api/inventario/ingredientes").status_code == 403
