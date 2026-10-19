import { formatearHora, minutosTranscurridos } from "../../compartido/formatoHora";
import type { Pedido } from "../../dominio/tipos";
import { nivelDeUrgencia } from "./urgencia";

interface Props {
  comanda: Pedido;
  ahora: Date;
  recienLlegada: boolean;
  ocupada: boolean;
  onIniciar: (comanda: Pedido) => void;
  onMarcarPlato: (comanda: Pedido, productoId: number, preparado: boolean) => void;
  onMarcarLista: (comanda: Pedido) => void;
}

/** IU-02: una comanda. Los platos se tocan para marcarlos; el botón avanza el estado. */
export function TarjetaComanda(props: Props) {
  const { comanda, ahora, recienLlegada, ocupada, onIniciar, onMarcarPlato, onMarcarLista } = props;
  const minutos = minutosTranscurridos(comanda.fechaHora, ahora);
  const enPreparacion = comanda.estado === "EN_PREPARACION";
  const lista = comanda.estado === "LISTO_PARA_SERVIR";
  const pendientes = comanda.detalles.filter((d) => !d.preparado).length;

  return (
    <article className={["comanda", recienLlegada ? "comanda--nueva" : "", lista ? "comanda--lista" : ""].join(" ")}>
      <header className="comanda__encabezado">
        <h2 className="comanda__mesa">Mesa {comanda.numeroMesa}</h2>
        <span className={`comanda__tiempo comanda__tiempo--${nivelDeUrgencia(minutos)}`}>{minutos} min</span>
        <p className="comanda__hora">
          Pedido #{comanda.id} · recibido {formatearHora(comanda.fechaHora)}
        </p>
      </header>

      <ul className="comanda__platos">
        {comanda.detalles.map((detalle) => (
          <li key={detalle.productoId}>
            <button
              type="button"
              className="comanda__plato"
              disabled={!enPreparacion || ocupada}
              aria-pressed={detalle.preparado}
              onClick={() => onMarcarPlato(comanda, detalle.productoId, !detalle.preparado)}
            >
              <span className={`punto ${detalle.preparado ? "punto--verde" : "punto--ambar"}`} aria-hidden="true" />
              <span className="comanda__cantidad">{detalle.cantidad}×</span>
              {detalle.nombreProducto}
            </button>
          </li>
        ))}
      </ul>

      <footer className="comanda__pie">
        {comanda.estado === "REGISTRADO" && (
          <button type="button" className="boton boton--secundario boton--grande" disabled={ocupada}
                  onClick={() => onIniciar(comanda)}>
            Empezar preparación
          </button>
        )}
        {enPreparacion && (
          <>
            <button type="button" className="boton boton--primario boton--grande"
                    disabled={pendientes > 0 || ocupada} onClick={() => onMarcarLista(comanda)}>
              Marcar como listo
            </button>
            {pendientes > 0 && (
              <p className="comanda__ayuda">Toca cada plato cuando esté listo · faltan {pendientes}</p>
            )}
          </>
        )}
        {lista && (
          <button type="button" className="boton boton--grande comanda__notificado" disabled>
            Listo — mesero notificado
          </button>
        )}
      </footer>
    </article>
  );
}
