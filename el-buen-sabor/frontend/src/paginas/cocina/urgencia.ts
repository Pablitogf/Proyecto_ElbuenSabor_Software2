/** Código de color de IU-02 según el tiempo que lleva la comanda en cola. */
export type NivelUrgencia = "a-tiempo" | "atencion" | "urgente";

const MINUTOS_PARA_ATENCION = 10;
const MINUTOS_PARA_URGENTE = 15;

export function nivelDeUrgencia(minutosEnCola: number): NivelUrgencia {
  if (minutosEnCola > MINUTOS_PARA_URGENTE) return "urgente";
  if (minutosEnCola >= MINUTOS_PARA_ATENCION) return "atencion";
  return "a-tiempo";
}

export const LEYENDA_URGENCIA: { nivel: NivelUrgencia; texto: string }[] = [
  { nivel: "a-tiempo", texto: "Menos de 10 min" },
  { nivel: "atencion", texto: "Entre 10 y 15 min" },
  { nivel: "urgente", texto: "Más de 15 min" },
];
