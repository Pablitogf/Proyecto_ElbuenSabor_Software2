/** Un solo archivo con todas las rutas de la API, agrupadas por módulo. */
import type {
  Factura, Ingrediente, Jornada, LineaPagoSolicitud, LineaPedido, Mesa, MotivoMerma, Movimiento,
  Pedido, Plato, ReporteCierre, Reserva, ResultadoCobro, ResumenDelDia, Simulador,
  SugerenciaCompra, Unidad, Usuario,
} from "../dominio/tipos";
import { actualizar, obtener, obtenerTexto, publicar } from "./clienteHttp";

export const sesionApi = {
  usuariosDemo: () => obtener<{ nombre: string; nombreUsuario: string; rol: Usuario["rol"] }[]>(
    "/api/sesion/usuarios-demo"),
  iniciar: (nombreUsuario: string, pin: string) =>
    publicar<{ token: string; usuario: Usuario }>("/api/sesion", { nombreUsuario, pin }),
};

export const salonApi = {
  mesas: () => obtener<Mesa[]>("/api/mesas"),
  menu: () => obtener<Plato[]>("/api/menu"),
  pedidoDeMesa: (numero: number) => obtener<Pedido | null>(`/api/mesas/${numero}/pedido`),
};

export const pedidosApi = {
  registrar: (numeroMesa: number, lineas: LineaPedido[]) =>
    publicar<Pedido>("/api/pedidos", {
      numeroMesa,
      items: lineas.map((l) => ({ productoId: l.plato.id, cantidad: l.cantidad })),
    }),
  listos: () => obtener<Pedido[]>("/api/pedidos/listos"),
  entregar: (id: number) => publicar<Pedido>(`/api/pedidos/${id}/entregar`),
  cancelar: (id: number, motivo: string) => publicar<Pedido>(`/api/pedidos/${id}/cancelar`, { motivo }),
};

export const cocinaApi = {
  comandas: () => obtener<Pedido[]>("/api/comandas"),
  iniciar: (id: number) => publicar<Pedido>(`/api/comandas/${id}/iniciar`),
  marcarPlato: (id: number, productoId: number, preparado: boolean) =>
    actualizar<Pedido>(`/api/comandas/${id}/platos/${productoId}`, { preparado }),
  marcarListo: (id: number) => publicar<Pedido>(`/api/comandas/${id}/listo`),
};

export const cajaApi = {
  cuentas: () => obtener<Pedido[]>("/api/caja/cuentas"),
  cobrar: (pedidoId: number, pagos: LineaPagoSolicitud[]) =>
    publicar<ResultadoCobro>("/api/caja/cobros", { pedidoId, pagos }),
  facturas: () => obtener<Factura[]>("/api/facturas"),
  reenviar: (id: number) => publicar<Factura>(`/api/facturas/${id}/reenviar`),
  xml: (id: number) => obtenerTexto(`/api/facturas/${id}/xml`),
};

export const jornadaApi = {
  actual: () => obtener<Jornada>("/api/jornada"),
  resumen: () => obtener<ResumenDelDia>("/api/jornada/resumen"),
  previsualizar: (efectivoContado: number, observacion: string) =>
    publicar<ReporteCierre>("/api/jornada/previsualizar-cierre", { efectivoContado, observacion }),
  cerrar: (efectivoContado: number, observacion: string, confirmarInconsistencias: boolean) =>
    publicar<Jornada>("/api/jornada/cerrar", { efectivoContado, observacion, confirmarInconsistencias }),
  abrir: (baseCaja: number) => publicar<Jornada>("/api/jornada/abrir", { baseCaja }),
};

export const inventarioApi = {
  ingredientes: () => obtener<Ingrediente[]>("/api/inventario/ingredientes"),
  crear: (nombre: string, unidad: Unidad, stockMinimo: number) =>
    publicar<Ingrediente>("/api/inventario/ingredientes", { nombre, unidad, stockMinimo }),
  entrada: (id: number, cantidad: number, proveedor: string) =>
    publicar<Ingrediente>(`/api/inventario/ingredientes/${id}/entradas`, { cantidad, proveedor }),
  merma: (id: number, cantidad: number, motivo: MotivoMerma, detalle: string) =>
    publicar<Ingrediente>(`/api/inventario/ingredientes/${id}/mermas`, { cantidad, motivo, detalle }),
  minimo: (id: number, stockMinimo: number) =>
    actualizar<Ingrediente>(`/api/inventario/ingredientes/${id}/minimo`, { stockMinimo }),
  movimientos: () => obtener<Movimiento[]>("/api/inventario/movimientos"),
  sugerencias: () => obtener<SugerenciaCompra[]>("/api/inventario/sugerencias"),
};

export interface DatosReserva {
  nombreCliente: string;
  telefono: string;
  personas: number;
  inicio: string;
  numeroMesa: number | null;
  notas: string;
}

export const reservasApi = {
  delDia: (fecha: string) => obtener<Reserva[]>(`/api/reservas?fecha=${fecha}`),
  crear: (datos: DatosReserva) => publicar<Reserva>("/api/reservas", datos),
  reprogramar: (id: number, inicio: string, personas: number, numeroMesa: number | null) =>
    actualizar<Reserva>(`/api/reservas/${id}`, { inicio, personas, numeroMesa }),
  confirmarLlegada: (id: number) => publicar<Reserva>(`/api/reservas/${id}/llegada`),
  cancelar: (id: number) => publicar<Reserva>(`/api/reservas/${id}/cancelar`),
  noAsistio: (id: number) => publicar<Reserva>(`/api/reservas/${id}/no-asistio`),
};

export const demostracionApi = {
  simulador: () => obtener<Simulador>("/api/demostracion/simulador"),
  configurar: (estado: Simulador) => actualizar<Simulador>("/api/demostracion/simulador", estado),
  reiniciar: () => publicar<void>("/api/demostracion/reiniciar"),
};
