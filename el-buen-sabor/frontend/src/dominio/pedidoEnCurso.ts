/**
 * Reglas del pedido que el mesero está armando en pantalla (antes de confirmar).
 * Son funciones puras: reciben las líneas actuales y devuelven unas nuevas.
 */
import type { LineaPedido, Plato } from "./tipos";

export function cantidadEnPedido(lineas: LineaPedido[], platoId: number): number {
  return lineas.find((linea) => linea.plato.id === platoId)?.cantidad ?? 0;
}

/** RF-01: no se pueden pedir platos sin stock ni más porciones de las que hay. */
export function puedeAgregarse(lineas: LineaPedido[], plato: Plato): boolean {
  return plato.disponible && cantidadEnPedido(lineas, plato.id) < plato.porcionesDisponibles;
}

export function agregarPlato(lineas: LineaPedido[], plato: Plato): LineaPedido[] {
  if (!puedeAgregarse(lineas, plato)) return lineas;

  const yaEstaEnElPedido = cantidadEnPedido(lineas, plato.id) > 0;
  if (!yaEstaEnElPedido) return [...lineas, { plato, cantidad: 1 }];

  return lineas.map((linea) =>
    linea.plato.id === plato.id ? { ...linea, cantidad: linea.cantidad + 1 } : linea,
  );
}

export function quitarPlato(lineas: LineaPedido[], platoId: number): LineaPedido[] {
  return lineas
    .map((linea) =>
      linea.plato.id === platoId ? { ...linea, cantidad: linea.cantidad - 1 } : linea,
    )
    .filter((linea) => linea.cantidad > 0);
}

export function subtotal(linea: LineaPedido): number {
  return linea.plato.precio * linea.cantidad;
}

/** RF-06: el total se recalcula cada vez que cambia el pedido. */
export function calcularTotal(lineas: LineaPedido[]): number {
  return lineas.reduce((total, linea) => total + subtotal(linea), 0);
}

/** Tras refrescar el menú, recorta cantidades que ya no alcanzan y quita platos agotados. */
export function ajustarAlMenuActual(lineas: LineaPedido[], menu: Plato[]): LineaPedido[] {
  return lineas.flatMap((linea) => {
    const platoActual = menu.find((plato) => plato.id === linea.plato.id);
    if (!platoActual?.disponible) return [];
    const cantidad = Math.min(linea.cantidad, platoActual.porcionesDisponibles);
    return [{ plato: platoActual, cantidad }];
  });
}
