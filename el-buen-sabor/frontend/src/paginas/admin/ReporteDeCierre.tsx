import { formatearPesos } from "../../compartido/formatoMoneda";
import type { ReporteCierre } from "../../dominio/tipos";

/** RF-10: número de transacciones, ganancia total y por medio de pago. */
export function ReporteDeCierre({ reporte, previo = false }: { reporte: ReporteCierre; previo?: boolean }) {
  const diferencia = reporte.diferenciaEfectivo;
  return (
    <section className="reporte" aria-label="Reporte de cierre">
      {!previo && <h3>Reporte del cierre {reporte.comprobanteDian && <small>· DIAN {reporte.comprobanteDian}</small>}</h3>}
      <dl className="reporte__datos">
        <dt>Transacciones</dt><dd>{reporte.transacciones}</dd>
        <dt>Ventas totales</dt><dd>{formatearPesos(reporte.totalVentas)}</dd>
        <dt>En efectivo</dt><dd>{formatearPesos(reporte.ventasPorMetodo.EFECTIVO)}</dd>
        <dt>Con tarjeta</dt><dd>{formatearPesos(reporte.ventasPorMetodo.TARJETA)}</dd>
        <dt>Impuestos facturados</dt><dd>{formatearPesos(reporte.impuestoTotal)}</dd>
        <dt>Pedidos cancelados</dt><dd>{reporte.pedidosCancelados}</dd>
        <dt>Efectivo esperado</dt><dd>{formatearPesos(reporte.efectivoEsperado)} <small>(base {formatearPesos(reporte.baseCaja)})</small></dd>
        <dt>Efectivo contado</dt>
        <dd>
          {formatearPesos(reporte.efectivoContado)}{" "}
          {diferencia !== 0 && (
            <span className={diferencia < 0 ? "texto-peligro" : "texto-alerta"}>
              ({diferencia < 0 ? "faltan" : "sobran"} {formatearPesos(Math.abs(diferencia))})
            </span>
          )}
        </dd>
      </dl>
      {!previo && reporte.observacion && <p className="reporte__observacion">Observación: {reporte.observacion}</p>}
    </section>
  );
}
