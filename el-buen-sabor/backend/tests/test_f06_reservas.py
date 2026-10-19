"""F-06 · Gestionar reservas."""

from datetime import timedelta

from tests.ayudas import LOMO_SALTADO, MESA_RESERVADA, mesa, registrar


def nueva_reserva(api, horas: float = 3, personas: int = 3, **extra):
    inicio = api.reloj.ahora() + timedelta(hours=horas)
    return api.como("laura").post("/api/reservas", json={
        "nombreCliente": "Pedro Gil", "telefono": "3001234567", "personas": personas,
        "inicio": inicio.isoformat(), **extra})


def test_asigna_la_mesa_mas_pequena_que_sirve(api):
    # Mesas 1-2 son de 2 personas y la 3 sigue ocupada durante la próxima hora (RD-01).
    assert nueva_reserva(api, horas=1, personas=3).json()["numeroMesa"] == 4
    # Dentro de 3 horas la mesa 3 ya no bloquea: es la primera de 4 puestos.
    assert nueva_reserva(api, horas=3, personas=3).json()["numeroMesa"] == 3


def test_no_cruza_dos_reservas_en_la_misma_mesa(api):
    nueva_reserva(api, horas=3, numeroMesa=5)
    choque = nueva_reserva(api, horas=4, numeroMesa=5)
    assert choque.status_code == 409


def test_sin_mesas_para_un_grupo_grande(api):
    respuesta = nueva_reserva(api, horas=24, personas=12)
    assert respuesta.status_code == 409
    assert "No hay mesas" in respuesta.json()["detalle"]


def test_reserva_fuera_de_horario(api):
    assert nueva_reserva(api, horas=9).status_code == 422  # 22:00


def test_reprogramar_cambia_de_mesa_si_hace_falta(api):
    reserva = nueva_reserva(api, personas=2).json()
    assert reserva["numeroMesa"] in (1, 2)
    movida = api.como("laura").put(f"/api/reservas/{reserva['id']}", json={
        "inicio": reserva["inicio"], "personas": 6})
    assert movida.json()["numeroMesa"] == 7  # La de 6 puestos, no la de 8.


def test_confirmar_llegada_libera_la_mesa_para_tomar_el_pedido(api):
    assert mesa(api, MESA_RESERVADA)["estado"] == "RESERVADA"
    reserva_id = mesa(api, MESA_RESERVADA)["reservaQueAparta"]["id"]

    confirmada = api.como("laura").post(f"/api/reservas/{reserva_id}/llegada")
    assert confirmada.json()["estado"] == "CUMPLIDA"
    assert mesa(api, MESA_RESERVADA)["estado"] == "DISPONIBLE"
    assert registrar(api, MESA_RESERVADA, (LOMO_SALTADO, 1)).status_code == 201


def test_no_asistio_solo_despues_de_la_tolerancia(api):
    reserva_id = mesa(api, MESA_RESERVADA)["reservaQueAparta"]["id"]
    laura = api.como("laura")
    assert laura.post(f"/api/reservas/{reserva_id}/no-asistio").status_code == 409
    api.reloj.avanzar(minutes=40)
    assert laura.post(f"/api/reservas/{reserva_id}/no-asistio").json()["estado"] == "NO_ASISTIO"
    assert mesa(api, MESA_RESERVADA)["estado"] == "DISPONIBLE"


def test_agenda_del_dia(api):
    hoy = api.reloj.ahora().date().isoformat()
    reservas = api.como("laura").get(f"/api/reservas?fecha={hoy}").json()
    assert [r["nombreCliente"] for r in reservas] == ["Familia Ramírez", "Juliana Ospina"]
    assert reservas[0]["puedeConfirmarse"] is True
