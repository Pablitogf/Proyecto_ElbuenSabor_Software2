import { useCallback, useEffect, useRef, useState } from "react";
import { mensajeDe } from "../api/clienteHttp";

/** Carga un recurso, lo expone con estado de carga/error y permite recargarlo. */
export function useCarga<T>(cargar: () => Promise<T>, inicial: T) {
  const [datos, setDatos] = useState<T>(inicial);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const funcion = useRef(cargar);
  funcion.current = cargar;

  const recargar = useCallback(async () => {
    try {
      const resultado = await funcion.current();
      setDatos(resultado);
      setError(null);
      return resultado;
    } catch (causa) {
      setError(mensajeDe(causa));
      return undefined;
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    void recargar();
  }, [recargar]);

  return { datos, setDatos, cargando, error, recargar };
}
