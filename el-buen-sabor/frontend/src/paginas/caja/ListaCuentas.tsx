import { formatearPesos } from "../../compartido/formatoMoneda";
import { ETIQUETA_ESTADO_PEDIDO } from "../../dominio/etiquetas";
import type { Pedido } from "../../dominio/tipos";

interface Props {
  cuentas: Pedido[];
  seleccionada: number | null;
  onSeleccionar: (pedido: Pedido) => void;
}

/** IU-03 panel izquierdo: mesas con cuenta. Solo las servidas se pueden cobrar (Contrato 3). */
export function ListaCuentas({ cuentas, seleccionada, onSeleccionar }: Props) {
  if (cuentas.length === 0) {
    return <p className="caja__vacio">No hay mesas con cuenta abierta.</p>;
  }
  return (
    <ul className="cuentas">
      {cuentas.map((cuenta) => {
        const lista = cuenta.estado === "ENTREGADO";
        const platos = cuenta.detalles.reduce((suma, d) => suma + d.cantidad, 0);
        return (
          <li key={cuenta.id}>
            <button
              type="button"
              className={`cuenta ${lista ? "cuenta--lista" : ""}`}
              aria-pressed={cuenta.id === seleccionada}
              onClick={() => onSeleccionar(cuenta)}
            >
              <span className="cuenta__mesa">Mesa {cuenta.numeroMesa}</span>
              <span className="cuenta__total">{formatearPesos(cuenta.total)}</span>
              <span className="cuenta__detalle">{platos} platos</span>
              <span className={`insignia ${lista ? "insignia--lista" : "insignia--neutra"}`}>
                {lista ? "Cuenta lista" : `En servicio · ${ETIQUETA_ESTADO_PEDIDO[cuenta.estado].toLowerCase()}`}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
