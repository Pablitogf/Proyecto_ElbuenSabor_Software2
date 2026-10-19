from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.dominio.usuario import Permiso, Usuario
from app.presentacion.dependencias import ContenedorDep, UsuarioDep, requiere
from app.presentacion.esquemas.base import ErrorRespuesta
from app.presentacion.esquemas.caja import (
    AperturaSolicitud,
    CierreSolicitud,
    CobroRespuesta,
    CobroSolicitud,
    FacturaRespuesta,
    JornadaRespuesta,
    ReporteCierreRespuesta,
    ResumenDelDiaRespuesta,
)
from app.presentacion.esquemas.pedidos import PedidoRespuesta

enrutador = APIRouter(prefix="/api", tags=["Caja y facturación (F-02, F-03)"])
ERRORES = {404: {"model": ErrorRespuesta}, 409: {"model": ErrorRespuesta},
           422: {"model": ErrorRespuesta}, 502: {"model": ErrorRespuesta}}
PuedeCobrar = Annotated[Usuario, Depends(requiere(Permiso.COBRAR))]
PuedeVerCaja = Annotated[Usuario, Depends(requiere(Permiso.VER_REGISTROS_CAJA))]
PuedeCerrar = Annotated[Usuario, Depends(requiere(Permiso.CERRAR_CAJA))]


# ── Cobro (F-02) ──────────────────────────────────────────────────────────────
@enrutador.get("/caja/cuentas", response_model=list[PedidoRespuesta])
def cuentas_abiertas(_: PuedeCobrar, contenedor: ContenedorDep):
    return [PedidoRespuesta.desde(p) for p in contenedor.cobros().cuentas_abiertas()]


@enrutador.post("/caja/cobros", response_model=CobroRespuesta, responses=ERRORES)
async def cobrar_cuenta(solicitud: CobroSolicitud, cajero: PuedeCobrar, contenedor: ContenedorDep):
    """CU-02: valida, cobra (tarjeta vía pasarela), libera la mesa, factura y envía a la DIAN."""
    resultado = await contenedor.cobros().cobrar(
        solicitud.pedido_id, [p.a_dominio() for p in solicitud.pagos], cajero)
    detalle = contenedor.facturacion().detalle(resultado.factura.id)
    return CobroRespuesta.desde(resultado, detalle.pedido.numero_mesa)


# ── Facturación electrónica (F-03) ─────────────────────────────────────────────
@enrutador.get("/facturas", response_model=list[FacturaRespuesta])
def facturas_recientes(_: PuedeVerCaja, contenedor: ContenedorDep):
    return [FacturaRespuesta.con_detalle(d) for d in contenedor.facturacion().recientes()]


@enrutador.post("/facturas/{factura_id}/reenviar", response_model=FacturaRespuesta, responses=ERRORES)
async def reenviar_a_dian(factura_id: int, contenedor: ContenedorDep,
                          _: Annotated[Usuario, Depends(requiere(Permiso.GESTIONAR_FACTURAS))]):
    await contenedor.facturacion().enviar_a_dian(factura_id)
    return FacturaRespuesta.con_detalle(contenedor.facturacion().detalle(factura_id))


@enrutador.get("/facturas/{factura_id}/xml", responses={200: {"content": {"application/xml": {}}}})
def descargar_xml(factura_id: int, _: PuedeVerCaja, contenedor: ContenedorDep) -> Response:
    """SWR-07: documento en formato UBL 2.1 que se envió a la DIAN."""
    factura = contenedor.facturacion().detalle(factura_id).factura
    return Response(
        content=factura.xml or "", media_type="application/xml",
        headers={"Content-Disposition": f'inline; filename="{factura.numero}.xml"'},
    )


# ── Jornada y cierre de caja (RF-10, RF-11) ────────────────────────────────────
@enrutador.get("/jornada", response_model=JornadaRespuesta)
def jornada_actual(_: UsuarioDep, contenedor: ContenedorDep):
    """Cualquier rol la consulta: si la caja está cerrada, las tablets lo muestran."""
    return JornadaRespuesta.desde(contenedor.jornada().resumen().jornada)


@enrutador.get("/jornada/resumen", response_model=ResumenDelDiaRespuesta)
def resumen_del_dia(_: PuedeVerCaja, contenedor: ContenedorDep):
    return ResumenDelDiaRespuesta.desde(contenedor.jornada().resumen())


@enrutador.post("/jornada/previsualizar-cierre", response_model=ReporteCierreRespuesta)
def previsualizar_cierre(solicitud: CierreSolicitud, _: PuedeCerrar, contenedor: ContenedorDep):
    reporte = contenedor.jornada().previsualizar_cierre(solicitud.efectivo_contado, solicitud.observacion)
    return ReporteCierreRespuesta.desde(reporte)


@enrutador.post("/jornada/cerrar", response_model=JornadaRespuesta, responses=ERRORES)
async def cerrar_caja(solicitud: CierreSolicitud, administrador: PuedeCerrar, contenedor: ContenedorDep):
    jornada = await contenedor.jornada().cerrar(
        solicitud.efectivo_contado, solicitud.observacion, solicitud.confirmar_inconsistencias,
        administrador)
    return JornadaRespuesta.desde(jornada)


@enrutador.post("/jornada/abrir", response_model=JornadaRespuesta, responses=ERRORES)
async def abrir_caja(solicitud: AperturaSolicitud, administrador: PuedeCerrar, contenedor: ContenedorDep):
    return JornadaRespuesta.desde(await contenedor.jornada().abrir(solicitud.base_caja, administrador))
