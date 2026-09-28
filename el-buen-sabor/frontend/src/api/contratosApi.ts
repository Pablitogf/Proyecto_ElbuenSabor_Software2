/** Forma exacta del JSON que envía y recibe el backend (snake_case). */
import type { Categoria, EstadoMesa } from "../dominio/tipos";

export interface MesaJson {
  numero: number;
  capacidad: number;
  estado: EstadoMesa;
}

export interface PlatoJson {
  id: number;
  nombre: string;
  descripcion: string;
  precio: number;
  categoria: Categoria;
  icono: string;
  porciones_disponibles: number;
  disponible: boolean;
}

export interface DetallePedidoJson {
  producto_id: number;
  nombre_producto: string;
  cantidad: number;
  precio_unitario: number;
  subtotal: number;
}

export interface PedidoJson {
  id: number;
  numero_mesa: number;
  fecha_hora: string;
  estado: string;
  detalles: DetallePedidoJson[];
  total: number;
}

export interface PedidoSolicitudJson {
  numero_mesa: number;
  items: { producto_id: number; cantidad: number }[];
}

export type EventoJson =
  | { tipo: "PEDIDO_REGISTRADO"; datos: { comanda: PedidoJson; mesa: MesaJson } }
  | { tipo: "DATOS_REINICIADOS"; datos: Record<string, never> };
