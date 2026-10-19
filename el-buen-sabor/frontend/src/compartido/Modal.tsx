import { useEffect, useRef, type ReactNode } from "react";

interface Props {
  titulo: string;
  onCerrar: () => void;
  children: ReactNode;
  ancho?: "normal" | "amplio";
}

/** Diálogo accesible: se cierra con Escape o tocando el fondo. */
export function Modal({ titulo, onCerrar, children, ancho = "normal" }: Props) {
  const dialogo = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const anterior = document.activeElement as HTMLElement | null;
    dialogo.current?.querySelector<HTMLElement>("input, select, textarea, button")?.focus();
    const alPresionar = (e: KeyboardEvent) => e.key === "Escape" && onCerrar();
    window.addEventListener("keydown", alPresionar);
    return () => {
      window.removeEventListener("keydown", alPresionar);
      anterior?.focus();
    };
  }, [onCerrar]);

  return (
    <div className="modal-fondo" onMouseDown={(e) => e.target === e.currentTarget && onCerrar()}>
      <div ref={dialogo} className={`modal modal--${ancho}`} role="dialog" aria-modal="true" aria-label={titulo}>
        <header className="modal__encabezado">
          <h2>{titulo}</h2>
          <button type="button" className="modal__cerrar" aria-label="Cerrar" onClick={onCerrar}>×</button>
        </header>
        {children}
      </div>
    </div>
  );
}
