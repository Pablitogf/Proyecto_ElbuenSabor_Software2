import { useCallback, useState } from "react";
import { salonApi } from "../../api/endpoints";
import type { Plato } from "../../dominio/tipos";

export function useMenu(alFallar: (error: unknown) => void) {
  const [platos, setPlatos] = useState<Plato[]>([]);
  const [cargando, setCargando] = useState(false);

  /** Paso 2: cada consulta recalcula la disponibilidad según el inventario actual. */
  const recargarMenu = useCallback(async (): Promise<Plato[]> => {
    setCargando(true);
    try {
      const menu = await salonApi.menu();
      setPlatos(menu);
      return menu;
    } catch (error) {
      alFallar(error);
      return [];
    } finally {
      setCargando(false);
    }
  }, [alFallar]);

  return { platos, cargando, recargarMenu };
}
