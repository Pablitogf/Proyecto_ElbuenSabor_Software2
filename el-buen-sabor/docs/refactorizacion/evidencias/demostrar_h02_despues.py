"""Evidencia H-02 después: el emisor ya no recibe la unidad de trabajo y no persiste nada."""
import inspect
from datetime import datetime
from app.dominio.factura import EmisorDeFacturas, ResolucionDIAN
from app.dominio.impuestos import IVA_19
from app.dominio.pedido import DetallePedido, Pedido

print("Firma:", "emitir" + str(inspect.signature(EmisorDeFacturas.emitir)))
resolucion = ResolucionDIAN("1876", "FEBS", 1001, 5000, "clave", "900123456", "2")
pedido = Pedido.registrar(6, [DetallePedido(9, "Ajiaco", 2, 26000)], datetime(2026, 10, 19, 13), 1, 1)
pedido.id = 3
factura = EmisorDeFacturas(resolucion, IVA_19).emitir(pedido, 0, datetime(2026, 10, 19, 13))
print(f"Sin base de datos: {factura.numero}, total {factura.total}, id={factura.id} (sin persistir: solo el repositorio asigna id)")
