/** Enrutador mínimo basado en la URL (sin dependencias externas). */
import { useEffect, useState } from "react";
import type { Permiso, Rol } from "../dominio/tipos";

export const RUTAS = {
  ingreso: "/ingreso",
  mesero: "/mesero",
  cocina: "/cocina",
  caja: "/caja",
  administracion: "/admin",
  reservas: "/reservas",
} as const;

export type Ruta = (typeof RUTAS)[keyof typeof RUTAS];

/** RBAC en la interfaz: qué permiso necesita cada pantalla (el backend vuelve a validar). */
export const PERMISO_POR_RUTA: Record<Exclude<Ruta, "/ingreso">, Permiso> = {
  "/mesero": "REGISTRAR_PEDIDO",
  "/cocina": "VER_COMANDAS",
  "/caja": "COBRAR",
  "/admin": "ADMINISTRAR_SISTEMA",
  "/reservas": "VER_RESERVAS",
};

export const INICIO_POR_ROL: Record<Rol, Ruta> = {
  MESERO: RUTAS.mesero,
  COCINERO: RUTAS.cocina,
  CAJERO: RUTAS.caja,
  ADMINISTRADOR: RUTAS.administracion,
};

export function navegar(ruta: string, reemplazar = false): void {
  if (window.location.pathname === ruta) return;
  if (reemplazar) window.history.replaceState({}, "", ruta);
  else window.history.pushState({}, "", ruta);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

export function useRutaActual(): string {
  const [ruta, setRuta] = useState(window.location.pathname);
  useEffect(() => {
    const actualizar = () => setRuta(window.location.pathname);
    window.addEventListener("popstate", actualizar);
    return () => window.removeEventListener("popstate", actualizar);
  }, []);
  return ruta;
}
