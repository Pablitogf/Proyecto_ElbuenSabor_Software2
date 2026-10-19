import { useEffect, useRef, useState } from "react";
import type { EventoTiempoReal } from "../dominio/tipos";
import { useSesion } from "../sesion/ContextoSesion";

const ESPERA_PARA_RECONECTAR_MS = 2000;

function direccion(token: string): string {
  const protocolo = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocolo}://${window.location.host}/ws/eventos?token=${encodeURIComponent(token)}`;
}

/** Cierra la conexión aunque aún esté conectándose, sin disparar la reconexión. */
function cerrarSinAvisos(conexion: WebSocket) {
  conexion.onclose = null;
  if (conexion.readyState === WebSocket.CONNECTING) conexion.onopen = () => conexion.close();
  else conexion.close();
}

/**
 * Escucha los eventos del backend (patrón Observer del lado del cliente) y se
 * reconecta sola. Devuelve si la pantalla está en línea (RF-02).
 */
export function useEventosTiempoReal(alRecibir: (evento: EventoTiempoReal) => void): boolean {
  const { token } = useSesion();
  const [conectado, setConectado] = useState(false);
  const manejador = useRef(alRecibir);
  manejador.current = alRecibir;

  useEffect(() => {
    if (!token) return;
    let conexion: WebSocket;
    let temporizador: number | undefined;
    let activo = true;

    function conectar() {
      conexion = new WebSocket(direccion(token!));
      conexion.onopen = () => setConectado(true);
      conexion.onmessage = (mensaje) => manejador.current(JSON.parse(mensaje.data) as EventoTiempoReal);
      conexion.onclose = () => {
        setConectado(false);
        if (activo) temporizador = window.setTimeout(conectar, ESPERA_PARA_RECONECTAR_MS);
      };
    }

    conectar();
    return () => {
      activo = false;
      window.clearTimeout(temporizador);
      cerrarSinAvisos(conexion);
    };
  }, [token]);

  return conectado;
}

/** Ayuda para reaccionar solo a ciertos tipos de evento. */
export function esEvento(evento: EventoTiempoReal, ...tipos: string[]): boolean {
  return tipos.includes(evento.tipo);
}
