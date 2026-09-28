"""Inyección de dependencias: aquí se decide qué implementación concreta
recibe cada caso de uso. Es el único lugar que 'conoce' todas las capas."""

from fastapi import Request

from app.aplicacion.casos_de_uso.consultar_menu_disponible import ConsultarMenuDisponible
from app.aplicacion.casos_de_uso.listar_comandas_activas import ListarComandasActivas
from app.aplicacion.casos_de_uso.listar_mesas import ListarMesas
from app.aplicacion.casos_de_uso.registrar_pedido import RegistrarPedido
from app.infraestructura.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSQL
from app.presentacion.tiempo_real.gestor_conexiones import GestorConexiones
from app.presentacion.tiempo_real.notificador_websocket import NotificadorWebSocket


def _nueva_unidad_de_trabajo(request: Request) -> UnidadDeTrabajoSQL:
    return UnidadDeTrabajoSQL(request.app.state.fabrica_de_sesiones)


def obtener_gestor_conexiones(request: Request) -> GestorConexiones:
    return request.app.state.gestor_conexiones


def obtener_listar_mesas(request: Request) -> ListarMesas:
    return ListarMesas(_nueva_unidad_de_trabajo(request))


def obtener_consultar_menu(request: Request) -> ConsultarMenuDisponible:
    return ConsultarMenuDisponible(_nueva_unidad_de_trabajo(request))


def obtener_listar_comandas(request: Request) -> ListarComandasActivas:
    return ListarComandasActivas(_nueva_unidad_de_trabajo(request))


def obtener_registrar_pedido(request: Request) -> RegistrarPedido:
    notificador = NotificadorWebSocket(obtener_gestor_conexiones(request))
    return RegistrarPedido(_nueva_unidad_de_trabajo(request), notificador)
