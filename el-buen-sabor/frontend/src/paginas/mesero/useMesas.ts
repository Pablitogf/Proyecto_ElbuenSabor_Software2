import { useCallback, useEffect, useState } from "react";
import { obtenerMesas } from "../../api/restauranteApi";
import type { Mesa } from "../../dominio/tipos";

export function useMesas(alFallar: (mensaje: string) => void) {
  const [mesas, setMesas] = useState<Mesa[]>([]);

  const recargarMesas = useCallback(async () => {
    try {
      setMesas(await obtenerMesas());
    } catch (error) {
      alFallar((error as Error).message);
    }
  }, [alFallar]);

  const actualizarMesa = useCallback((mesaActualizada: Mesa) => {
    setMesas((actuales) =>
      actuales.map((mesa) => (mesa.numero === mesaActualizada.numero ? mesaActualizada : mesa)),
    );
  }, []);

  useEffect(() => {
    void recargarMesas();
  }, [recargarMesas]);

  return { mesas, recargarMesas, actualizarMesa };
}
