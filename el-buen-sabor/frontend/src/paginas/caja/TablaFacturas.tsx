import { formatearHora } from "../../compartido/formatoHora";
import { formatearPesos } from "../../compartido/formatoMoneda";
import type { Factura } from "../../dominio/tipos";

interface Props {
  facturas: Factura[];
  reenviando: number | null;
  onReenviar: (factura: Factura) => void;
  onVerXml: (factura: Factura) => void;
}

const METODO: Record<string, string> = { EFECTIVO: "Efectivo", TARJETA: "Tarjeta", MIXTO: "Mixto" };

/** F-03: facturas del día con su estado ante la DIAN. Las pendientes se reenvían desde aquí. */
export function TablaFacturas({ facturas, reenviando, onReenviar, onVerXml }: Props) {
  if (facturas.length === 0) return <p className="caja__vacio">Aún no hay facturas emitidas.</p>;
  return (
    <table className="tabla">
      <thead>
        <tr>
          <th>Factura</th><th>Mesa</th><th>Hora</th><th>Medio</th>
          <th className="num">Total</th><th>DIAN</th><th aria-label="Acciones" />
        </tr>
      </thead>
      <tbody>
        {facturas.map((f) => (
          <tr key={f.id}>
            <td><strong>{f.numero}</strong></td>
            <td>{f.numeroMesa}</td>
            <td>{formatearHora(f.fechaEmision)}</td>
            <td>{f.metodoPago ? METODO[f.metodoPago] : "—"}</td>
            <td className="num">{formatearPesos(f.total)}</td>
            <td>
              {f.estado === "VALIDADA"
                ? <span className="insignia insignia--lista" title={f.codigoValidacion ?? ""}>Validada</span>
                : <span className="insignia insignia--alerta" title={f.ultimoError ?? ""}>Pendiente</span>}
            </td>
            <td className="tabla__acciones">
              {f.estado !== "VALIDADA" && (
                <button type="button" className="boton boton--secundario boton--chico"
                        disabled={reenviando === f.id} onClick={() => onReenviar(f)}>
                  {reenviando === f.id ? "Enviando…" : "Reintentar envío"}
                </button>
              )}
              <button type="button" className="boton boton--enlace" onClick={() => onVerXml(f)}>XML</button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
