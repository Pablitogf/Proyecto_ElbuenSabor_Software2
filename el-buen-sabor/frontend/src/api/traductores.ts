/** Convierten el JSON del backend en los tipos que usa la interfaz (camelCase). */
import type { Comanda, EventoTiempoReal, LineaPedido, Mesa, Plato } from "../dominio/tipos";
import type {
  EventoJson,
  MesaJson,
  PedidoJson,
  PedidoSolicitudJson,
  PlatoJson,
} from "./contratosApi";

export function aMesa(json: MesaJson): Mesa {
  return { numero: json.numero, capacidad: json.capacidad, estado: json.estado };
}

export function aPlato(json: PlatoJson): Plato {
  return {
    id: json.id,
    nombre: json.nombre,
    descripcion: json.descripcion,
    precio: json.precio,
    categoria: json.categoria,
    icono: json.icono,
    porcionesDisponibles: json.porciones_disponibles,
    disponible: json.disponible,
  };
}

export function aComanda(json: PedidoJson): Comanda {
  return {
    id: json.id,
    numeroMesa: json.numero_mesa,
    fechaHora: new Date(json.fecha_hora),
    total: json.total,
    detalles: json.detalles.map((detalle) => ({
      productoId: detalle.producto_id,
      nombreProducto: detalle.nombre_producto,
      cantidad: detalle.cantidad,
      subtotal: detalle.subtotal,
    })),
  };
}

export function aEvento(json: EventoJson): EventoTiempoReal {
  switch (json.tipo) {
    case "PEDIDO_REGISTRADO":
      return {
        tipo: json.tipo,
        comanda: aComanda(json.datos.comanda),
        mesa: aMesa(json.datos.mesa),
      };
    case "DATOS_REINICIADOS":
      return { tipo: json.tipo };
  }
}

export function aSolicitudDePedido(
  numeroMesa: number,
  lineas: LineaPedido[],
): PedidoSolicitudJson {
  return {
    numero_mesa: numeroMesa,
    items: lineas.map((linea) => ({ producto_id: linea.plato.id, cantidad: linea.cantidad })),
  };
}
