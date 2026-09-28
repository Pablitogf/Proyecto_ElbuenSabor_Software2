import { useCallback, useEffect, useState } from "react";
import { obtenerComandasActivas } from "../../api/restauranteApi";
import type { Comanda } from "../../dominio/tipos";

export function useComandas() {
  const [comandas, setComandas] = useState<Comanda[]>([]);
  const [error, setError] = useState<string | null>(null);

  const recargarComandas = useCallback(async () => {
    try {
      setComandas(await obtenerComandasActivas());
      setError(null);
    } catch (causa) {
      setError((causa as Error).message);
    }
  }, []);

  /** Paso 5: la comanda nueva se agrega al final (orden de llegada). */
  const agregarComanda = useCallback((nueva: Comanda) => {
    setComandas((actuales) =>
      actuales.some((comanda) => comanda.id === nueva.id) ? actuales : [...actuales, nueva],
    );
  }, []);

  useEffect(() => {
    void recargarComandas();
  }, [recargarComandas]);

  return { comandas, error, recargarComandas, agregarComanda };
}
