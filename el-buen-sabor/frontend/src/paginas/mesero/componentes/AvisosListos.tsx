import { useEffect, useState } from "react";
import { minutosTranscurridos } from "../../../compartido/formatoHora";
import type { Pedido } from "../../../dominio/tipos";

const MINUTOS_PARA_INSISTIR = 5; // CU-01 6a: si el mesero no responde en 5 min, se insiste.

interface Props {
  pedidos: Pedido[];
  onServir: (pedido: Pedido) => void;
}

/** RF-04: barra de platos listos. Solo desaparece cuando el mesero marca "Servido". */
export function AvisosListos({ pedidos, onServir }: Props) {
  const [ahora, setAhora] = useState(() => new Date());
  useEffect(() => {
    const temporizador = window.setInterval(() => setAhora(new Date()), 30_000);
    return () => window.clearInterval(temporizador);
  }, []);

  if (pedidos.length === 0) return null;

  return (
    <section className="avisos-listos" aria-label="Platos listos para servir" aria-live="polite">
      {pedidos.map((pedido) => {
        const minutos = minutosTranscurridos(pedido.horaListo ?? pedido.fechaHora, ahora);
        const insistir = minutos >= MINUTOS_PARA_INSISTIR;
        return (
          <article key={pedido.id} className={`aviso-listo ${insistir ? "aviso-listo--urgente" : ""}`}>
            <span className="aviso-listo__icono" aria-hidden="true">🔔</span>
            <p>
              <strong>Mesa {pedido.numeroMesa} lista</strong>
              <span>{pedido.detalles.map((d) => `${d.cantidad}× ${d.nombreProducto}`).join(", ")}</span>
            </p>
            <span className="aviso-listo__tiempo">{minutos === 0 ? "ahora" : `hace ${minutos} min`}</span>
            <button type="button" className="boton boton--blanco" onClick={() => onServir(pedido)}>
              Marcar servido
            </button>
          </article>
        );
      })}
    </section>
  );
}
