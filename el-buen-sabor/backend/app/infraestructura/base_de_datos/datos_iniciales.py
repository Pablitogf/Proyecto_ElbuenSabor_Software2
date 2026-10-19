"""Datos de demostración para presentar las 6 funcionalidades sin preparar nada:

- Un usuario por rol (los PIN están en el README).
- Jornada de caja abierta con base de $200.000.
- Mesa 2 con pedido LISTO (el mesero ve la notificación), mesa 3 EN PREPARACIÓN
  (cocina), mesa 6 ENTREGADO (lista para cobrar en caja).
- Reserva que aparta la mesa 7 en 20 minutos, otra en la noche y otra mañana.
- Ingredientes ya bajo el mínimo (alertas) e historial de consumo de 7 días
  para la sugerencia de compra.
"""

from datetime import datetime, timedelta
from functools import lru_cache

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.dominio.estados_pedido import EstadoPedido
from app.dominio.inventario import TipoMovimiento
from app.dominio.jornada import EstadoJornada
from app.dominio.mesa import EstadoMesa
from app.dominio.producto import Categoria
from app.dominio.reserva import HORA_APERTURA, ULTIMA_RESERVA, EstadoReserva
from app.dominio.usuario import Rol
from app.infraestructura.base_de_datos.conexion import ModeloBase
from app.infraestructura.base_de_datos.modelos import (
    DetallePedidoModelo,
    IngredienteModelo,
    JornadaModelo,
    MesaModelo,
    MovimientoInventarioModelo,
    PedidoModelo,
    ProductoModelo,
    RecetaModelo,
    ReservaModelo,
    UsuarioModelo,
)
from app.infraestructura.seguridad.credenciales import generar_hash_pin

# (id, nombre, usuario, rol, PIN)
USUARIOS = [
    (1, "Laura Gómez", "laura", Rol.MESERO, "1111"),
    (2, "Carlos Muñoz", "carlos", Rol.COCINERO, "2222"),
    (3, "Diana Restrepo", "diana", Rol.CAJERO, "3333"),
    (4, "Sofía Arango", "admin", Rol.ADMINISTRADOR, "0000"),
]
ID_MESERO, ID_ADMIN = 1, 4
BASE_DE_CAJA = 200_000

CAPACIDAD_POR_MESA = {1: 2, 2: 2, 3: 4, 4: 4, 5: 4, 6: 4, 7: 6, 8: 8}

# (id, nombre, unidad, stock, stock_minimo)
INGREDIENTES = [
    (1, "Arroz", "g", 5000, 1000),
    (2, "Frijol", "g", 3000, 600),
    (3, "Carne de res", "g", 4000, 800),
    (4, "Chicharrón", "g", 1500, 300),
    (5, "Huevo", "und", 30, 6),
    (6, "Plátano maduro", "und", 20, 4),
    (7, "Aguacate", "und", 10, 2),
    (8, "Pollo", "g", 3000, 600),
    (9, "Papa", "g", 6000, 1000),
    (10, "Mazorca", "und", 15, 3),
    (11, "Mojarra", "und", 0, 2),
    (12, "Limón", "und", 40, 8),
    (13, "Mora", "g", 2000, 400),
    (14, "Leche", "ml", 5000, 1000),
    (15, "Azúcar", "g", 3000, 500),
    (16, "Harina de maíz", "g", 3000, 600),
    (17, "Queso", "g", 2000, 400),
    (18, "Plátano verde", "und", 25, 5),
    (19, "Gaseosa personal", "und", 24, 6),
    (20, "Cerveza", "und", 36, 12),
    (21, "Aguardiente (media)", "und", 6, 2),
    (22, "Tomate", "g", 2000, 400),
    (23, "Cebolla", "g", 2000, 400),
    (24, "Porción de torta tres leches", "und", 2, 2),
    (25, "Breva", "und", 0, 6),
    (26, "Yuca", "g", 3000, 600),
    (27, "Costilla de res", "g", 2500, 500),
]

