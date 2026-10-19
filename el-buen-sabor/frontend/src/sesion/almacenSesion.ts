/**
 * La sesión vive en sessionStorage: cada pestaña tiene su propio usuario, así se
 * pueden abrir la tablet del mesero y la pantalla de cocina lado a lado.
 */
import type { Usuario } from "../dominio/tipos";

const CLAVE = "el-buen-sabor.sesion";

export interface DatosSesion {
  token: string;
  usuario: Usuario;
}

export function leerSesion(): DatosSesion | null {
  try {
    const guardado = sessionStorage.getItem(CLAVE);
    return guardado ? (JSON.parse(guardado) as DatosSesion) : null;
  } catch {
    return null;
  }
}

export function guardarSesion(datos: DatosSesion): void {
  try {
    sessionStorage.setItem(CLAVE, JSON.stringify(datos));
  } catch {
    // Sin almacenamiento la sesión dura lo que dure la página abierta.
  }
}

export function borrarSesion(): void {
  try {
    sessionStorage.removeItem(CLAVE);
  } catch {
    // Nada que borrar.
  }
}
