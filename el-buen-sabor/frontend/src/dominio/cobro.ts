/**
 * Arma el desglose del pago a partir de lo que el cajero digita (CU-02, 4a).
 * Funciones puras: la interfaz las usa para mostrar el cambio en vivo y el
 * backend vuelve a validar todo antes de cobrar.
 */
import type { LineaPagoSolicitud } from "./tipos";

export type ModoPago = "EFECTIVO" | "TARJETA" | "MIXTO";

export interface EntradaCobro {
  modo: ModoPago;
  total: number;
  recibido: number;      // Efectivo que entregó el cliente.
  parteEfectivo: number; // Solo en MIXTO: cuánto de la cuenta se paga en efectivo.
}

export interface PlanDeCobro {
  pagos: LineaPagoSolicitud[];
  enTarjeta: number;
  cambio: number;
  problema: string | null;
}

const pesos = (valor: number) => `$${valor.toLocaleString("es-CO")}`;

export function planearCobro({ modo, total, recibido, parteEfectivo }: EntradaCobro): PlanDeCobro {
  if (modo === "TARJETA") {
    return { pagos: [{ metodo: "TARJETA", monto: total }], enTarjeta: total, cambio: 0, problema: null };
  }
  const efectivo = modo === "EFECTIVO" ? total : parteEfectivo;
  const enTarjeta = total - efectivo;
  const pagos: LineaPagoSolicitud[] = [{ metodo: "EFECTIVO", monto: efectivo, montoRecibido: recibido }];
  if (enTarjeta > 0) pagos.push({ metodo: "TARJETA", monto: enTarjeta });

  return { pagos, enTarjeta, cambio: Math.max(0, recibido - efectivo), problema: validar(modo, total, efectivo, recibido) };
}

function validar(modo: ModoPago, total: number, efectivo: number, recibido: number): string | null {
  if (modo === "MIXTO" && (efectivo <= 0 || efectivo >= total)) {
    return "En pago mixto, la parte en efectivo debe ser mayor que cero y menor que el total.";
  }
  if (recibido < efectivo) return `Faltan ${pesos(efectivo - recibido)} en efectivo.`;
  return null;
}

/** Billetes sugeridos para cobrar rápido: el valor exacto y los redondeos siguientes. */
export function montosSugeridos(valor: number): number[] {
  const opciones = [valor, ...[10_000, 20_000, 50_000, 100_000].map((b) => Math.ceil(valor / b) * b)];
  return [...new Set(opciones)].filter((m) => m >= valor).slice(0, 4);
}