# (id, nombre, descripción, precio COP, categoría, icono, receta[(ingrediente_id, cantidad)])
PRODUCTOS = [
    (1, "Limonada natural", "Limón recién exprimido, hielo y un toque de azúcar.", 6000,
     Categoria.BEBIDAS, "🍋", [(12, 2), (15, 30)]),
    (2, "Jugo de mora en leche", "Mora licuada con leche entera.", 7000,
     Categoria.BEBIDAS, "🥤", [(13, 150), (14, 200), (15, 30)]),
    (3, "Gaseosa personal", "Botella de 350 ml bien fría.", 4500,
     Categoria.BEBIDAS, "🫧", [(19, 1)]),
    (4, "Empanadas x3", "Masa de maíz rellena de carne y papa, con ají.", 8000,
     Categoria.ENTRADAS, "🥟", [(16, 150), (3, 60), (9, 90)]),
    (5, "Patacones con hogao", "Plátano verde frito con hogao de tomate y cebolla.", 9000,
     Categoria.ENTRADAS, "🍌", [(18, 1), (22, 80), (23, 50)]),
    (6, "Arepa con queso", "Arepa asada rellena de queso campesino.", 6500,
     Categoria.ENTRADAS, "🫓", [(16, 120), (17, 60)]),
    (7, "Bandeja paisa", "Frijoles, arroz, carne molida, chicharrón, huevo, maduro y aguacate.",
     32000, Categoria.PLATOS_PRINCIPALES, "🍛",
     [(2, 200), (1, 150), (3, 150), (4, 120), (5, 1), (6, 1), (7, 0.5)]),
    (8, "Lomo saltado", "Res salteada con cebolla, tomate y papas fritas, con arroz.", 30000,
     Categoria.PLATOS_PRINCIPALES, "🥩", [(3, 200), (23, 80), (22, 80), (9, 200), (1, 150)]),
    (9, "Ajiaco santafereño", "Sopa de papas con pollo desmechado, mazorca y aguacate.", 26000,
     Categoria.PLATOS_PRINCIPALES, "🍲", [(8, 200), (9, 300), (10, 1), (7, 0.5)]),
    (10, "Mojarra frita", "Mojarra entera frita con patacón, arroz de coco y limón.", 34000,
     Categoria.PLATOS_PRINCIPALES, "🐟", [(11, 1), (18, 1), (1, 150), (12, 1)]),
    (11, "Costilla en salsa criolla", "Costilla de res en salsa de tomate con yuca cocida.", 29000,
     Categoria.PLATOS_PRINCIPALES, "🍖", [(27, 350), (26, 200), (22, 100), (23, 60)]),
    (12, "Pollo asado", "Cuarto de pollo asado con papa salada y arroz.", 24000,
     Categoria.PLATOS_PRINCIPALES, "🍗", [(8, 350), (9, 200), (1, 150)]),
    (13, "Arroz con leche", "Arroz cremoso con canela.", 7000,
     Categoria.POSTRES, "🍮", [(1, 60), (14, 250), (15, 40)]),
    (14, "Torta tres leches", "Bizcocho húmedo bañado en tres leches.", 9000,
     Categoria.POSTRES, "🍰", [(24, 1)]),
    (15, "Brevas con arequipe", "Brevas en almíbar con arequipe y queso.", 8500,
     Categoria.POSTRES, "🍯", [(25, 3), (17, 40)]),
    (16, "Cerveza nacional", "Botella de 330 ml.", 6000,
     Categoria.LICORES, "🍺", [(20, 1)]),
    (17, "Aguardiente (media)", "Media botella de aguardiente.", 45000,
     Categoria.LICORES, "🥃", [(21, 1)]),
]

# (mesa, minutos transcurridos, estado, platos preparados, [(producto_id, cantidad)])
PEDIDOS_PREVIOS = [
    (2, 22, EstadoPedido.LISTO_PARA_SERVIR, True, [(12, 1), (3, 1)]),
    (3, 12, EstadoPedido.EN_PREPARACION, False, [(7, 2), (1, 2)]),
    (6, 48, EstadoPedido.ENTREGADO, True, [(9, 2), (5, 1), (16, 2), (13, 1)]),
]

# Consumo diario aproximado de los últimos 7 días (ingrediente_id, cantidad por día).
CONSUMO_HISTORICO_DIARIO = [(1, 900), (3, 700), (8, 900), (9, 1700), (12, 12), (20, 10), (2, 400)]


@lru_cache
def _hash_pin(pin: str) -> str:
    """Se calcula una vez por proceso: PBKDF2 es lento a propósito."""
    return generar_hash_pin(pin)


def reiniciar_base_de_datos(motor: Engine, ahora: datetime) -> None:
    """Borra todo y vuelve a cargar los datos de demostración."""
    ModeloBase.metadata.drop_all(motor)
    inicializar_base_de_datos(motor, ahora)


def inicializar_base_de_datos(motor: Engine, ahora: datetime) -> None:
    """Crea las tablas y carga datos solo si la base está vacía."""
    ModeloBase.metadata.create_all(motor)
    with Session(motor) as sesion:
        if sesion.scalar(select(UsuarioModelo).limit(1)) is None:
            _cargar(sesion, ahora)
            sesion.commit()


