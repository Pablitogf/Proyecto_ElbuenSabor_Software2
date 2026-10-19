import { formatearHora } from "../../compartido/formatoHora";
import { formatearPesos } from "../../compartido/formatoMoneda";
import type { ResultadoCobro } from "../../dominio/tipos";

/** IU-03 vista previa de la última factura: número DIAN, mesa, hora, monto y medio de pago. */
export function ComprobanteCobro({ resultado }: { resultado: ResultadoCobro }) {
  const { pago, factura } = resultado;
  const validada = factura.estado === "VALIDADA";
  return (
    <section className={`comprobante ${validada ? "" : "comprobante--pendiente"}`} aria-live="polite">
      <div>
        <p className="comprobante__titulo">
          Factura {factura.numero} · Mesa {factura.numeroMesa} · {formatearHora(factura.fechaEmision)}
        </p>
        <p className="comprobante__detalle">
          Base {formatearPesos(factura.base)} + {factura.nombreImpuesto} {Math.round(factura.tarifaImpuesto * 100)}%{" "}
          {formatearPesos(factura.impuesto)} = <strong>{formatearPesos(factura.total)}</strong>
          {pago.cambio > 0 && <> · Cambio entregado {formatearPesos(pago.cambio)}</>}
        </p>
        <p className="comprobante__cufe" title={factura.cufe}>CUFE {factura.cufe.slice(0, 24)}…</p>
      </div>
      <p className="comprobante__estado">
        {validada ? "✓ Validada por la DIAN" : `DIAN pendiente: ${factura.ultimoError}`}
      </p>
    </section>
  );
}
