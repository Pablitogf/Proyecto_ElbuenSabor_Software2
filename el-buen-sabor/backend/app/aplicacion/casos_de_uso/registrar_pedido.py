from collections import Counter
from dataclasses import dataclass

from app.aplicacion.puertos import NotificadorEventos, UnidadDeTrabajo
from app.dominio.excepciones import (
    MesaNoEncontradaError,
    ProductoInactivoError,
    ProductoNoEncontradoError,
)
from app.dominio.inventario import Inventario
from app.dominio.mesa import Mesa
from app.dominio.pedido import DetallePedido, Pedido
from app.dominio.producto import ProductoMenu


@dataclass(frozen=True)
class ItemSolicitado:
    producto_id: int
    cantidad: int


class RegistrarPedido:
    """F-01 / CU-01 / Contrato 1 (crearPedido).

    1. Verifica que la mesa exista y esté disponible (RD-01).
    2. Verifica que los platos existan y estén activos (RD-02).
    3. Vuelve a consultar el inventario y descuenta ingredientes (RF-03, RF-05).
    4. Registra el pedido y ocupa la mesa en una sola transacción.
    5. Envía la comanda a cocina en tiempo real (RF-02).
    """

    def __init__(
        self, unidad_de_trabajo: UnidadDeTrabajo, notificador: NotificadorEventos
    ) -> None:
        self._uow = unidad_de_trabajo
        self._notificador = notificador

    async def ejecutar(self, numero_mesa: int, items: list[ItemSolicitado]) -> Pedido:
        with self._uow:
            mesa = self._obtener_mesa(numero_mesa)
            productos_con_cantidad = self._obtener_productos_activos(items)

            pedido = Pedido.registrar(numero_mesa, self._crear_detalles(productos_con_cantidad))
            self._descontar_inventario(productos_con_cantidad)
            mesa.ocupar()

            self._uow.mesas.guardar(mesa)
            pedido_guardado = self._uow.pedidos.agregar(pedido)
            self._uow.confirmar()

        await self._notificador.notificar_pedido_registrado(pedido_guardado, mesa)
        return pedido_guardado

    def _obtener_mesa(self, numero_mesa: int) -> Mesa:
        mesa = self._uow.mesas.obtener(numero_mesa)
        if mesa is None:
            raise MesaNoEncontradaError(numero_mesa)
        return mesa

    def _obtener_productos_activos(
        self, items: list[ItemSolicitado]
    ) -> list[tuple[ProductoMenu, int]]:
        cantidades_por_producto = self._agrupar_cantidades(items)
        return [
            (self._obtener_producto_activo(producto_id), cantidad)
            for producto_id, cantidad in cantidades_por_producto.items()
        ]

    @staticmethod
    def _agrupar_cantidades(items: list[ItemSolicitado]) -> Counter[int]:
        """Si el mismo plato llega dos veces, se suma en un solo renglón."""
        cantidades: Counter[int] = Counter()
        for item in items:
            cantidades[item.producto_id] += item.cantidad
        return cantidades

    def _obtener_producto_activo(self, producto_id: int) -> ProductoMenu:
        producto = self._uow.productos.obtener(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(producto_id)
        if not producto.activo:
            raise ProductoInactivoError(producto.nombre)
        return producto

    @staticmethod
    def _crear_detalles(
        productos_con_cantidad: list[tuple[ProductoMenu, int]],
    ) -> list[DetallePedido]:
        return [
            DetallePedido(
                producto_id=producto.id,
                nombre_producto=producto.nombre,
                cantidad=cantidad,
                precio_unitario=producto.precio,
            )
            for producto, cantidad in productos_con_cantidad
        ]

    def _descontar_inventario(self, productos_con_cantidad: list[tuple[ProductoMenu, int]]) -> None:
        inventario = Inventario(self._uow.ingredientes.listar())
        inventario.consumir(productos_con_cantidad)
        self._uow.ingredientes.guardar_todos(inventario.ingredientes())
