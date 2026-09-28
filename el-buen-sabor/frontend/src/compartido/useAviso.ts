import { useCallback, useEffect, useState } from "react";

export type TipoAviso = "exito" | "error";

export interface Aviso {
  id: number;
  tipo: TipoAviso;
  mensaje: string;
}

const DURACION_AVISO_MS = 4000;

export function useAviso() {
  const [aviso, setAviso] = useState<Aviso | null>(null);

  const mostrarAviso = useCallback((tipo: TipoAviso, mensaje: string) => {
    setAviso({ id: Date.now(), tipo, mensaje });
  }, []);

  useEffect(() => {
    if (!aviso) return;
    const temporizador = window.setTimeout(() => setAviso(null), DURACION_AVISO_MS);
    return () => window.clearTimeout(temporizador);
  }, [aviso]);

  return { aviso, mostrarAviso };
}
