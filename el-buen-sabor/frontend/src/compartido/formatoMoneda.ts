const FORMATO_PESOS = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
const FORMATO_NUMERO = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 1 });

export function formatearPesos(valor: number): string {
  return FORMATO_PESOS.format(valor);
}

export function formatearCantidad(valor: number, unidad: string): string {
  return `${FORMATO_NUMERO.format(valor)} ${unidad}`;
}

/** Lee lo que el cajero escribe ("50.000", "50000", "$ 50.000") como número entero. */
export function leerPesos(texto: string): number {
  const digitos = texto.replace(/\D/g, "");
  return digitos ? Number(digitos) : 0;
}
