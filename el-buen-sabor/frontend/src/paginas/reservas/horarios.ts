import { fechaIso } from "../../compartido/formatoHora";

/** Franjas que ofrece el formulario: de 11:00 a 20:00 cada 30 minutos (políticas de F-06). */
export const HORAS_DE_RESERVA: string[] = Array.from({ length: 19 }, (_, i) => {
  const minutos = 11 * 60 + i * 30;
  return `${String(Math.floor(minutos / 60)).padStart(2, "0")}:${minutos % 60 === 0 ? "00" : "30"}`;
});

const ANTICIPACION_MINIMA_MS = 15 * 60_000;

/** Para hoy solo se ofrecen las franjas que aún cumplen la anticipación mínima. */
export function franjasDisponibles(fecha: string, ahora: Date): string[] {
  return HORAS_DE_RESERVA.filter(
    (hora) => new Date(unirFechaHora(fecha, hora)).getTime() >= ahora.getTime() + ANTICIPACION_MINIMA_MS,
  );
}

/** La primera franja válida desde la fecha preferida (si hoy ya no hay, mañana a la 1 p. m.). */
export function propuestaInicial(fechaPreferida: string, ahora: Date): { fecha: string; hora: string } {
  const libres = franjasDisponibles(fechaPreferida, ahora);
  if (libres.length > 0) return { fecha: fechaPreferida, hora: libres.includes("13:00") ? "13:00" : libres[0] };
  const manana = new Date(ahora.getTime() + 24 * 60 * 60_000);
  return { fecha: fechaIso(manana), hora: "13:00" };
}

export function separarFechaHora(iso: string): { fecha: string; hora: string } {
  return { fecha: iso.slice(0, 10), hora: iso.slice(11, 16) };
}

export function unirFechaHora(fecha: string, hora: string): string {
  return `${fecha}T${hora}:00`;
}
