/** Textos que ve el usuario para cada estado. Un solo lugar para todo el vocabulario. */
import type {
  EstadoPedido, EstadoReserva, MotivoMerma, Rol, TipoMovimiento,
} from "./tipos";

export const ETIQUETA_ESTADO_PEDIDO: Record<EstadoPedido, string> = {
  REGISTRADO: "En cola de cocina",
  EN_PREPARACION: "En preparación",
  LISTO_PARA_SERVIR: "Listo para servir",
  ENTREGADO: "Servido",
  PAGADO: "Pagado",
  FACTURADO: "Facturado",
  CANCELADO: "Cancelado",
};

export const ETIQUETA_ROL: Record<Rol, string> = {
  MESERO: "Mesero",
  COCINERO: "Cocina",
  CAJERO: "Caja",
  ADMINISTRADOR: "Administración",
};

export const ETIQUETA_ESTADO_RESERVA: Record<EstadoReserva, string> = {
  PENDIENTE: "Pendiente",
  CUMPLIDA: "Llegó",
  CANCELADA: "Cancelada",
  NO_ASISTIO: "No asistió",
};

export const ETIQUETA_MOTIVO_MERMA: Record<MotivoMerma, string> = {
  VENCIMIENTO: "Vencimiento",
  DANO: "Daño",
  DERRAME: "Derrame",
  OTRO: "Otro",
};

export const ETIQUETA_MOVIMIENTO: Record<TipoMovimiento, string> = {
  ENTRADA: "Entrada",
  SALIDA_PEDIDO: "Consumo",
  DEVOLUCION: "Devolución",
  MERMA: "Pérdida",
};
