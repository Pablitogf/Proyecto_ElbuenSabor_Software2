"""Punto de entrada del backend: arma la aplicación conectando todas las capas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.configuracion import Configuracion
from app.infraestructura.base_de_datos.conexion import crear_fabrica_de_sesiones, crear_motor
from app.infraestructura.base_de_datos.datos_iniciales import inicializar_base_de_datos
from app.presentacion.manejo_de_errores import registrar_manejadores_de_error
from app.presentacion.rutas import comandas, demostracion, menu, mesas, pedidos, tiempo_real
from app.presentacion.tiempo_real.gestor_conexiones import GestorConexiones

ENRUTADORES = [
    mesas.enrutador,
    menu.enrutador,
    pedidos.enrutador,
    comandas.enrutador,
    tiempo_real.enrutador,
    demostracion.enrutador,
]


def crear_aplicacion(configuracion: Configuracion | None = None) -> FastAPI:
    configuracion = configuracion or Configuracion()
    motor = crear_motor(configuracion.url_base_datos)

    @asynccontextmanager
    async def ciclo_de_vida(_: FastAPI):
        inicializar_base_de_datos(motor)
        yield
        motor.dispose()

    aplicacion = FastAPI(
        title="El Buen Sabor — API de pedidos",
        description="Vertical slice F-01: Registrar pedido desde la tablet del mesero.",
        version="0.1.0",
        lifespan=ciclo_de_vida,
    )
    aplicacion.state.motor = motor
    aplicacion.state.fabrica_de_sesiones = crear_fabrica_de_sesiones(motor)
    aplicacion.state.gestor_conexiones = GestorConexiones()

    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=configuracion.origenes_permitidos,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    registrar_manejadores_de_error(aplicacion)
    for enrutador in ENRUTADORES:
        aplicacion.include_router(enrutador)
    return aplicacion


app = crear_aplicacion()
