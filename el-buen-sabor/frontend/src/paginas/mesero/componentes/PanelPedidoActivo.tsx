import { useEffect, useState } from "react";
import { salonApi } from "../../../api/endpoints";
import { formatearHora } from "../../../compartido/formatoHora";
import { formatearPesos } from "../../../compartido/formatoMoneda";
import { ETIQUETA_ESTADO_PEDIDO } from "../../../dominio/etiquetas";
import type { Mesa, Pedido } from "../../../dominio/tipos";

interface Props {
  mesa: Mesa;
  ocupado: boolean;
  onServir: (pedido: Pedido) => void;
  onCancelar: (pedido: Pedido, motivo: string) => void;
}

/** Al tocar una mesa ocupada el mesero ve su pedido y lo que puede hacer con él. */
export function PanelPedidoActivo({ mesa, ocupado, onServir, onCancelar }: Props) {
  const [pedido, setPedido] = useState<Pedido | null>(null);
  const [cancelando, setCancelando] = useState(false);
  const [motivo, setMotivo] = useState("");
  const versionDelPedido = `${mesa.pedido?.id}-${mesa.pedido?.estado}`;

  useEffect(() => {
    let vigente = true;
    salonApi.pedidoDeMesa(mesa.numero).then((p) => vigente && setPedido(p)).catch(() => {});
    setCancelando(false);
    return () => {
      vigente = false;
    };
  }, [mesa.numero, versionDelPedido]);

  if (!pedido) {
    return <aside className="resumen"><p className="resumen__vacio">Consultando el pedido…</p></aside>;
  }

  return (
    <aside className="resumen" aria-label={`Pedido de la mesa ${mesa.numero}`}>
      <h2 className="resumen__titulo">
        Pedido #{pedido.id}
        <span className={`insignia insignia--${pedido.estado.toLowerCase()}`}>
          {ETIQUETA_ESTADO_PEDIDO[pedido.estado]}
        </span>
      </h2>
      <p className="resumen__meta">Mesa {mesa.numero} · tomado a las {formatearHora(pedido.fechaHora)}</p>
      <ul className="resumen__lineas">
        {pedido.detalles.map((d) => (
          <li key={d.productoId} className="linea-pedido linea-pedido--lectura">
            <span className="linea-pedido__nombre">
              <span className={`punto ${d.preparado ? "punto--verde" : "punto--ambar"}`}
                    aria-label={d.preparado ? "Preparado" : "Pendiente"} />
              {d.cantidad}× {d.nombreProducto}
            </span>
            <span className="linea-pedido__subtotal">{formatearPesos(d.subtotal)}</span>
          </li>
        ))}
      </ul>
      <div className="resumen__pie">
        <p className="resumen__total"><span>Total</span><strong>{formatearPesos(pedido.total)}</strong></p>

        {pedido.estado === "LISTO_PARA_SERVIR" && (
          <button type="button" className="boton boton--primario boton--grande" disabled={ocupado}
                  onClick={() => onServir(pedido)}>
            Marcar servido
          </button>
        )}
        {pedido.estado === "ENTREGADO" && (
          <p className="resumen__motivo">Servido. La cuenta ya aparece en caja para cobrarla.</p>
        )}
        {(pedido.estado === "EN_PREPARACION") && (
          <p className="resumen__motivo">Cocina ya lo está preparando; te avisamos cuando esté listo.</p>
        )}
        {pedido.estado === "REGISTRADO" && !cancelando && (
          <>
            <p className="resumen__motivo">En cola de cocina. Aún se puede cancelar si hubo un error.</p>
            <button type="button" className="boton boton--peligro-suave" onClick={() => setCancelando(true)}>
              Cancelar pedido
            </button>
          </>
        )}
        {pedido.estado === "REGISTRADO" && cancelando && (
          <form className="formulario-cancelacion"
                onSubmit={(e) => { e.preventDefault(); onCancelar(pedido, motivo); }}>
            <label htmlFor="motivo">¿Por qué se cancela?</label>
            <input id="motivo" className="campo" value={motivo} placeholder="Ej: error de digitación"
                   onChange={(e) => setMotivo(e.target.value)} autoFocus />
            <div className="fila-botones">
              <button type="button" className="boton boton--secundario" onClick={() => setCancelando(false)}>
                Volver
              </button>
              <button className="boton boton--peligro" disabled={ocupado}>Cancelar pedido</button>
            </div>
          </form>
        )}
      </div>
    </aside>
  );
}
