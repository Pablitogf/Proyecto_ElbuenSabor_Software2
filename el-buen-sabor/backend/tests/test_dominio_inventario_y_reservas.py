"""Reglas de inventario (F-04) y reservas (F-06)."""

from datetime import datetime, timedelta

import pytest

from app.dominio.agenda_mesas import AgendaDeMesas
from app.dominio.excepciones import (
    AccionDeReservaInvalidaError,
    CantidadInvalidaError,
    ConflictoDeReservaError,
    DatoInvalidoError,
    ReservaInvalidaError,
    SinMesasParaReservaError,
    StockInsuficienteError,
)
from app.dominio.inventario import Ingrediente, Inventario, MotivoMerma, MovimientoInventario
from app.dominio.mesa import EstadoMesa, Mesa
from app.dominio.producto import Categoria, IngredienteDeReceta, ProductoMenu
from app.dominio.reabastecimiento import CoberturaPorConsumoPromedio
from app.dominio.reserva import EstadoReserva, Reserva

AHORA = datetime(2026, 10, 19, 13, 0)


class TestInventario:
    def lomo(self) -> ProductoMenu:
        return ProductoMenu(1, "Lomo", "", 30000, Categoria.PLATOS_PRINCIPALES, "🥩",
                            receta=[IngredienteDeReceta(1, 150), IngredienteDeReceta(2, 200)])

    def test_porciones_segun_el_ingrediente_que_mas_limita(self):
        inventario = Inventario([Ingrediente(1, "Arroz", "g", 1000, 100), Ingrediente(2, "Carne", "g", 600, 100)])
        assert inventario.porciones_disponibles(self.lomo()) == 3

    def test_si_no_alcanza_no_descuenta_nada(self):
        arroz, carne = Ingrediente(1, "Arroz", "g", 1000, 100), Ingrediente(2, "Carne", "g", 300, 100)
        with pytest.raises(StockInsuficienteError):
            Inventario([arroz, carne]).consumir([(self.lomo(), 2)])
        assert (arroz.stock, carne.stock) == (1000, 300)

    def test_reporta_los_ingredientes_que_cruzan_el_minimo(self):
        carne = Ingrediente(2, "Carne", "g", 500, 200)
        resultado = Inventario([Ingrediente(1, "Arroz", "g", 1000, 100), carne]).consumir([(self.lomo(), 2)])
        assert resultado.ingredientes_que_cruzaron_minimo == [carne]

    def test_la_merma_no_puede_superar_el_stock(self):
        with pytest.raises(StockInsuficienteError):
            Ingrediente(1, "Arroz", "g", 100, 50).registrar_merma(150)

    def test_entrada_exige_cantidad_positiva_y_proveedor(self):
        with pytest.raises(CantidadInvalidaError):
            MovimientoInventario.entrada(1, 0, "Surtifruver", AHORA, 4)
        with pytest.raises(DatoInvalidoError, match="proveedor"):
            MovimientoInventario.entrada(1, 500, "  ", AHORA, 4)

    def test_merma_por_otro_motivo_exige_descripcion(self):
        with pytest.raises(DatoInvalidoError):
            MovimientoInventario.merma(1, 10, MotivoMerma.OTRO, "", AHORA, 4)

    def test_sugerencia_cubre_tres_dias_de_consumo_mas_el_minimo(self):
        arroz = Ingrediente(1, "Arroz", "g", 1000, 1000)
        sugerencia = CoberturaPorConsumoPromedio().sugerir(arroz, consumo_en_periodo=7000)
        # 1000 g/día × 3 días + 1000 g mínimo − 1000 g en stock = 3000 g
        assert sugerencia.cantidad_sugerida == 3000
        assert sugerencia.dias_restantes == 1.0


class TestReservas:
    def reserva(self, mesa: int = 3, horas: int = 3, personas: int = 4) -> Reserva:
        reserva = Reserva.crear("Ana Pérez", "3001234567", personas, AHORA + timedelta(hours=horas),
                                mesa, 4, AHORA)
        reserva.id = mesa * 100 + horas
        return reserva

    def test_valida_horario_de_atencion(self):
        with pytest.raises(ReservaInvalidaError, match="entre las 11:00 y las 20:00"):
            Reserva.crear("Ana Pérez", "3001234567", 2, AHORA.replace(hour=21), 1, 4, AHORA)

    def test_valida_telefono_y_anticipacion(self):
        with pytest.raises(ReservaInvalidaError, match="teléfono"):
            Reserva.crear("Ana Pérez", "123", 2, AHORA + timedelta(hours=2), 1, 4, AHORA)
        with pytest.raises(ReservaInvalidaError, match="anticipación"):
            Reserva.crear("Ana Pérez", "3001234567", 2, AHORA + timedelta(minutes=5), 1, 4, AHORA)

    def test_asigna_la_mesa_mas_pequena_donde_caben(self):
        mesas = [Mesa(1, 2), Mesa(3, 4), Mesa(7, 6)]
        assert AgendaDeMesas(mesas, [], AHORA).asignar(3, AHORA + timedelta(hours=2)).numero == 3

    def test_no_permite_dos_reservas_cruzadas_en_la_misma_mesa(self):
        agenda = AgendaDeMesas([Mesa(3, 4)], [self.reserva(mesa=3, horas=3)], AHORA)
        with pytest.raises(ConflictoDeReservaError):
            agenda.validar_mesa_elegida(3, 2, AHORA + timedelta(hours=4))
        agenda.validar_mesa_elegida(3, 2, AHORA + timedelta(hours=5))  # Ya terminó: sí se puede.

    def test_mesa_ocupada_no_se_reserva_para_las_proximas_dos_horas(self):
        agenda = AgendaDeMesas([Mesa(3, 4, EstadoMesa.OCUPADA)], [], AHORA)
        with pytest.raises(SinMesasParaReservaError):
            agenda.asignar(2, AHORA + timedelta(hours=1))
        assert agenda.asignar(2, AHORA + timedelta(hours=3)).numero == 3

    def test_la_mesa_se_ve_reservada_media_hora_antes(self):
        reserva = self.reserva(mesa=3, horas=3)
        agenda = AgendaDeMesas([Mesa(3, 4)], [reserva], reserva.inicio - timedelta(minutes=20))
        assert agenda.vista(Mesa(3, 4)).estado == EstadoMesa.RESERVADA

    def test_llegada_solo_dentro_de_la_ventana(self):
        reserva = self.reserva()
        with pytest.raises(AccionDeReservaInvalidaError, match="temprano"):
            reserva.confirmar_llegada(reserva.inicio - timedelta(hours=1))
        reserva.confirmar_llegada(reserva.inicio + timedelta(minutes=10))
        assert reserva.estado == EstadoReserva.CUMPLIDA

    def test_no_asistio_solo_despues_de_la_tolerancia(self):
        reserva = self.reserva()
        with pytest.raises(AccionDeReservaInvalidaError):
            reserva.marcar_no_asistio(reserva.inicio + timedelta(minutes=5))
        reserva.marcar_no_asistio(reserva.inicio + timedelta(minutes=20))
        assert reserva.estado == EstadoReserva.NO_ASISTIO
