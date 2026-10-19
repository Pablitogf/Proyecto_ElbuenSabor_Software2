import { useEffect } from "react";
import { INICIO_POR_ROL, navegar, PERMISO_POR_RUTA, RUTAS, useRutaActual } from "./compartido/navegacion";
import { PaginaAdministracion } from "./paginas/admin/PaginaAdministracion";
import { PaginaCaja } from "./paginas/caja/PaginaCaja";
import { PaginaCocina } from "./paginas/cocina/PaginaCocina";
import { PaginaIngreso } from "./paginas/ingreso/PaginaIngreso";
import { PaginaMesero } from "./paginas/mesero/PaginaMesero";
import { PaginaReservas } from "./paginas/reservas/PaginaReservas";
import { useSesion } from "./sesion/ContextoSesion";

const PAGINAS: Record<keyof typeof PERMISO_POR_RUTA, () => JSX.Element> = {
  [RUTAS.mesero]: PaginaMesero,
  [RUTAS.cocina]: PaginaCocina,
  [RUTAS.caja]: PaginaCaja,
  [RUTAS.administracion]: PaginaAdministracion,
  [RUTAS.reservas]: PaginaReservas,
};

/** Cada rol entra a su pantalla; las rutas sin permiso redirigen al inicio del rol. */
export function App() {
  const ruta = useRutaActual();
  const { usuario, puede } = useSesion();
  const pagina = ruta in PAGINAS ? (ruta as keyof typeof PAGINAS) : null;
  const permitida = pagina !== null && puede(PERMISO_POR_RUTA[pagina]);

  useEffect(() => {
    if (!usuario) navegar(RUTAS.ingreso, true);
    else if (!permitida) navegar(INICIO_POR_ROL[usuario.rol], true);
  }, [usuario, permitida]);

  if (!usuario) return <PaginaIngreso />;
  if (!permitida) return null;
  const Pagina = PAGINAS[pagina];
  return <Pagina />;
}
