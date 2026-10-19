import { Aviso } from "../../compartido/Aviso";
import { EncabezadoApp } from "../../compartido/EncabezadoApp";
import { useAviso } from "../../compartido/useAviso";
import { useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { AgendaReservas } from "./AgendaReservas";

/** Reservas desde la tablet del mesero (F-06: "como administrador y mesero…"). */
export function PaginaReservas() {
  const { aviso, mostrarAviso, mostrarError } = useAviso();
  const conectado = useEventosTiempoReal(() => {});
  return (
    <div className="pagina-simple">
      <EncabezadoApp titulo="Reservas" conectado={conectado} />
      <main className="pagina-simple__contenido">
        <AgendaReservas onAviso={mostrarAviso} onError={mostrarError} />
      </main>
      <Aviso aviso={aviso} />
    </div>
  );
}
