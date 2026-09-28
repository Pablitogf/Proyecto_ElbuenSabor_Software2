import { useCallback, useMemo, useState } from "react";
import {
  agregarPlato,
  ajustarAlMenuActual,
  calcularTotal,
  quitarPlato,
} from "../../dominio/pedidoEnCurso";
import type { LineaPedido, Plato } from "../../dominio/tipos";

export function usePedidoEnCurso() {
  const [lineas, setLineas] = useState<LineaPedido[]>([]);

  const agregar = useCallback((plato: Plato) => setLineas((l) => agregarPlato(l, plato)), []);
  const quitar = useCallback((platoId: number) => setLineas((l) => quitarPlato(l, platoId)), []);
  const vaciar = useCallback(() => setLineas([]), []);
  const ajustarAlMenu = useCallback(
    (menu: Plato[]) => setLineas((l) => ajustarAlMenuActual(l, menu)),
    [],
  );
  const total = useMemo(() => calcularTotal(lineas), [lineas]);

  return { lineas, total, agregar, quitar, vaciar, ajustarAlMenu };
}
