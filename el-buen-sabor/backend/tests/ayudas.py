"""Datos de la semilla que usan las pruebas (ver datos_iniciales.py)."""

BANDEJA_PAISA, LOMO_SALTADO, MOJARRA_FRITA, TORTA_TRES_LECHES, LIMONADA = 7, 8, 10, 14, 1
MESA_LIBRE, MESA_LIBRE_2 = 5, 4
MESA_CON_PEDIDO_LISTO, MESA_EN_PREPARACION, MESA_ENTREGADA, MESA_RESERVADA = 2, 3, 6, 7
PEDIDO_LISTO, PEDIDO_EN_PREPARACION, PEDIDO_ENTREGADO = 1, 2, 3
TOTAL_PEDIDO_ENTREGADO = 80_000
BASE_DE_CAJA = 200_000
ARROZ = 1


def mesa(api, numero: int) -> dict:
    return next(m for m in api.como("laura").get("/api/mesas").json() if m["numero"] == numero)


def plato(api, producto_id: int) -> dict:
    return next(p for p in api.como("laura").get("/api/menu").json() if p["id"] == producto_id)


def ingrediente(api, ingrediente_id: int) -> dict:
    lista = api.como("admin").get("/api/inventario/ingredientes").json()
    return next(i for i in lista if i["id"] == ingrediente_id)


def registrar(api, numero_mesa: int, *items: tuple[int, int]):
    return api.como("laura").post("/api/pedidos", json={
        "numeroMesa": numero_mesa,
        "items": [{"productoId": p, "cantidad": c} for p, c in items],
    })


def efectivo(monto: int, recibido: int | None = None) -> dict:
    return {"metodo": "EFECTIVO", "monto": monto, "montoRecibido": recibido if recibido else monto}


def tarjeta(monto: int) -> dict:
    return {"metodo": "TARJETA", "monto": monto}


def cobrar(api, pedido_id: int, *pagos: dict):
    return api.como("diana").post("/api/caja/cobros", json={"pedidoId": pedido_id, "pagos": list(pagos)})


def llevar_hasta_entregado(api, pedido_id: int) -> None:
    cocina, mesero = api.como("carlos"), api.como("laura")
    pedido = next(p for p in cocina.get("/api/comandas").json() if p["id"] == pedido_id)
    if pedido["estado"] == "REGISTRADO":
        assert cocina.post(f"/api/comandas/{pedido_id}/iniciar").status_code == 200
    if pedido["estado"] in ("REGISTRADO", "EN_PREPARACION"):
        for detalle in pedido["detalles"]:
            cocina.put(f"/api/comandas/{pedido_id}/platos/{detalle['productoId']}", json={"preparado": True})
        assert cocina.post(f"/api/comandas/{pedido_id}/listo").status_code == 200
    assert mesero.post(f"/api/pedidos/{pedido_id}/entregar").status_code == 200
