import { jornadaApi } from "../api/endpoints";
import type { Jornada } from "../dominio/tipos";
import { useCarga } from "./useCarga";

export function useJornada() {
  const { datos, recargar } = useCarga<Jornada | null>(jornadaApi.actual, null);
  return { jornada: datos, recargarJornada: recargar };
}
