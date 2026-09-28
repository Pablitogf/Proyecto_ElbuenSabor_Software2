"""Pruebas unitarias de las reglas de negocio, sin base de datos ni HTTP."""

import pytest

from app.dominio.excepciones import (
    CantidadInvalidaError,
    MesaNoDisponibleError,
    PedidoVacioError,
    StockInsuficienteError,
)
from app.dominio.inventario import Ingrediente, Inventario
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.pedido import DetallePedido, EstadoPedido, Pedido
from app.dominio.producto import Categoria, IngredienteDeReceta, ProductoMenu

ARROZ_ID, CARNE_ID = 1, 2


def crear_inventario(arroz: float = 1000, carne: float = 600) -> Inventario:
    return Inventario([
        Ingrediente(ARROZ_ID, "Arroz", "g", arroz, 100),
        Ingrediente(CARNE_ID, "Carne", "g", carne, 100),
    ])


def crear_lomo_saltado() -> ProductoMenu:
    return ProductoMenu(
        id=1, nombre="Lomo saltado", descripcion="", precio=30000,
        categoria=Categoria.PLATOS_PRINCIPALES, icono="🥩",
        receta=[IngredienteDeReceta(ARROZ_ID, 150), IngredienteDeReceta(CARNE_ID, 200)],
    )


class TestMesa:
    def test_una_mesa_disponible_pasa_a_ocupada(self):
        mesa = Mesa(numero=5, capacidad=4)

        mesa.ocupar()

        assert mesa.estado == EstadoMesa.OCUPADA

    def test_una_mesa_ocupada_no_acepta_otro_pedido(self):
        mesa = Mesa(numero=5, capacidad=4, estado=EstadoMesa.OCUPADA)

        with pytest.raises(MesaNoDisponibleError):
            mesa.ocupar()


class TestInventario:
    def test_calcula_porciones_segun_el_ingrediente_que_mas_limita(self):
        inventario = crear_inventario(arroz=1000, carne=600)

        assert inventario.porciones_disponibles(crear_lomo_saltado()) == 3

    def test_sin_stock_de_un_ingrediente_no_hay_porciones(self):
        inventario = crear_inventario(carne=0)

        assert inventario.porciones_disponibles(crear_lomo_saltado()) == 0

    def test_consumir_descuenta_los_ingredientes_de_la_receta(self):
        inventario = crear_inventario(arroz=1000, carne=600)

        inventario.consumir([(crear_lomo_saltado(), 2)])

        stock = {ingrediente.id: ingrediente.stock for ingrediente in inventario.ingredientes()}
        assert stock == {ARROZ_ID: 700, CARNE_ID: 200}

    def test_si_no_alcanza_no_descuenta_nada(self):
        inventario = crear_inventario(arroz=1000, carne=300)

        with pytest.raises(StockInsuficienteError):
            inventario.consumir([(crear_lomo_saltado(), 2)])

        stock = {ingrediente.id: ingrediente.stock for ingrediente in inventario.ingredientes()}
        assert stock == {ARROZ_ID: 1000, CARNE_ID: 300}


class TestPedido:
    def test_calcula_el_total_sumando_los_subtotales(self):
        pedido = Pedido.registrar(5, [
            DetallePedido(1, "Bandeja paisa", 2, 32000),
            DetallePedido(2, "Limonada", 1, 6000),
        ])

        assert pedido.total == 70000
        assert pedido.estado == EstadoPedido.REGISTRADO

    def test_no_se_puede_registrar_un_pedido_sin_platos(self):
        with pytest.raises(PedidoVacioError):
            Pedido.registrar(5, [])

    def test_la_cantidad_de_un_plato_debe_ser_positiva(self):
        with pytest.raises(CantidadInvalidaError):
            DetallePedido(1, "Bandeja paisa", 0, 32000)
