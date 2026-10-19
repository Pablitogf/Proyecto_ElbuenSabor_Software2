import { formatearHora } from "../../../compartido/formatoHora";
import type { Mesa } from "../../../dominio/tipos";

interface Props {
  mesa: Mesa;
  ocupado: boolean;
  onConfirmarLlegada: (reservaId: number) => void;
}

/** CU-05 paso 7: el cliente con reserva llegó; el mesero lo confirma y toma el pedido. */
export function PanelReserva({ mesa, ocupado, onConfirmarLlegada }: Props) {
  const reserva = mesa.reservaQueAparta!;
  return (
    <aside className="resumen" aria-label={`Reserva de la mesa ${mesa.numero}`}>
      <h2 className="resumen__titulo">
        Mesa {mesa.numero}
        <span className="insignia insignia--reservada">Reservada</span>
      </h2>
      <div className="panel-reserva">
        <p className="panel-reserva__cliente">{reserva.nombreCliente}</p>
        <p>{reserva.personas} personas · {formatearHora(reserva.inicio)}</p>
        <p className="resumen__motivo">
          La mesa está apartada desde 30 minutos antes. Cuando el cliente llegue, confírmalo para tomarle el pedido.
          Si es otro cliente, ubícalo en una mesa libre.
        </p>
      </div>
      <div className="resumen__pie">
        <button type="button" className="boton boton--primario boton--grande" disabled={ocupado}
                onClick={() => onConfirmarLlegada(reserva.id)}>
          Confirmar llegada
        </button>
      </div>
    </aside>
  );
}
