import { useCallback, useState } from "react";
import { obtenerMenu } from "../../api/restauranteApi";
import type { Plato } from "../../dominio/tipos";

export function useMenu(alFallar: (mensaje: string) => void) {
  const [platos, setPlatos] = useState<Plato[]>([]);
  const [cargando, setCargando] = useState(false);

  /** Paso 2: cada consulta recalcula la disponibilidad según el inventario actual. */
  const recargarMenu = useCallback(async (): Promise<Plato[]> => {
    setCargando(true);
    try {
      const menu = await obtenerMenu();
      setPlatos(menu);
      return menu;
    } catch (error) {
      alFallar((error as Error).message);
      return [];
    } finally {
      setCargando(false);
    }
  }, [alFallar]);

  return { platos, cargando, recargarMenu };
}
