import { cantidadEnPedido, puedeAgregarse } from "../../../dominio/pedidoEnCurso";
import type { Categoria, LineaPedido, Plato } from "../../../dominio/tipos";
import { TarjetaPlato } from "./TarjetaPlato";

interface Props {
  platos: Plato[];
  categoria: Categoria;
  lineas: LineaPedido[];
  hayMesaSeleccionada: boolean;
  cargando: boolean;
  onAgregarPlato: (plato: Plato) => void;
}

/** Los platos disponibles van primero; los que no tienen stock quedan al final, bloqueados. */
function ordenarPorDisponibilidad(platos: Plato[]): Plato[] {
  return [...platos].sort((a, b) => Number(b.disponible) - Number(a.disponible));
}

export function ListaPlatos(props: Props) {
  const { platos, categoria, lineas, hayMesaSeleccionada, cargando, onAgregarPlato } = props;

  if (!hayMesaSeleccionada) {
    return (
      <p className="platos__indicacion">
        Toca una mesa libre para ver el menú y empezar su pedido.
      </p>
    );
  }
  if (cargando && platos.length === 0) {
    return <p className="platos__indicacion">Consultando el inventario…</p>;
  }

  const platosDeLaCategoria = ordenarPorDisponibilidad(
    platos.filter((plato) => plato.categoria === categoria),
  );

  return (
    <ul className="platos" aria-label="Platos de la categoría">
      {platosDeLaCategoria.map((plato) => (
        <TarjetaPlato
          key={plato.id}
          plato={plato}
          cantidadEnPedido={cantidadEnPedido(lineas, plato.id)}
          sePuedeAgregar={puedeAgregarse(lineas, plato)}
          onAgregar={onAgregarPlato}
        />
      ))}
    </ul>
  );
}
