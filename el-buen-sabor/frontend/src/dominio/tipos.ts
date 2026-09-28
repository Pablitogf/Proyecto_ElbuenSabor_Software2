export type EstadoMesa = "DISPONIBLE" | "OCUPADA" | "RESERVADA";

export type Categoria =
  | "BEBIDAS"
  | "ENTRADAS"
  | "PLATOS_PRINCIPALES"
  | "POSTRES"
  | "LICORES";

export interface Mesa {
  numero: number;
  capacidad: number;
  estado: EstadoMesa;
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

export interface DetalleComanda {
  productoId: number;
  nombreProducto: string;
  cantidad: number;
  subtotal: number;
}

export interface Comanda {
  id: number;
  numeroMesa: number;
  fechaHora: Date;
  detalles: DetalleComanda[];
  total: number;
}

export type EventoTiempoReal =
  | { tipo: "PEDIDO_REGISTRADO"; comanda: Comanda; mesa: Mesa }
  | { tipo: "DATOS_REINICIADOS" };
