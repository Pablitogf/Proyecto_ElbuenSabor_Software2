import type { EstadoMesa, Mesa } from "../../../dominio/tipos";

const ETIQUETA_POR_ESTADO: Record<EstadoMesa, string> = {
  DISPONIBLE: "Libre",
  OCUPADA: "Ocupada",
  RESERVADA: "Reservada",
};

interface Props {
  mesa: Mesa;
  seleccionada: boolean;
  onSeleccionar: (mesa: Mesa) => void;
}

export function TarjetaMesa({ mesa, seleccionada, onSeleccionar }: Props) {
  const variante = seleccionada ? "seleccionada" : mesa.estado.toLowerCase();
  const etiqueta = seleccionada ? "Tomando pedido" : ETIQUETA_POR_ESTADO[mesa.estado];

  return (
    <button
      type="button"
      className={`tarjeta-mesa tarjeta-mesa--${variante}`}
      aria-pressed={seleccionada}
      onClick={() => onSeleccionar(mesa)}
    >
      <span className="tarjeta-mesa__numero">Mesa {mesa.numero}</span>
      <span className="tarjeta-mesa__estado">{etiqueta}</span>
    </button>
  );
}
