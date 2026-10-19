"""Cierre de caja (RF-10, RF-11, CU-06 9a) y operación con la caja cerrada (M-02)."""

from tests.ayudas import (
    BASE_DE_CAJA, LOMO_SALTADO, MESA_LIBRE, PEDIDO_EN_PREPARACION, PEDIDO_ENTREGADO, PEDIDO_LISTO,
    TOTAL_PEDIDO_ENTREGADO, cobrar, efectivo, llevar_hasta_entregado, registrar, tarjeta,
)


def cobrar_todas_las_mesas(api) -> int:
    llevar_hasta_entregado(api, PEDIDO_LISTO)
    llevar_hasta_entregado(api, PEDIDO_EN_PREPARACION)
    efectivo_total = 0
    for pedido_id in (PEDIDO_LISTO, PEDIDO_EN_PREPARACION):
        total = next(c["total"] for c in api.como("diana").get("/api/caja/cuentas").json()
                     if c["id"] == pedido_id)
        assert cobrar(api, pedido_id, efectivo(total)).status_code == 200
        efectivo_total += total
    assert cobrar(api, PEDIDO_ENTREGADO, tarjeta(TOTAL_PEDIDO_ENTREGADO)).status_code == 200
    return efectivo_total


def test_mesas_sin_cobrar_bloquean_el_cierre(api):
    admin = api.como("admin")
    previa = admin.post("/api/jornada/previsualizar-cierre", json={"efectivoContado": BASE_DE_CAJA}).json()
    assert previa["sePuedeCerrar"] is False
    assert "sin cobrar" in previa["bloqueos"][0]
    respuesta = admin.post("/api/jornada/cerrar", json={"efectivoContado": BASE_DE_CAJA})
    assert respuesta.status_code == 409
    assert respuesta.json()["motivos"]


def test_cierre_exitoso_con_reporte_y_caja_bloqueada(api):
    efectivo_cobrado = cobrar_todas_las_mesas(api)
    admin = api.como("admin")
    contado = BASE_DE_CAJA + efectivo_cobrado

    jornada = admin.post("/api/jornada/cerrar", json={"efectivoContado": contado}).json()
    reporte = jornada["reporte"]
    assert jornada["estado"] == "CERRADA"
    assert reporte["transacciones"] == 3
    assert reporte["ventasPorMetodo"]["TARJETA"] == TOTAL_PEDIDO_ENTREGADO
    assert reporte["comprobanteDian"].startswith("DIAN-")

    # M-02: con la caja cerrada no hay pedidos nuevos hasta abrir otra jornada.
    assert registrar(api, MESA_LIBRE, (LOMO_SALTADO, 1)).status_code == 409
    assert admin.post("/api/jornada/abrir", json={"baseCaja": 150_000}).json()["estado"] == "ABIERTA"
    assert registrar(api, MESA_LIBRE, (LOMO_SALTADO, 1)).status_code == 201


def test_faltante_de_efectivo_exige_observacion(api):
    efectivo_cobrado = cobrar_todas_las_mesas(api)
    admin = api.como("admin")
    contado = BASE_DE_CAJA + efectivo_cobrado - 5_000

    sin_confirmar = admin.post("/api/jornada/cerrar", json={"efectivoContado": contado})
    assert sin_confirmar.status_code == 409
    confirmado = admin.post("/api/jornada/cerrar", json={
        "efectivoContado": contado, "confirmarInconsistencias": True,
        "observacion": "Se devolvió cambio de más a la mesa 3"})
    assert confirmado.json()["reporte"]["inconsistencias"][0].startswith("Faltan $5.000")


def test_solo_el_administrador_cierra_la_caja(api):
    respuesta = api.como("diana").post("/api/jornada/cerrar", json={"efectivoContado": 0})
    assert respuesta.status_code == 403
