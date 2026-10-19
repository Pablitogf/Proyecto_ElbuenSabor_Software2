import { useEffect, useState } from "react";
import { reservasApi, salonApi, type DatosReserva } from "../../api/endpoints";
import { fechaIso, formatearFechaLarga, formatearHora } from "../../compartido/formatoHora";
import { Modal } from "../../compartido/Modal";
import { useCarga } from "../../compartido/useCarga";
import { esEvento, useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { ETIQUETA_ESTADO_RESERVA } from "../../dominio/etiquetas";
import type { EventoTiempoReal, Mesa, Reserva } from "../../dominio/tipos";
import { useSesion } from "../../sesion/ContextoSesion";
import { FormularioReserva } from "./FormularioReserva";

interface Props {
  onAviso: (tipo: "exito" | "error", mensaje: string) => void;
  onError: (error: unknown) => void;
}

type Edicion = { tipo: "nueva" } | { tipo: "reprogramar"; reserva: Reserva } | null;

/** F-06 · agenda del día: registrar, consultar, reprogramar, llegada, cancelación y no-show. */
export function AgendaReservas({ onAviso, onError }: Props) {
  const { puede } = useSesion();
  const [fecha, setFecha] = useState(() => fechaIso(new Date()));
  const reservas = useCarga<Reserva[]>(() => reservasApi.delDia(fecha), []);
  const mesas = useCarga<Mesa[]>(salonApi.mesas, []);
  const [edicion, setEdicion] = useState<Edicion>(null);
  const [enviando, setEnviando] = useState(false);
  const gestiona = puede("GESTIONAR_RESERVAS");

  useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (esEvento(evento, "ReservasActualizadas", "DatosReiniciados")) void reservas.recargar();
  });

  const { recargar } = reservas;
  useEffect(() => {
    void recargar();
  }, [fecha, recargar]);

  async function ejecutar(accion: () => Promise<Reserva>, exito: (r: Reserva) => string) {
    setEnviando(true);
    try {
      const reserva = await accion();
      onAviso("exito", exito(reserva));
      setEdicion(null);
      await reservas.recargar();
    } catch (error) {
      onError(error);
    } finally {
      setEnviando(false);
    }
  }

  const guardar = (datos: DatosReserva) => {
    if (edicion?.tipo === "reprogramar") {
      void ejecutar(() => reservasApi.reprogramar(edicion.reserva.id, datos.inicio, datos.personas, datos.numeroMesa),
        (r) => `Reserva movida a las ${formatearHora(r.inicio)}, mesa ${r.numeroMesa}.`);
    } else {
      void ejecutar(() => reservasApi.crear(datos),
        (r) => `Reserva de ${r.nombreCliente} registrada en la mesa ${r.numeroMesa}.`);
    }
  };

  const pendientes = reservas.datos.filter((r) => r.estado === "PENDIENTE").length;

  return (
    <section className="agenda">
      <header className="agenda__encabezado">
        <div>
          <h2>{formatearFechaLarga(`${fecha}T12:00:00`)}</h2>
          <p className="agenda__resumen">
            {reservas.datos.length === 1 ? "1 reserva" : `${reservas.datos.length} reservas`} · {pendientes} por llegar
          </p>
        </div>
        <input className="campo" type="date" value={fecha} aria-label="Fecha"
               onChange={(e) => e.target.value && setFecha(e.target.value)} />
        {gestiona && (
          <button type="button" className="boton boton--primario" onClick={() => setEdicion({ tipo: "nueva" })}>
            Nueva reserva
          </button>
        )}
      </header>

      {reservas.datos.length === 0 && !reservas.cargando ? (
        <p className="agenda__vacia">No hay reservas para este día.</p>
      ) : (
        <ul className="agenda__lista">
          {reservas.datos.map((r) => (
            <li key={r.id} className={`reserva reserva--${r.estado.toLowerCase()} ${r.vencida ? "reserva--vencida" : ""}`}>
              <div className="reserva__hora">
                <strong>{formatearHora(r.inicio)}</strong>
                <span>hasta {formatearHora(r.fin)}</span>
              </div>
              <div className="reserva__cliente">
                <strong>{r.nombreCliente}</strong>
                <span>{r.personas} personas · Mesa {r.numeroMesa} · {r.telefono}</span>
                {r.notas && <em>{r.notas}</em>}
              </div>
              <span className={`insignia insignia--reserva-${r.estado.toLowerCase()}`}>
                {r.vencida ? "Pasó la tolerancia" : ETIQUETA_ESTADO_RESERVA[r.estado]}
              </span>
              {gestiona && r.estado === "PENDIENTE" && (
                <div className="reserva__acciones">
                  {r.puedeConfirmarse && (
                    <button type="button" className="boton boton--primario boton--chico" disabled={enviando}
                            onClick={() => ejecutar(() => reservasApi.confirmarLlegada(r.id),
                              () => `Llegada de ${r.nombreCliente} confirmada. Mesa ${r.numeroMesa} lista.`)}>
                      Llegó
                    </button>
                  )}
                  {r.vencida && (
                    <button type="button" className="boton boton--secundario boton--chico" disabled={enviando}
                            onClick={() => ejecutar(() => reservasApi.noAsistio(r.id),
                              () => `Mesa ${r.numeroMesa} liberada.`)}>
                      No asistió
                    </button>
                  )}
                  {!r.vencida && (
                    <button type="button" className="boton boton--secundario boton--chico"
                            onClick={() => setEdicion({ tipo: "reprogramar", reserva: r })}>
                      Reprogramar
                    </button>
                  )}
                  <button type="button" className="boton boton--peligro-suave boton--chico" disabled={enviando}
                          onClick={() => window.confirm(`¿Cancelar la reserva de ${r.nombreCliente}?`)
                            && ejecutar(() => reservasApi.cancelar(r.id), () => "Reserva cancelada.")}>
                    Cancelar
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {edicion && (
        <Modal titulo={edicion.tipo === "nueva" ? "Nueva reserva" : `Reprogramar a ${edicion.reserva.nombreCliente}`}
               onCerrar={() => setEdicion(null)}>
          <FormularioReserva
            mesas={mesas.datos}
            fechaInicial={fecha}
            reserva={edicion.tipo === "reprogramar" ? edicion.reserva : undefined}
            enviando={enviando}
            onGuardar={guardar}
            onCancelar={() => setEdicion(null)}
          />
        </Modal>
      )}
    </section>
  );
}
