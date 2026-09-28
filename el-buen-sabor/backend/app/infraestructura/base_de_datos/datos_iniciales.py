"""Datos de demostración: mesas, ingredientes, menú con recetas y dos pedidos
previos para que la pantalla de cocina no arranque vacía."""

from datetime import datetime, timedelta

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.dominio.mesa import EstadoMesa
from app.dominio.pedido import EstadoPedido
from app.dominio.producto import Categoria
from app.infraestructura.base_de_datos.conexion import ModeloBase
from app.infraestructura.base_de_datos.modelos import (
    DetallePedidoModelo,
    IngredienteModelo,
    MesaModelo,
    PedidoModelo,
    ProductoModelo,
    RecetaModelo,
)

MESAS_OCUPADAS_AL_INICIO = {3, 6}
CANTIDAD_DE_MESAS = 8

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

# (mesa, minutos transcurridos, [(producto_id, cantidad)])
PEDIDOS_PREVIOS = [
    (3, 12, [(7, 2), (1, 2)]),
    (6, 4, [(9, 1), (5, 1), (16, 1)]),
]


def reiniciar_base_de_datos(motor: Engine) -> None:
    """Borra todo y vuelve a cargar los datos de demostración."""
    ModeloBase.metadata.drop_all(motor)
    inicializar_base_de_datos(motor)


def inicializar_base_de_datos(motor: Engine) -> None:
    """Crea las tablas y carga datos solo si la base está vacía."""
    ModeloBase.metadata.create_all(motor)
    with Session(motor) as sesion:
        if sesion.scalar(select(MesaModelo).limit(1)) is None:
            _cargar_datos_de_demostracion(sesion)
            sesion.commit()


def _cargar_datos_de_demostracion(sesion: Session) -> None:
    sesion.add_all(_crear_mesas())
    sesion.add_all(_crear_ingredientes())
    sesion.add_all(_crear_productos())
    sesion.flush()
    sesion.add_all(_crear_pedidos_previos())


def _crear_mesas() -> list[MesaModelo]:
    return [
        MesaModelo(
            numero=numero,
            capacidad=4,
            estado=(EstadoMesa.OCUPADA if numero in MESAS_OCUPADAS_AL_INICIO
                    else EstadoMesa.DISPONIBLE).value,
        )
        for numero in range(1, CANTIDAD_DE_MESAS + 1)
    ]


def _crear_ingredientes() -> list[IngredienteModelo]:
    return [
        IngredienteModelo(id=id_, nombre=nombre, unidad=unidad, stock=stock, stock_minimo=minimo)
        for id_, nombre, unidad, stock, minimo in INGREDIENTES
    ]


def _crear_productos() -> list[ProductoModelo]:
    return [
        ProductoModelo(
            id=id_,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria=categoria.value,
            icono=icono,
            receta=[
                RecetaModelo(ingrediente_id=ingrediente_id, cantidad_por_porcion=cantidad)
                for ingrediente_id, cantidad in receta
            ],
        )
        for id_, nombre, descripcion, precio, categoria, icono, receta in PRODUCTOS
    ]


def _crear_pedidos_previos() -> list[PedidoModelo]:
    productos_por_id = {producto[0]: producto for producto in PRODUCTOS}
    ahora = datetime.now()
    return [
        PedidoModelo(
            numero_mesa=mesa,
            fecha_hora=ahora - timedelta(minutes=minutos),
            estado=EstadoPedido.REGISTRADO.value,
            detalles=[
                DetallePedidoModelo(
                    producto_id=producto_id,
                    nombre_producto=productos_por_id[producto_id][1],
                    cantidad=cantidad,
                    precio_unitario=productos_por_id[producto_id][3],
                )
                for producto_id, cantidad in items
            ],
        )
        for mesa, minutos, items in PEDIDOS_PREVIOS
    ]
