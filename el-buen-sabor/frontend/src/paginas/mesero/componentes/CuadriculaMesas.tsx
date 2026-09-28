import type { Mesa } from "../../../dominio/tipos";
import { TarjetaMesa } from "./TarjetaMesa";

interface Props {
  mesas: Mesa[];
  numeroMesaSeleccionada: number | null;
  onSeleccionarMesa: (mesa: Mesa) => void;
}

export function CuadriculaMesas({ mesas, numeroMesaSeleccionada, onSeleccionarMesa }: Props) {
  return (
    <section className="mesas" aria-label="Mesas del salón">
      {mesas.map((mesa) => (
        <TarjetaMesa
          key={mesa.numero}
          mesa={mesa}
          seleccionada={mesa.numero === numeroMesaSeleccionada}
          onSeleccionar={onSeleccionarMesa}
        />
      ))}
    </section>
  );
}
