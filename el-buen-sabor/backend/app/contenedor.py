"""Raíz de composición (Composition Root / Inyección de Dependencias).

Es el ÚNICO lugar que conoce todas las capas: decide qué adaptador concreto
recibe cada puerto. Los servicios compartidos se crean una vez; cada petición
obtiene casos de uso nuevos con su propia unidad de trabajo.
"""

from sqlalchemy import Engine

from app.aplicacion.casos_de_uso.autenticacion.gestor_sesion import GestorSesion
from app.aplicacion.casos_de_uso.caja.estrategias_pago import FabricaEstrategiasPago
from app.aplicacion.casos_de_uso.caja.gestor_cobros import GestorCobros
from app.aplicacion.casos_de_uso.caja.gestor_jornada import GestorJornada
from app.aplicacion.casos_de_uso.cocina.gestor_cocina import GestorCocina
from app.aplicacion.casos_de_uso.facturacion.emisor_facturas import EmisorDeFacturas
from app.aplicacion.casos_de_uso.facturacion.gestor_facturacion import GestorFacturacion
from app.aplicacion.casos_de_uso.inventario.gestor_inventario import GestorInventario
from app.aplicacion.casos_de_uso.pedidos.gestor_pedidos import GestorPedidos
from app.aplicacion.casos_de_uso.reservas.gestor_reservas import GestorReservas
from app.aplicacion.casos_de_uso.salon.consultar_salon import ConsultarSalon
from app.aplicacion.puertos import Reloj
from app.configuracion import Configuracion
from app.dominio.agenda_mesas import MejorAjuste
from app.dominio.factura import ResolucionDIAN
from app.dominio.impuestos import CALCULADORAS
from app.dominio.reabastecimiento import CoberturaPorConsumoPromedio
from app.infraestructura.base_de_datos.conexion import crear_fabrica_de_sesiones, crear_motor
from app.infraestructura.base_de_datos.unidad_de_trabajo import UnidadDeTrabajoSQL
from app.infraestructura.eventos.bus_en_memoria import BusDeEventosEnMemoria
from app.infraestructura.integraciones.dian.servicio_dian_simulado import ServicioDIANSimulado
from app.infraestructura.integraciones.pasarela_simulada import PasarelaBancariaSimulada
from app.infraestructura.integraciones.simulador import EstadoDelSimulador
from app.infraestructura.reloj import RelojDelSistema
from app.infraestructura.seguridad.credenciales import ServicioDeCredencialesHMAC


class Contenedor:
    def __init__(self, configuracion: Configuracion, reloj: Reloj | None = None) -> None:
        self.configuracion = configuracion
        self.reloj: Reloj = reloj or RelojDelSistema()
        self.motor: Engine = crear_motor(configuracion.url_base_datos)
        self._fabrica_de_sesiones = crear_fabrica_de_sesiones(self.motor)

        self.bus = BusDeEventosEnMemoria()
        self.simulador = EstadoDelSimulador()
        self.credenciales = ServicioDeCredencialesHMAC(configuracion.clave_secreta)
        self.resolucion = ResolucionDIAN(
            numero=configuracion.resolucion_numero, prefijo=configuracion.resolucion_prefijo,
            desde=configuracion.resolucion_desde, hasta=configuracion.resolucion_hasta,
            clave_tecnica=configuracion.clave_tecnica_dian, nit_emisor=configuracion.nit_emisor,
            ambiente=configuracion.ambiente_dian,
        )
        self.impuesto = CALCULADORAS[configuracion.impuesto_factura]
        self.servicio_dian = ServicioDIANSimulado(self.simulador, self.resolucion, configuracion.razon_social)
        self.estrategias_pago = FabricaEstrategiasPago(PasarelaBancariaSimulada(self.simulador))
        self.emisor_facturas = EmisorDeFacturas(self.resolucion, self.impuesto)
        self.politica_reabastecimiento = CoberturaPorConsumoPromedio()
        self.estrategia_mesas = MejorAjuste()

    # ── Fábricas de casos de uso (una instancia por petición) ──────────────────
    def unidad_de_trabajo(self) -> UnidadDeTrabajoSQL:
        return UnidadDeTrabajoSQL(self._fabrica_de_sesiones)

    def sesion(self) -> GestorSesion:
        return GestorSesion(self.unidad_de_trabajo(), self.credenciales)

    def salon(self) -> ConsultarSalon:
        return ConsultarSalon(self.unidad_de_trabajo(), self.reloj)

    def pedidos(self) -> GestorPedidos:
        return GestorPedidos(self.unidad_de_trabajo(), self.bus, self.reloj)

    def cocina(self) -> GestorCocina:
        return GestorCocina(self.unidad_de_trabajo(), self.bus, self.reloj)

    def facturacion(self) -> GestorFacturacion:
        return GestorFacturacion(self.unidad_de_trabajo(), self.bus, self.reloj, self.servicio_dian)

    def cobros(self) -> GestorCobros:
        return GestorCobros(self.unidad_de_trabajo(), self.bus, self.reloj, self.estrategias_pago,
                            self.emisor_facturas, self.facturacion())

    def jornada(self) -> GestorJornada:
        return GestorJornada(self.unidad_de_trabajo(), self.bus, self.reloj, self.servicio_dian)

    def inventario(self) -> GestorInventario:
        return GestorInventario(self.unidad_de_trabajo(), self.bus, self.reloj,
                                self.politica_reabastecimiento)

    def reservas(self) -> GestorReservas:
        return GestorReservas(self.unidad_de_trabajo(), self.bus, self.reloj, self.estrategia_mesas)
