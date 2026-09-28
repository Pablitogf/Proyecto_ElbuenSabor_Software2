import { formatearPesos } from "../../../compartido/formatoMoneda";
import { puedeAgregarse, subtotal } from "../../../dominio/pedidoEnCurso";
import type { LineaPedido, Mesa, Plato } from "../../../dominio/tipos";

interface Props {
  mesa: Mesa | null;
  lineas: LineaPedido[];
  total: number;
  enviando: boolean;
  conectado: boolean;
  onAgregarPlato: (plato: Plato) => void;
  onQuitarPlato: (platoId: number) => void;
  onConfirmar: () => void;
}

function motivoParaNoConfirmar(props: Props): string | null {
  if (!props.mesa) return "Selecciona una mesa libre.";
  if (props.lineas.length === 0) return "Agrega al menos un plato.";
  if (!props.conectado) return "Sin conexión con cocina. Espera a que vuelva.";
  return null;
}

export function ResumenPedido(props: Props) {
  const { mesa, lineas, total, enviando, onAgregarPlato, onQuitarPlato, onConfirmar } = props;
  const motivoBloqueo = motivoParaNoConfirmar(props);

  return (
    <aside className="resumen" aria-label="Pedido actual">
      <h2 className="resumen__titulo">
        Pedido actual{mesa && <span className="resumen__mesa">Mesa {mesa.numero}</span>}
      </h2>

      {lineas.length === 0 ? (
        <p className="resumen__vacio">Los platos que agregues aparecen aquí.</p>
      ) : (
        <ul className="resumen__lineas">
          {lineas.map((linea) => (
            <li key={linea.plato.id} className="linea-pedido">
              <span className="linea-pedido__nombre">{linea.plato.nombre}</span>
              <span className="linea-pedido__subtotal">{formatearPesos(subtotal(linea))}</span>
              <div className="linea-pedido__cantidad">
                <button
                  type="button"
                  className="boton-cantidad"
                  aria-label={`Quitar una porción de ${linea.plato.nombre}`}
                  onClick={() => onQuitarPlato(linea.plato.id)}
                >
                  −
                </button>
                <span aria-label="Cantidad">{linea.cantidad}</span>
                <button
                  type="button"
                  className="boton-cantidad"
                  aria-label={`Agregar una porción de ${linea.plato.nombre}`}
                  disabled={!puedeAgregarse(lineas, linea.plato)}
                  onClick={() => onAgregarPlato(linea.plato)}
                >
                  +
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="resumen__pie">
        <p className="resumen__total">
          <span>Total</span>
          <strong>{formatearPesos(total)}</strong>
        </p>
        <button
          type="button"
          className="resumen__confirmar"
          disabled={motivoBloqueo !== null || enviando}
          onClick={onConfirmar}
        >
          {enviando ? "Enviando a cocina…" : "Confirmar pedido"}
        </button>
        {motivoBloqueo && <p className="resumen__motivo">{motivoBloqueo}</p>}
      </div>
    </aside>
  );
}
