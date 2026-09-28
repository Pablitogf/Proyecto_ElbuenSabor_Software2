import { formatearPesos } from "../../../compartido/formatoMoneda";
import type { Plato } from "../../../dominio/tipos";

const UMBRAL_POCAS_PORCIONES = 3;

interface Props {
  plato: Plato;
  cantidadEnPedido: number;
  sePuedeAgregar: boolean;
  onAgregar: (plato: Plato) => void;
}

function describirExistencias(plato: Plato, cantidadEnPedido: number): string | null {
  if (!plato.disponible) return "Sin stock";
  const restantes = plato.porcionesDisponibles - cantidadEnPedido;
  if (restantes <= 0) return "No quedan más porciones";
  if (plato.porcionesDisponibles > UMBRAL_POCAS_PORCIONES) return null;
  return restantes === 1 ? "Queda 1" : `Quedan ${restantes}`;
}

export function TarjetaPlato({ plato, cantidadEnPedido, sePuedeAgregar, onAgregar }: Props) {
  const existencias = describirExistencias(plato, cantidadEnPedido);

  return (
    <li className={`tarjeta-plato ${plato.disponible ? "" : "tarjeta-plato--agotado"}`}>
      <span className="tarjeta-plato__icono" aria-hidden="true">{plato.icono}</span>
      <div className="tarjeta-plato__texto">
        <h3 className="tarjeta-plato__nombre">{plato.nombre}</h3>
        <p className="tarjeta-plato__descripcion">{plato.descripcion}</p>
        <p className="tarjeta-plato__precio">
          {formatearPesos(plato.precio)}
          {existencias && <span className="tarjeta-plato__existencias">{existencias}</span>}
        </p>
      </div>
      <button
        type="button"
        className="boton-cantidad boton-cantidad--agregar"
        aria-label={`Agregar ${plato.nombre}`}
        disabled={!sePuedeAgregar}
        onClick={() => onAgregar(plato)}
      >
        +
      </button>
    </li>
  );
}
