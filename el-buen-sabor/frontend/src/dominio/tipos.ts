/** Contratos que devuelve la API (JSON en camelCase). */

export type Rol = "MESERO" | "COCINERO" | "CAJERO" | "ADMINISTRADOR";
export type Permiso =
  | "VER_SALON" | "REGISTRAR_PEDIDO" | "ATENDER_MESA" | "VER_COMANDAS" | "PREPARAR_PEDIDO"
  | "COBRAR" | "VER_REGISTROS_CAJA" | "GESTIONAR_FACTURAS" | "CERRAR_CAJA"
  | "GESTIONAR_INVENTARIO" | "VER_RESERVAS" | "GESTIONAR_RESERVAS" | "ADMINISTRAR_SISTEMA";

export interface Usuario {
  id: number;
  nombre: string;
  nombreUsuario: string;
  rol: Rol;
  permisos: Permiso[];
}

export type EstadoMesa = "DISPONIBLE" | "OCUPADA" | "RESERVADA";
export type EstadoPedido =
  | "REGISTRADO" | "EN_PREPARACION" | "LISTO_PARA_SERVIR" | "ENTREGADO"
  | "PAGADO" | "FACTURADO" | "CANCELADO";
export type Categoria = "BEBIDAS" | "ENTRADAS" | "PLATOS_PRINCIPALES" | "POSTRES" | "LICORES";

export interface ReservaBreve {
  id: number;
  nombreCliente: string;
  personas: number;
  inicio: string;
}

export interface Mesa {
  numero: number;
  capacidad: number;
  estado: EstadoMesa;
  reservaQueAparta: ReservaBreve | null;
  proximaReserva: ReservaBreve | null;
  pedido: { id: number; estado: EstadoPedido; total: number; cantidadPlatos: number } | null;
}

export interface Plato {
  id: number;
  nombre: string;
  descripcion: string;
  precio: number;
  categoria: Categoria;
  icono: string;
  porcionesDisponibles: number;
  disponible: boolean;
}

export interface LineaPedido {
  plato: Plato;
  cantidad: number;
}

export interface DetallePedido {
  productoId: number;
  nombreProducto: string;
  cantidad: number;
  precioUnitario: number;
  subtotal: number;
  preparado: boolean;
}

export interface Pedido {
  id: number;
  numeroMesa: number;
  fechaHora: string;
  estado: EstadoPedido;
  detalles: DetallePedido[];
  total: number;
  horaListo: string | null;
  motivoCancelacion: string | null;
}

// ── Caja y facturación ──────────────────────────────────────────────────────
export type MetodoPago = "EFECTIVO" | "TARJETA";

export interface LineaPagoSolicitud {
  metodo: MetodoPago;
  monto: number;
  montoRecibido?: number;
}

export interface Pago {
  id: number;
  total: number;
  cambio: number;
  metodo: string;
  fechaHora: string;
  lineas: (LineaPagoSolicitud & { autorizacion: string | null; cambio: number })[];
}

export type EstadoFactura = "PENDIENTE_DIAN" | "VALIDADA";

export interface Factura {
  id: number;
  numero: string;
  numeroMesa: number | null;
  fechaEmision: string;
  base: number;
  impuesto: number;
  nombreImpuesto: string;
  tarifaImpuesto: number;
  total: number;
  cufe: string;
  estado: EstadoFactura;
  intentosEnvio: number;
  ultimoError: string | null;
  codigoValidacion: string | null;
  metodoPago: string | null;
}

export interface ResultadoCobro {
  pago: Pago;
  factura: Factura;
}

export interface ReporteCierre {
  transacciones: number;
  totalVentas: number;
  ventasPorMetodo: Record<MetodoPago, number>;
  impuestoTotal: number;
  facturasEmitidas: number;
  pedidosCancelados: number;
  baseCaja: number;
  efectivoEsperado: number;
  efectivoContado: number;
  diferenciaEfectivo: number;
  inconsistencias: string[];
  bloqueos: string[];
  sePuedeCerrar: boolean;
  observacion: string | null;
  comprobanteDian: string | null;
}

export interface Jornada {
  id: number;
  estado: "ABIERTA" | "CERRADA";
  fechaApertura: string;
  fechaCierre: string | null;
  baseCaja: number;
  reporte: ReporteCierre | null;
}

export interface ResumenDelDia {
  jornada: Jornada;
  ventasTotales: number;
  pedidosProcesados: number;
  ticketPromedio: number;
  facturasValidadas: number;
  facturasEmitidas: number;
  mesasEnServicio: number;
  alertasInventario: Ingrediente[];
}

// ── Inventario ──────────────────────────────────────────────────────────────
export type Unidad = "g" | "ml" | "und";
export type MotivoMerma = "VENCIMIENTO" | "DANO" | "DERRAME" | "OTRO";
export type TipoMovimiento = "ENTRADA" | "SALIDA_PEDIDO" | "DEVOLUCION" | "MERMA";

export interface Ingrediente {
  id: number;
  nombre: string;
  unidad: Unidad;
  stock: number;
  stockMinimo: number;
  bajoMinimo: boolean;
}

export interface Movimiento {
  id: number;
  ingrediente: string;
  unidad: Unidad;
  tipo: TipoMovimiento;
  cantidad: number;
  fechaHora: string;
  proveedor: string | null;
  motivo: MotivoMerma | null;
  detalle: string | null;
  pedidoId: number | null;
}

export interface SugerenciaCompra {
  ingrediente: Ingrediente;
  consumoDiario: number;
  diasRestantes: number | null;
  cantidadSugerida: number;
}

// ── Reservas ────────────────────────────────────────────────────────────────
export type EstadoReserva = "PENDIENTE" | "CUMPLIDA" | "CANCELADA" | "NO_ASISTIO";

export interface Reserva {
  id: number;
  nombreCliente: string;
  telefono: string;
  personas: number;
  inicio: string;
  fin: string;
  numeroMesa: number;
  estado: EstadoReserva;
  notas: string | null;
  vencida: boolean;
  puedeConfirmarse: boolean;
}

export interface Simulador {
  dianDisponible: boolean;
  rechazarProximaTarjeta: boolean;
}

export interface EventoTiempoReal {
  tipo: string;
  datos: Record<string, unknown>;
}
