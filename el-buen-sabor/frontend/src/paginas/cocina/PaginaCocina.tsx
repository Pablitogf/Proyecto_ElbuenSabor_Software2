import { useState } from "react";
import { formatearHora } from "../../compartido/formatoHora";
import { IndicadorConexion } from "../../compartido/IndicadorConexion";
import { useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import type { EventoTiempoReal } from "../../dominio/tipos";
import { TarjetaComanda } from "./TarjetaComanda";
import { LEYENDA_URGENCIA } from "./urgencia";
import { useComandas } from "./useComandas";
import { useReloj } from "./useReloj";

/** IU-02: pantalla de cocina. Recibe las comandas en tiempo real (RF-02). */
export function PaginaCocina() {
  const ahora = useReloj();
  const { comandas, error, recargarComandas, agregarComanda } = useComandas();
  const [idRecienLlegada, setIdRecienLlegada] = useState<number | null>(null);

  const conectado = useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (evento.tipo === "PEDIDO_REGISTRADO") {
      agregarComanda(evento.comanda);
      setIdRecienLlegada(evento.comanda.id);
    } else {
      setIdRecienLlegada(null);
      void recargarComandas();
    }
  });

  return (
    <div className="cocina">
      <header className="cocina__encabezado">
        <h1>Comandas activas</h1>
        <span className="cocina__contador">{comandas.length} en cola</span>
        <IndicadorConexion conectado={conectado} />
        <time className="cocina__reloj">{formatearHora(ahora)}</time>
      </header>

      {error && <p className="cocina__error">{error}</p>}

      {comandas.length === 0 ? (
        <p className="cocina__vacio">
          No hay comandas pendientes. Las nuevas aparecen aquí en cuanto el mesero confirma.
        </p>
      ) : (
        <main className="cocina__tablero">
          {comandas.map((comanda) => (
            <TarjetaComanda
              key={comanda.id}
              comanda={comanda}
              ahora={ahora}
              recienLlegada={comanda.id === idRecienLlegada}
            />
          ))}
        </main>
      )}

      <footer className="cocina__leyenda">
        {LEYENDA_URGENCIA.map(({ nivel, texto }) => (
          <span key={nivel} className="cocina__leyenda-item">
            <span className={`comanda__tiempo comanda__tiempo--${nivel}`} aria-hidden="true" />
            {texto}
          </span>
        ))}
      </footer>
    </div>
  );
}
