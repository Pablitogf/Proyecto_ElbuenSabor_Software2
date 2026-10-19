import type { Jornada } from "../dominio/tipos";

/** M-02: con la caja cerrada no se toman pedidos ni se cobra. */
export function AvisoCajaCerrada({ jornada }: { jornada: Jornada | null }) {
  if (!jornada || jornada.estado === "ABIERTA") return null;
  return (
    <p className="aviso-caja-cerrada" role="status">
      La caja está cerrada. No se pueden tomar pedidos ni cobrar hasta que administración abra una nueva jornada.
    </p>
  );
}
