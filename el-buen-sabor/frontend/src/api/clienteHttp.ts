export class ErrorDeApi extends Error {
  constructor(
    mensaje: string,
    readonly codigoHttp: number,
  ) {
    super(mensaje);
    this.name = "ErrorDeApi";
  }
}

const MENSAJE_SIN_SERVIDOR =
  "No hay conexión con el servidor. Revisa que el backend esté encendido.";

export async function solicitar<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const respuesta = await enviar(ruta, opciones);
  if (!respuesta.ok) throw await crearError(respuesta);
  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

async function enviar(ruta: string, opciones: RequestInit): Promise<Response> {
  try {
    return await fetch(ruta, {
      ...opciones,
      headers: { "Content-Type": "application/json", ...opciones.headers },
    });
  } catch {
    throw new ErrorDeApi(MENSAJE_SIN_SERVIDOR, 0);
  }
}

async function crearError(respuesta: Response): Promise<ErrorDeApi> {
  const cuerpo = await respuesta.json().catch(() => ({}));
  const mensaje = typeof cuerpo.detalle === "string" ? cuerpo.detalle : MENSAJE_SIN_SERVIDOR;
  return new ErrorDeApi(mensaje, respuesta.status);
}
