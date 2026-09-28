const FORMATO_HORA = new Intl.DateTimeFormat("es-CO", {
  hour: "numeric",
  minute: "2-digit",
});

export function formatearHora(fecha: Date): string {
  return FORMATO_HORA.format(fecha);
}

export function minutosTranscurridos(desde: Date, hasta: Date): number {
  const MILISEGUNDOS_POR_MINUTO = 60_000;
  return Math.max(0, Math.floor((hasta.getTime() - desde.getTime()) / MILISEGUNDOS_POR_MINUTO));
}
