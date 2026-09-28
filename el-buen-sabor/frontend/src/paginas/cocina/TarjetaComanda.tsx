import { formatearHora, minutosTranscurridos } from "../../compartido/formatoHora";
import type { Comanda } from "../../dominio/tipos";
import { nivelDeUrgencia } from "./urgencia";

interface Props {
  comanda: Comanda;
  ahora: Date;
  recienLlegada: boolean;
}

export function TarjetaComanda({ comanda, ahora, recienLlegada }: Props) {
  const minutosEnCola = minutosTranscurridos(comanda.fechaHora, ahora);

  return (
    <article className={`comanda ${recienLlegada ? "comanda--nueva" : ""}`}>
      <header className="comanda__encabezado">
        <h2 className="comanda__mesa">Mesa {comanda.numeroMesa}</h2>
        <span className={`comanda__tiempo comanda__tiempo--${nivelDeUrgencia(minutosEnCola)}`}>
          {minutosEnCola} min
        </span>
        <p className="comanda__hora">
          Pedido #{comanda.id}, recibido a las {formatearHora(comanda.fechaHora)}
        </p>
      </header>
      <ul className="comanda__platos">
        {comanda.detalles.map((detalle) => (
          <li key={detalle.productoId} className="comanda__plato">
            <span className="comanda__punto" aria-label="Pendiente de preparar" />
            <span className="comanda__cantidad">{detalle.cantidad}×</span>
            {detalle.nombreProducto}
          </li>
        ))}
      </ul>
    </article>
  );
}
