import { leerSesion } from "../sesion/almacenSesion";

export class ErrorDeApi extends Error {
  constructor(
    mensaje: string,
    readonly codigoHttp: number,
    readonly motivos: string[] = [],
  ) {
    super(mensaje);
    this.name = "ErrorDeApi";
  }
}

const MENSAJE_SIN_SERVIDOR =
  "No hay conexión con el servidor. Revisa que el backend esté encendido.";
const SESION_EXPIRADA = 401;

let avisarSesionExpirada: () => void = () => {};

/** El proveedor de sesión se registra aquí para cerrar la sesión ante un 401. */
export function alExpirarSesion(callback: () => void): () => void {
  avisarSesionExpirada = callback;
  return () => {
    avisarSesionExpirada = () => {};
  };
}

type Metodo = "GET" | "POST" | "PUT";

export async function solicitar<T>(ruta: string, metodo: Metodo = "GET", cuerpo?: unknown): Promise<T> {
  const respuesta = await enviar(ruta, metodo, cuerpo);
  if (!respuesta.ok) throw await crearError(respuesta);
  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

/** Para descargas que no son JSON (por ejemplo, el XML de la factura). */
export async function obtenerTexto(ruta: string): Promise<string> {
  const respuesta = await enviar(ruta, "GET", undefined);
  if (!respuesta.ok) throw await crearError(respuesta);
  return respuesta.text();
}

export const obtener = <T>(ruta: string) => solicitar<T>(ruta);
export const publicar = <T>(ruta: string, cuerpo?: unknown) => solicitar<T>(ruta, "POST", cuerpo ?? {});
export const actualizar = <T>(ruta: string, cuerpo: unknown) => solicitar<T>(ruta, "PUT", cuerpo);

async function enviar(ruta: string, metodo: Metodo, cuerpo: unknown): Promise<Response> {
  const token = leerSesion()?.token;
  try {
    return await fetch(ruta, {
      method: metodo,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
  } catch {
    throw new ErrorDeApi(MENSAJE_SIN_SERVIDOR, 0);
  }
}

async function crearError(respuesta: Response): Promise<ErrorDeApi> {
  const cuerpo = await respuesta.json().catch(() => ({}));
  const mensaje = typeof cuerpo.detalle === "string" ? cuerpo.detalle : MENSAJE_SIN_SERVIDOR;
  if (respuesta.status === SESION_EXPIRADA && !respuesta.url.endsWith("/api/sesion")) {
    avisarSesionExpirada();
  }
  return new ErrorDeApi(mensaje, respuesta.status, cuerpo.motivos ?? []);
}

export function mensajeDe(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}
