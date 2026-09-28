import { useEffect, useState } from "react";

export function useReloj(intervaloMs = 1000): Date {
  const [ahora, setAhora] = useState(() => new Date());

  useEffect(() => {
    const temporizador = window.setInterval(() => setAhora(new Date()), intervaloMs);
    return () => window.clearInterval(temporizador);
  }, [intervaloMs]);

  return ahora;
}
