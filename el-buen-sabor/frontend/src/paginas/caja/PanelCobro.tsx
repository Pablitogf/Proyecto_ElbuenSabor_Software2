import { useEffect, useMemo, useState } from "react";
import { formatearPesos, leerPesos } from "../../compartido/formatoMoneda";
import { montosSugeridos, planearCobro, type ModoPago } from "../../dominio/cobro";
import type { LineaPagoSolicitud, Pedido } from "../../dominio/tipos";

interface Props {
  cuenta: Pedido;
  cobrando: boolean;
  cajaCerrada: boolean;
  onCobrar: (pagos: LineaPagoSolicitud[]) => void;
}

const MODOS: { valor: ModoPago; nombre: string }[] = [
  { valor: "EFECTIVO", nombre: "Efectivo" },
  { valor: "TARJETA", nombre: "Tarjeta" },
  { valor: "MIXTO", nombre: "Efectivo + tarjeta" },
];

/** IU-03 panel derecho: desglose, medio de pago, cambio en vivo y cobro (F-02). */
export function PanelCobro({ cuenta, cobrando, cajaCerrada, onCobrar }: Props) {
  const [modo, setModo] = useState<ModoPago>("EFECTIVO");
  const [recibido, setRecibido] = useState("");
  const [parteEfectivo, setParteEfectivo] = useState("");

  useEffect(() => {
    setModo("EFECTIVO");
    setRecibido("");
    setParteEfectivo("");
  }, [cuenta.id]);

  const plan = useMemo(() => planearCobro({
    modo, total: cuenta.total, recibido: leerPesos(recibido), parteEfectivo: leerPesos(parteEfectivo),
  }), [modo, cuenta.total, recibido, parteEfectivo]);

  const cobrable = cuenta.estado === "ENTREGADO";
  const faltaRecibido = modo !== "TARJETA" && recibido === "";
  const bloqueo = cajaCerrada ? "La caja está cerrada."
    : !cobrable ? "Esta mesa aún no ha sido servida; se cobra cuando el mesero la marque como servida."
    : faltaRecibido ? null : plan.problema;
  const efectivoACubrir = modo === "EFECTIVO" ? cuenta.total : leerPesos(parteEfectivo);

  return (
    <section className="cobro" aria-label={`Cobro de la mesa ${cuenta.numeroMesa}`}>
      <h2 className="cobro__titulo">Cobro · Mesa {cuenta.numeroMesa}</h2>

      <table className="tabla tabla--compacta">
        <thead>
          <tr><th>Cant.</th><th>Plato</th><th className="num">Precio</th><th className="num">Subtotal</th></tr>
        </thead>
        <tbody>
          {cuenta.detalles.map((d) => (
            <tr key={d.productoId}>
              <td>{d.cantidad}</td>
              <td>{d.nombreProducto}</td>
              <td className="num">{formatearPesos(d.precioUnitario)}</td>
              <td className="num">{formatearPesos(d.subtotal)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr><td colSpan={3}>Total (impuestos incluidos)</td><td className="num">{formatearPesos(cuenta.total)}</td></tr>
        </tfoot>
      </table>

      <fieldset className="cobro__metodo" disabled={!cobrable || cajaCerrada}>
        <legend>Medio de pago</legend>
        <div className="segmentado">
          {MODOS.map((m) => (
            <button key={m.valor} type="button" aria-pressed={modo === m.valor} onClick={() => setModo(m.valor)}>
              {m.nombre}
            </button>
          ))}
        </div>

        {modo === "MIXTO" && (
          <label className="campo-etiquetado">
            Parte que se paga en efectivo
            <input className="campo campo--dinero" inputMode="numeric" value={parteEfectivo}
                   placeholder="$ 0" onChange={(e) => setParteEfectivo(e.target.value)} />
          </label>
        )}

        {modo !== "TARJETA" && (
          <div className="campo-etiquetado">
            <label htmlFor="recibido">Efectivo recibido</label>
            <input id="recibido" className="campo campo--dinero" inputMode="numeric" value={recibido}
                   placeholder="$ 0" onChange={(e) => setRecibido(e.target.value)} />
            {efectivoACubrir > 0 && (
              <div className="sugerencias-billetes">
                {montosSugeridos(efectivoACubrir).map((monto) => (
                  <button key={monto} type="button" className="boton boton--chip"
                          onClick={() => setRecibido(String(monto))}>
                    {formatearPesos(monto)}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </fieldset>

      <dl className="cobro__resumen">
        {plan.enTarjeta > 0 && (<><dt>En tarjeta</dt><dd>{formatearPesos(plan.enTarjeta)}</dd></>)}
        {modo !== "TARJETA" && (<><dt>Cambio</dt><dd className="cobro__cambio">{formatearPesos(plan.cambio)}</dd></>)}
      </dl>

      <button
        type="button"
        className="boton boton--primario boton--grande"
        disabled={Boolean(bloqueo) || faltaRecibido || cobrando || !cobrable}
        onClick={() => onCobrar(plan.pagos)}
      >
        {cobrando ? "Procesando pago…" : "Registrar pago y generar factura"}
      </button>
      {bloqueo && <p className="cobro__problema" role="alert">{bloqueo}</p>}
    </section>
  );
}
