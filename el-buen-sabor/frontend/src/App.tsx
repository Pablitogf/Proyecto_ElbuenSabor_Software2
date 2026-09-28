import { RUTA_COCINA } from "./compartido/rutas";
import { PaginaCocina } from "./paginas/cocina/PaginaCocina";
import { PaginaMesero } from "./paginas/mesero/PaginaMesero";

/** Dos pantallas: la tablet del mesero (IU-01) en "/" y la cocina (IU-02) en "/cocina". */
export function App() {
  const esPantallaDeCocina = window.location.pathname.startsWith(RUTA_COCINA);
  return esPantallaDeCocina ? <PaginaCocina /> : <PaginaMesero />;
}
