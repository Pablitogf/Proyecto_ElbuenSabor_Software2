import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { alExpirarSesion } from "../api/clienteHttp";
import type { Permiso, Usuario } from "../dominio/tipos";
import { borrarSesion, guardarSesion, leerSesion, type DatosSesion } from "./almacenSesion";

interface ValorSesion {
  usuario: Usuario | null;
  token: string | null;
  iniciar: (datos: DatosSesion) => void;
  salir: () => void;
  puede: (permiso: Permiso) => boolean;
}

const Contexto = createContext<ValorSesion | null>(null);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<DatosSesion | null>(leerSesion);

  const iniciar = useCallback((datos: DatosSesion) => {
    guardarSesion(datos);
    setSesion(datos);
  }, []);

  const salir = useCallback(() => {
    borrarSesion();
    setSesion(null);
  }, []);

  useEffect(() => alExpirarSesion(salir), [salir]);

  const valor = useMemo<ValorSesion>(() => ({
    usuario: sesion?.usuario ?? null,
    token: sesion?.token ?? null,
    iniciar,
    salir,
    puede: (permiso) => sesion?.usuario.permisos.includes(permiso) ?? false,
  }), [sesion, iniciar, salir]);

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion(): ValorSesion {
  const valor = useContext(Contexto);
  if (!valor) throw new Error("useSesion debe usarse dentro de <ProveedorSesion>");
  return valor;
}
