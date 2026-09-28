import { useState } from "react";
import { RUTA_COCINA } from "../../../compartido/rutas";
import { IndicadorConexion } from "../../../compartido/IndicadorConexion";
import type { Mesa } from "../../../dominio/tipos";

interface Props {
  mesaSeleccionada: Mesa | null;
  conectado: boolean;
  onReiniciarDatos: () => void;
}

export function BarraSuperior({ mesaSeleccionada, conectado, onReiniciarDatos }: Props) {
  const [ajustesAbiertos, setAjustesAbiertos] = useState(false);

  function reiniciar() {
    setAjustesAbiertos(false);
    if (window.confirm("¿Reiniciar mesas, inventario y comandas a los datos iniciales?")) {
      onReiniciarDatos();
    }
  }

  return (
    <header className="barra-superior">
      <h1 className="barra-superior__marca">Restaurante El Buen Sabor</h1>
      <p className="barra-superior__mesa">
        {mesaSeleccionada ? `Mesa ${mesaSeleccionada.numero}` : "Sin mesa seleccionada"}
      </p>
      <div className="barra-superior__acciones">
        <IndicadorConexion conectado={conectado} />
        <button
          type="button"
          className="barra-superior__ajustes"
          aria-label="Ajustes"
          aria-expanded={ajustesAbiertos}
          onClick={() => setAjustesAbiertos((abierto) => !abierto)}
        >
          ⚙
        </button>
        {ajustesAbiertos && (
          <div className="menu-ajustes" role="menu">
            <a role="menuitem" href={RUTA_COCINA} target="_blank" rel="noreferrer">
              Abrir pantalla de cocina
            </a>
            <button role="menuitem" type="button" onClick={reiniciar}>
              Reiniciar datos de demostración
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