def _cargar(sesion: Session, ahora: datetime) -> None:
    sesion.add_all(_usuarios())
    sesion.flush()
    jornada = JornadaModelo(fecha_apertura=ahora.replace(hour=10, minute=30, second=0),
                            base_caja=BASE_DE_CAJA, abierta_por=ID_ADMIN,
                            estado=EstadoJornada.ABIERTA.value)
    sesion.add(jornada)
    sesion.add_all(_mesas())
    sesion.add_all(_ingredientes())
    sesion.add_all(_productos())
    sesion.flush()
    sesion.add_all(_pedidos_previos(ahora, jornada.id))
    sesion.add_all(_reservas(ahora))
    sesion.add_all(_historial_de_consumo(ahora))


def _usuarios() -> list[UsuarioModelo]:
    return [UsuarioModelo(id=id_, nombre=nombre, nombre_usuario=usuario, rol=rol.value,
                          hash_pin=_hash_pin(pin))
            for id_, nombre, usuario, rol, pin in USUARIOS]


def _mesas() -> list[MesaModelo]:
    ocupadas = {mesa for mesa, *_ in PEDIDOS_PREVIOS}
    return [
        MesaModelo(numero=numero, capacidad=capacidad,
                   estado=(EstadoMesa.OCUPADA if numero in ocupadas else EstadoMesa.DISPONIBLE).value)
        for numero, capacidad in CAPACIDAD_POR_MESA.items()
    ]


def _ingredientes() -> list[IngredienteModelo]:
    return [IngredienteModelo(id=id_, nombre=nombre, unidad=unidad, stock=stock, stock_minimo=minimo)
            for id_, nombre, unidad, stock, minimo in INGREDIENTES]


def _productos() -> list[ProductoModelo]:
    return [
        ProductoModelo(
            id=id_, nombre=nombre, descripcion=descripcion, precio=precio,
            categoria=categoria.value, icono=icono,
            receta=[RecetaModelo(ingrediente_id=i, cantidad_por_porcion=c) for i, c in receta],
        )
        for id_, nombre, descripcion, precio, categoria, icono, receta in PRODUCTOS
    ]


def _pedidos_previos(ahora: datetime, jornada_id: int) -> list[PedidoModelo]:
    productos = {p[0]: p for p in PRODUCTOS}
    pedidos = []
    for mesa, minutos, estado, preparados, items in PEDIDOS_PREVIOS:
        registrado = ahora - timedelta(minutes=minutos)
        pedidos.append(PedidoModelo(
            numero_mesa=mesa, fecha_hora=registrado, estado=estado.value, mesero_id=ID_MESERO,
            jornada_id=jornada_id,
            hora_listo=ahora - timedelta(minutes=3) if estado == EstadoPedido.LISTO_PARA_SERVIR else None,
            detalles=[
                DetallePedidoModelo(producto_id=pid, nombre_producto=productos[pid][1], cantidad=cantidad,
                                    precio_unitario=productos[pid][3],
                                    preparado=preparados or indice == 0)
                for indice, (pid, cantidad) in enumerate(items)
            ],
        ))
    return pedidos


def _reservas(ahora: datetime) -> list[ReservaModelo]:
    def reserva(cliente: str, telefono: str, personas: int, inicio: datetime, mesa: int) -> ReservaModelo:
        return ReservaModelo(nombre_cliente=cliente, telefono=telefono, personas=personas,
                             inicio=inicio.replace(second=0), numero_mesa=mesa, creada_por=ID_ADMIN,
                             estado=EstadoReserva.PENDIENTE.value)

    manana = ahora + timedelta(days=1)
    mas_tarde = ahora + timedelta(hours=3)
    if not HORA_APERTURA <= mas_tarde.time() <= ULTIMA_RESERVA:  # Siempre dentro del horario.
        mas_tarde = manana.replace(hour=19, minute=30)
    return [
        # Aparta la mesa 7 desde ya: sirve para mostrar el estado "Reservada" y la llegada.
        reserva("Familia Ramírez", "3104567890", 6, ahora + timedelta(minutes=20), 7),
        reserva("Juliana Ospina", "3012223344", 2, mas_tarde, 1),
        reserva("Cumpleaños de Mateo", "3157778899", 8, manana.replace(hour=13, minute=0), 8),
    ]


def _historial_de_consumo(ahora: datetime) -> list[MovimientoInventarioModelo]:
    return [
        MovimientoInventarioModelo(ingrediente_id=ingrediente_id, tipo=TipoMovimiento.SALIDA_PEDIDO.value,
                                   cantidad=cantidad, fecha_hora=ahora - timedelta(days=dia, hours=2),
                                   detalle="Consumo histórico (datos de demostración)")
        for dia in range(1, 8)
        for ingrediente_id, cantidad in CONSUMO_HISTORICO_DIARIO
    ]
