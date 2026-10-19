import { useState, type ReactNode } from "react";
import { ETIQUETA_ROL } from "../dominio/etiquetas";
import { useSesion } from "../sesion/ContextoSesion";
import { IndicadorConexion } from "./IndicadorConexion";
import { navegar, PERMISO_POR_RUTA, RUTAS } from "./navegacion";

interface Props {
  titulo: string;
  centro?: ReactNode;
  conectado: boolean;
  variante?: "claro" | "oscuro";
}

const PANTALLAS: { ruta: keyof typeof PERMISO_POR_RUTA; nombre: string }[] = [
  { ruta: RUTAS.mesero, nombre: "Tablet del mesero" },
  { ruta: RUTAS.cocina, nombre: "Pantalla de cocina" },
  { ruta: RUTAS.caja, nombre: "Módulo de caja" },
  { ruta: RUTAS.reservas, nombre: "Reservas" },
  { ruta: RUTAS.administracion, nombre: "Administración" },
];

/** Barra superior común: nombre del restaurante, contexto, conexión y menú de usuario. */
export function EncabezadoApp({ titulo, centro, conectado, variante = "claro" }: Props) {
  const { usuario, puede, salir } = useSesion();
  const [abierto, setAbierto] = useState(false);
  const pantallas = PANTALLAS.filter(
    (p) => puede(PERMISO_POR_RUTA[p.ruta]) && p.ruta !== window.location.pathname,
  );

  function ir(ruta: string) {
    setAbierto(false);
    navegar(ruta);
  }

  return (
    <header className={`encabezado encabezado--${variante}`}>
      <h1 className="encabezado__marca">{titulo}</h1>
      <div className="encabezado__centro">{centro}</div>
      <div className="encabezado__acciones">
        <IndicadorConexion conectado={conectado} />
        <button
          type="button"
          className="encabezado__usuario"
          aria-expanded={abierto}
          onClick={() => setAbierto((a) => !a)}
        >
          <span className="encabezado__avatar" aria-hidden="true">{usuario?.nombre.charAt(0)}</span>
          <span className="encabezado__nombre">
            {usuario?.nombre}
            <small>{usuario && ETIQUETA_ROL[usuario.rol]}</small>
          </span>
        </button>
        {abierto && (
          <div className="menu-usuario" role="menu">
            {pantallas.map((p) => (
              <button key={p.ruta} role="menuitem" type="button" onClick={() => ir(p.ruta)}>
                {p.nombre}
              </button>
            ))}
            <button role="menuitem" type="button" className="menu-usuario__salir" onClick={salir}>
              Cerrar sesión
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
