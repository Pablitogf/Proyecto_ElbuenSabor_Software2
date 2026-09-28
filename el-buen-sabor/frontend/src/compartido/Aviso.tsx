import type { Aviso as DatosAviso } from "./useAviso";

export function Aviso({ aviso }: { aviso: DatosAviso | null }) {
  return (
    <div className="aviso-contenedor" role="status" aria-live="polite">
      {aviso && (
        <p key={aviso.id} className={`aviso aviso--${aviso.tipo}`}>
          {aviso.mensaje}
        </p>
      )}
    </div>
  );
}
