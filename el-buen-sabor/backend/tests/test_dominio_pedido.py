"""Patrón State del pedido (RD-03) y reglas de F-01/F-05."""

from datetime import datetime

import pytest

from app.dominio.estados_pedido import EstadoPedido
from app.dominio.excepciones import (
    CantidadInvalidaError,
    MesaNoDisponibleError,
    PedidoVacioError,
    PlatosSinPrepararError,
    TransicionDeEstadoInvalidaError,
)
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.pedido import DetallePedido, Pedido

AHORA = datetime(2026, 10, 19, 13, 0)


def nuevo_pedido() -> Pedido:
    return Pedido.registrar(5, [DetallePedido(7, "Bandeja paisa", 2, 32000),
                                DetallePedido(1, "Limonada", 1, 6000)], AHORA, mesero_id=1, jornada_id=1)


def test_el_total_suma_los_subtotales():
    assert nuevo_pedido().total == 70000


def test_no_se_registra_un_pedido_vacio():
    with pytest.raises(PedidoVacioError):
        Pedido.registrar(5, [], AHORA, 1, 1)


def test_la_cantidad_debe_ser_positiva():
    with pytest.raises(CantidadInvalidaError):
        DetallePedido(1, "Bandeja paisa", 0, 32000)


def test_recorre_el_ciclo_completo_en_orden():
    pedido = nuevo_pedido()
    pedido.iniciar_preparacion()
    pedido.marcar_plato(7, True)
    pedido.marcar_plato(1, True)
    pedido.marcar_listo(AHORA)
    pedido.entregar()
    pedido.registrar_pago()
    pedido.facturar()
    assert pedido.estado == EstadoPedido.FACTURADO


def test_no_se_puede_saltar_de_registrado_a_listo():
    with pytest.raises(TransicionDeEstadoInvalidaError):
        nuevo_pedido().marcar_listo(AHORA)


def test_no_se_cobra_un_pedido_que_no_se_ha_entregado():
    pedido = nuevo_pedido()
    pedido.iniciar_preparacion()
    with pytest.raises(TransicionDeEstadoInvalidaError, match="cobrar"):
        pedido.registrar_pago()


def test_cocina_no_despacha_con_platos_pendientes():
    pedido = nuevo_pedido()
    pedido.iniciar_preparacion()
    pedido.marcar_plato(7, True)
    with pytest.raises(PlatosSinPrepararError, match="Limonada"):
        pedido.marcar_listo(AHORA)


def test_no_se_marcan_platos_antes_de_iniciar():
    with pytest.raises(TransicionDeEstadoInvalidaError):
        nuevo_pedido().marcar_plato(7, True)


def test_solo_se_cancela_antes_de_que_cocina_empiece():
    cancelable = nuevo_pedido()
    cancelable.cancelar("Error de digitación")
    assert cancelable.estado == EstadoPedido.CANCELADO

    en_cocina = nuevo_pedido()
    en_cocina.iniciar_preparacion()
    with pytest.raises(TransicionDeEstadoInvalidaError, match="cancelar"):
        en_cocina.cancelar("Ya no lo quiere")


def test_mesa_ocupada_no_acepta_otro_pedido():
    with pytest.raises(MesaNoDisponibleError):
        Mesa(5, 4, EstadoMesa.OCUPADA).ocupar()
