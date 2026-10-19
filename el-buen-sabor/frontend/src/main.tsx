import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { ProveedorSesion } from "./sesion/ContextoSesion";
import "./estilos/base.css";
import "./estilos/componentes.css";
import "./estilos/ingreso.css";
import "./estilos/mesero.css";
import "./estilos/cocina.css";
import "./estilos/caja.css";
import "./estilos/admin.css";

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <ProveedorSesion>
      <App />
    </ProveedorSesion>
  </StrictMode>,
);
