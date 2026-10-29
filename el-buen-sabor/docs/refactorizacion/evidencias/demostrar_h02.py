"""Evidencia H-02: EmisorDeFacturas depende de una UnidadDeTrabajo ya abierta."""
from datetime import datetime
from app.configuracion import Configuracion
from app.contenedor import Contenedor
from app.infraestructura.base_de_datos.datos_iniciales import inicializar_base_de_datos

c = Contenedor(Configuracion(url_base_datos="sqlite:///h02_demo.db"))
inicializar_base_de_datos(c.motor, datetime(2026, 10, 19, 13))
ahora = datetime(2026, 10, 19, 13)

uow = c.unidad_de_trabajo()
with uow:
    pedido = uow.pedidos.obtener(3)
pedido.registrar_pago()

# Caso 1: la unidad de trabajo ya se cerró (se salió del bloque `with`).
factura = c.emisor_facturas.emitir(uow, pedido, ahora)
print(f"Caso 1 · UoW cerrada: emitir() NO falla y devuelve {factura.numero} (id={factura.id})")
with c.unidad_de_trabajo() as verificacion:
    guardadas = verificacion.facturas.listar_recientes(10)
print(f"         Facturas realmente guardadas en la base: {len(guardadas)} -> se perdió en silencio")

# Caso 2: una unidad de trabajo que nunca se abrió.
try:
    c.emisor_facturas.emitir(c.unidad_de_trabajo(), pedido, ahora)
except Exception as error:
    print(f"Caso 2 · UoW sin abrir: {type(error).__name__}: {error}")
uow._sesion.close()
with c.unidad_de_trabajo() as otra:
    print(f"Tras cerrar la sesión prestada, facturas en la base: {len(otra.facturas.listar_recientes(10))}")
