import { useEffect, useState } from "react";
import { Aviso } from "../../compartido/Aviso";
import { EncabezadoApp } from "../../compartido/EncabezadoApp";
import { useAviso } from "../../compartido/useAviso";
import { useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { AgendaReservas } from "../reservas/AgendaReservas";
import { SeccionInventario } from "./SeccionInventario";
import { SeccionResumen } from "./SeccionResumen";
import { SeccionSimulador } from "./SeccionSimulador";

type Seccion = "resumen" | "inventario" | "reservas" | "simulador";

const SECCIONES: { valor: Seccion; nombre: string; icono: string }[] = [
  { valor: "resumen", nombre: "Resumen y cierre", icono: "📊" },
  { valor: "inventario", nombre: "Inventario", icono: "📦" },
  { valor: "reservas", nombre: "Reservas", icono: "📅" },
  { valor: "simulador", nombre: "Simulador", icono: "🧪" },
];

function seccionInicial(): Seccion {
  const hash = window.location.hash.slice(1) as Seccion;
  return SECCIONES.some((s) => s.valor === hash) ? hash : "resumen";
}

/** IU-04: panel de administración. */
export function PaginaAdministracion() {
  const { aviso, mostrarAviso, mostrarError } = useAviso();
  const [seccion, setSeccion] = useState<Seccion>(seccionInicial);
  const conectado = useEventosTiempoReal(() => {});

  useEffect(() => {
    const alCambiarHash = () => setSeccion(seccionInicial());
    window.addEventListener("hashchange", alCambiarHash);
    return () => window.removeEventListener("hashchange", alCambiarHash);
  }, []);

  function ir(nueva: Seccion) {
    setSeccion(nueva);
    window.history.replaceState({}, "", `#${nueva}`);
  }

  const comunes = { onAviso: mostrarAviso, onError: mostrarError };

  return (
    <div className="admin">
      <EncabezadoApp titulo="El Buen Sabor · Administración" conectado={conectado} />
      <nav className="admin__menu" aria-label="Módulos">
        {SECCIONES.map((s) => (
          <button key={s.valor} type="button" aria-current={seccion === s.valor ? "page" : undefined}
                  onClick={() => ir(s.valor)}>
            <span aria-hidden="true">{s.icono}</span>{s.nombre}
          </button>
        ))}
      </nav>
      <main className="admin__contenido">
        {seccion === "resumen" && <SeccionResumen {...comunes} onIrAInventario={() => ir("inventario")} />}
        {seccion === "inventario" && <SeccionInventario {...comunes} />}
        {seccion === "reservas" && <AgendaReservas {...comunes} />}
        {seccion === "simulador" && <SeccionSimulador {...comunes} />}
      </main>
      <Aviso aviso={aviso} />
    </div>
  );
}
