import { formatearHora } from "../../../compartido/formatoHora";
import type { Mesa } from "../../../dominio/tipos";

interface Props {
  mesa: Mesa;
  seleccionada: boolean;
  onSeleccionar: (mesa: Mesa) => void;
}

function describir(mesa: Mesa): string {
  if (mesa.estado === "RESERVADA" && mesa.reservaQueAparta) {
    return `Reservada ${formatearHora(mesa.reservaQueAparta.inicio)}`;
  }
  if (mesa.estado === "DISPONIBLE") return "Libre";
  switch (mesa.pedido?.estado) {
    case "REGISTRADO":
    case "EN_PREPARACION":
      return "En cocina";
    case "LISTO_PARA_SERVIR":
      return "¡Listo para servir!";
    case "ENTREGADO":
      return "Servido · por cobrar";
    default:
      return "Ocupada";
  }
}

export function TarjetaMesa({ mesa, seleccionada, onSeleccionar }: Props) {
  const listo = mesa.pedido?.estado === "LISTO_PARA_SERVIR";
  const clases = [
    "tarjeta-mesa",
    `tarjeta-mesa--${mesa.estado.toLowerCase()}`,
    seleccionada ? "tarjeta-mesa--seleccionada" : "",
    listo ? "tarjeta-mesa--lista" : "",
  ].join(" ");

  return (
    <button type="button" className={clases} aria-pressed={seleccionada} onClick={() => onSeleccionar(mesa)}>
      <span className="tarjeta-mesa__numero">Mesa {mesa.numero}</span>
      <span className="tarjeta-mesa__estado">{describir(mesa)}</span>
      <span className="tarjeta-mesa__detalle">
        {mesa.capacidad} puestos
        {mesa.estado === "DISPONIBLE" && mesa.proximaReserva &&
          ` · reserva ${formatearHora(mesa.proximaReserva.inicio)}`}
      </span>
    </button>
  );
}
