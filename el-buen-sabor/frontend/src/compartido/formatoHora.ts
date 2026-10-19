const FORMATO_HORA = new Intl.DateTimeFormat("es-CO", { hour: "numeric", minute: "2-digit" });
const FORMATO_FECHA_LARGA = new Intl.DateTimeFormat("es-CO", {
  weekday: "long", day: "numeric", month: "long",
});

export function aFecha(valor: string | Date): Date {
  return typeof valor === "string" ? new Date(valor) : valor;
}

export function formatearHora(valor: string | Date): string {
  return FORMATO_HORA.format(aFecha(valor));
}

export function formatearFechaLarga(valor: string | Date): string {
  const texto = FORMATO_FECHA_LARGA.format(aFecha(valor));
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

export function minutosTranscurridos(desde: string | Date, hasta: Date): number {
  const MILISEGUNDOS_POR_MINUTO = 60_000;
  return Math.max(0, Math.floor((hasta.getTime() - aFecha(desde).getTime()) / MILISEGUNDOS_POR_MINUTO));
}

/** "2026-10-19" en hora local (para inputs type=date y la API). */
export function fechaIso(fecha: Date): string {
  const dos = (n: number) => String(n).padStart(2, "0");
  return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}`;
}
