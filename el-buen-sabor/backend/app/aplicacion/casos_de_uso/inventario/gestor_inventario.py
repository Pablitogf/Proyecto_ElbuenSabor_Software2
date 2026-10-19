"""Gestión de inventario (F-04, CU-04, RF-12, RF-14, RF-17)."""

from dataclasses import dataclass
from datetime import timedelta

from app.aplicacion.puertos import PublicadorEventos, Reloj, UnidadDeTrabajo
from app.dominio.eventos import EventoDeDominio, InventarioActualizado, StockBajoMinimo
from app.dominio.excepciones import IngredienteDuplicadoError, IngredienteNoEncontradoError
from app.dominio.inventario import Ingrediente, MotivoMerma, MovimientoInventario
from app.dominio.reabastecimiento import PoliticaReabastecimiento, SugerenciaCompra
from app.dominio.usuario import Usuario


@dataclass(frozen=True)
class MovimientoConNombre:
    movimiento: MovimientoInventario
    ingrediente: str
    unidad: str


class GestorInventario:
    def __init__(self, unidad_de_trabajo: UnidadDeTrabajo, eventos: PublicadorEventos, reloj: Reloj,
                 politica: PoliticaReabastecimiento, dias_historial: int = 7) -> None:
        self._uow = unidad_de_trabajo
        self._eventos = eventos
        self._reloj = reloj
        self._politica = politica
        self._dias_historial = dias_historial

    # ── Consultas ──────────────────────────────────────────────────────────────
    def ingredientes(self) -> list[Ingrediente]:
        with self._uow:
            return sorted(self._uow.ingredientes.listar(), key=lambda i: i.nombre)

    def movimientos(self, limite: int = 30) -> list[MovimientoConNombre]:
        with self._uow:
            nombres = {i.id: i for i in self._uow.ingredientes.listar()}
            return [
                MovimientoConNombre(m, nombres[m.ingrediente_id].nombre, nombres[m.ingrediente_id].unidad)
                for m in self._uow.movimientos.listar_recientes(limite)
            ]

    def sugerencias_de_compra(self) -> list[SugerenciaCompra]:
        """RF-12: qué pedirle al proveedor, lo más urgente primero."""
        desde = self._reloj.ahora() - timedelta(days=self._dias_historial)
        with self._uow:
            consumo = self._uow.movimientos.consumo_desde(desde)
            sugerencias = [
                self._politica.sugerir(ingrediente, consumo.get(ingrediente.id, 0.0))
                for ingrediente in self._uow.ingredientes.listar()
            ]
        return sorted(
            (s for s in sugerencias if s is not None),
            key=lambda s: (s.dias_restantes is None, s.dias_restantes or 0, s.ingrediente.nombre),
        )

    # ── Comandos ───────────────────────────────────────────────────────────────
    async def crear_ingrediente(self, nombre: str, unidad: str, stock_minimo: float) -> Ingrediente:
        """CU-04 pasos 5-6: el nuevo ingrediente queda listo para usarse en recetas."""
        ingrediente = Ingrediente.crear(nombre, unidad, stock_minimo)
        with self._uow:
            if self._uow.ingredientes.existe_con_nombre(ingrediente.nombre):
                raise IngredienteDuplicadoError(ingrediente.nombre)
            ingrediente = self._uow.ingredientes.agregar(ingrediente)
            self._uow.confirmar()
        await self._eventos.publicar(InventarioActualizado())
        return ingrediente

    async def registrar_entrada(self, ingrediente_id: int, cantidad: float, proveedor: str,
                                usuario: Usuario) -> Ingrediente:
        """CU-04 pasos 3-4 (y 4a). La alerta de mínimo desaparece si el stock se recupera."""
        movimiento = MovimientoInventario.entrada(
            ingrediente_id, cantidad, proveedor, self._reloj.ahora(), usuario.id)
        return await self._mover(ingrediente_id, movimiento, lambda i: i.reponer(cantidad))

    async def registrar_merma(self, ingrediente_id: int, cantidad: float, motivo: MotivoMerma,
                              detalle: str, usuario: Usuario) -> Ingrediente:
        """RF-17: las pérdidas se registran con su causa."""
        movimiento = MovimientoInventario.merma(
            ingrediente_id, cantidad, motivo, detalle, self._reloj.ahora(), usuario.id)
        return await self._mover(ingrediente_id, movimiento, lambda i: i.registrar_merma(cantidad))

    async def cambiar_minimo(self, ingrediente_id: int, nuevo_minimo: float) -> Ingrediente:
        """CU-04 paso 8: si el stock ya está por debajo del nuevo mínimo, se alerta."""
        with self._uow:
            ingrediente = self._ingrediente(ingrediente_id)
            ingrediente.cambiar_minimo(nuevo_minimo)
            self._uow.ingredientes.guardar(ingrediente)
            self._uow.confirmar()
        await self._eventos.publicar(InventarioActualizado(), *self._alerta_si_aplica(ingrediente))
        return ingrediente

    # ── Internos ───────────────────────────────────────────────────────────────
    async def _mover(self, ingrediente_id: int, movimiento: MovimientoInventario, aplicar) -> Ingrediente:
        with self._uow:
            ingrediente = self._ingrediente(ingrediente_id)
            estaba_bien = not ingrediente.esta_bajo_minimo
            aplicar(ingrediente)
            self._uow.ingredientes.guardar(ingrediente)
            self._uow.movimientos.agregar(movimiento)
            self._uow.confirmar()
        alertas = self._alerta_si_aplica(ingrediente) if estaba_bien else []
        await self._eventos.publicar(InventarioActualizado(), *alertas)
        return ingrediente

    @staticmethod
    def _alerta_si_aplica(ingrediente: Ingrediente) -> list[EventoDeDominio]:
        if not ingrediente.esta_bajo_minimo:
            return []
        return [StockBajoMinimo(ingrediente.id, ingrediente.nombre, ingrediente.stock,
                                ingrediente.stock_minimo, ingrediente.unidad)]

    def _ingrediente(self, ingrediente_id: int) -> Ingrediente:
        ingrediente = self._uow.ingredientes.obtener(ingrediente_id)
        if ingrediente is None:
            raise IngredienteNoEncontradoError(ingrediente_id)
        return ingrediente
