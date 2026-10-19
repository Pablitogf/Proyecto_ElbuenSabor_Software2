import { useState } from "react";
import { cocinaApi } from "../../api/endpoints";
import { Aviso } from "../../compartido/Aviso";
import { EncabezadoApp } from "../../compartido/EncabezadoApp";
import { formatearHora } from "../../compartido/formatoHora";
import { useAviso } from "../../compartido/useAviso";
import { useCarga } from "../../compartido/useCarga";
import { esEvento, useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import type { EventoTiempoReal, Pedido } from "../../dominio/tipos";
import { TarjetaComanda } from "./TarjetaComanda";
import { LEYENDA_URGENCIA } from "./urgencia";
import { useReloj } from "./useReloj";

/** IU-02: pantalla de cocina. Recibe comandas en tiempo real (RF-02) y despacha (F-05). */
export function PaginaCocina() {
  const ahora = useReloj();
  const { aviso, mostrarAviso, mostrarError } = useAviso();
  const comandas = useCarga<Pedido[]>(cocinaApi.comandas, []);
  const [idRecienLlegada, setIdRecienLlegada] = useState<number | null>(null);
  const [ocupada, setOcupada] = useState<number | null>(null);

  const conectado = useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (esEvento(evento, "PedidoRegistrado")) setIdRecienLlegada(evento.datos.pedido_id as number);
    if (esEvento(evento, "PedidoRegistrado", "EstadoDePedidoCambiado", "DatosReiniciados")) {
      void comandas.recargar();
    }
  });

  async function actuar(comanda: Pedido, accion: () => Promise<Pedido>, exito?: string) {
    setOcupada(comanda.id);
    try {
      const actualizada = await accion();
      comandas.setDatos((lista) => lista.map((c) => (c.id === actualizada.id ? actualizada : c)));
      if (exito) mostrarAviso("exito", exito);
    } catch (error) {
      mostrarError(error);
      void comandas.recargar();
    } finally {
      setOcupada(null);
    }
  }

  const activas = comandas.datos.filter((c) => c.estado !== "LISTO_PARA_SERVIR").length;

  return (
    <div className="cocina">
      <EncabezadoApp
        titulo="Comandas activas"
        variante="oscuro"
        centro={
          <span className="cocina__centro">
            <span className="cocina__contador">{activas} en preparación o en cola</span>
            <time className="cocina__reloj">{formatearHora(ahora)}</time>
          </span>
        }
        conectado={conectado}
      />

      {comandas.error && <p className="cocina__error">{comandas.error}</p>}

      {comandas.datos.length === 0 && !comandas.cargando ? (
        <p className="cocina__vacio">
          No hay comandas pendientes. Las nuevas aparecen aquí en cuanto el mesero confirma.
        </p>
      ) : (
        <main className="cocina__tablero">
          {comandas.datos.map((comanda) => (
            <TarjetaComanda
              key={comanda.id}
              comanda={comanda}
              ahora={ahora}
              recienLlegada={comanda.id === idRecienLlegada}
              ocupada={ocupada === comanda.id}
              onIniciar={(c) => actuar(c, () => cocinaApi.iniciar(c.id))}
              onMarcarPlato={(c, productoId, preparado) =>
                actuar(c, () => cocinaApi.marcarPlato(c.id, productoId, preparado))}
              onMarcarLista={(c) => actuar(c, () => cocinaApi.marcarListo(c.id),
                                           `Mesa ${c.numeroMesa} lista. Se avisó al mesero.`)}
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
      <Aviso aviso={aviso} />
    </div>
  );
}
