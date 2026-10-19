"""Punto de entrada del backend: arma la aplicación conectando todas las capas."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.aplicacion.puertos import Reloj
from app.configuracion import Configuracion
from app.contenedor import Contenedor
from app.infraestructura.base_de_datos.datos_iniciales import inicializar_base_de_datos
from app.presentacion.manejo_de_errores import registrar_manejadores_de_error
from app.presentacion.rutas import (
    caja,
    cocina,
    demostracion,
    inventario,
    pedidos,
    reservas,
    salon,
    sesion,
    tiempo_real,
)
from app.presentacion.tiempo_real.difusor_eventos import DifusorDeEventos
from app.presentacion.tiempo_real.gestor_conexiones import GestorConexiones

ENRUTADORES = [
    sesion.enrutador, salon.enrutador, pedidos.enrutador, cocina.enrutador, caja.enrutador,
    inventario.enrutador, reservas.enrutador, demostracion.enrutador, tiempo_real.enrutador,
]


def crear_aplicacion(configuracion: Configuracion | None = None, reloj: Reloj | None = None) -> FastAPI:
    contenedor = Contenedor(configuracion or Configuracion(), reloj)
    conexiones = GestorConexiones()
    contenedor.bus.suscribir(DifusorDeEventos(conexiones))  # Observer: eventos → pantallas.

    @asynccontextmanager
    async def ciclo_de_vida(_: FastAPI):
        inicializar_base_de_datos(contenedor.motor, contenedor.reloj.ahora())
        yield
        contenedor.motor.dispose()

    aplicacion = FastAPI(
        title="El Buen Sabor — API",
        description="Pedidos, cocina, caja, facturación DIAN, inventario y reservas (F-01 a F-06).",
        version="0.2.0",
        lifespan=ciclo_de_vida,
    )
    aplicacion.state.contenedor = contenedor
    aplicacion.state.conexiones = conexiones
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=contenedor.configuracion.origenes_permitidos,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    registrar_manejadores_de_error(aplicacion)
    for enrutador in ENRUTADORES:
        aplicacion.include_router(enrutador)
    return aplicacion


app = crear_aplicacion()
