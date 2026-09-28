import { useEffect, useRef, useState } from "react";
import type { EventoJson } from "../api/contratosApi";
import { aEvento } from "../api/traductores";
import type { EventoTiempoReal } from "../dominio/tipos";

const ESPERA_PARA_RECONECTAR_MS = 2000;

function direccionDelServidorDeEventos(): string {
  const protocolo = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocolo}://${window.location.host}/ws/eventos`;
}

/** Cierra la conexión aunque aún esté conectándose, sin disparar la reconexión. */
function cerrarSinAvisos(conexion: WebSocket) {
  conexion.onclose = null;
  if (conexion.readyState === WebSocket.CONNECTING) {
    conexion.onopen = () => conexion.close();
  } else {
    conexion.close();
  }
}

/**
 * Escucha los eventos del backend por WebSocket y se reconecta solo si se cae.
 * Devuelve si la pantalla está conectada (RF-02 exige conexión para enviar comandas).
 */
export function useEventosTiempoReal(alRecibirEvento: (evento: EventoTiempoReal) => void) {
  const [conectado, setConectado] = useState(false);
  const manejadorActual = useRef(alRecibirEvento);
  manejadorActual.current = alRecibirEvento;

  useEffect(() => {
    let conexion: WebSocket;
    let temporizador: number | undefined;
    let desmontado = false;

    function conectar() {
      conexion = new WebSocket(direccionDelServidorDeEventos());
      conexion.onopen = () => setConectado(true);
      conexion.onmessage = (mensaje) => {
        manejadorActual.current(aEvento(JSON.parse(mensaje.data) as EventoJson));
      };
      conexion.onclose = () => {
        setConectado(false);
        if (!desmontado) temporizador = window.setTimeout(conectar, ESPERA_PARA_RECONECTAR_MS);
      };
    }

    conectar();
    return () => {
      desmontado = true;
      window.clearTimeout(temporizador);
      cerrarSinAvisos(conexion);
    };
  }, []);

  return conectado;
}
