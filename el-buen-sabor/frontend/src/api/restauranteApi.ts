import type { Comanda, LineaPedido, Mesa, Plato } from "../dominio/tipos";
import { solicitar } from "./clienteHttp";
import type { MesaJson, PedidoJson, PlatoJson } from "./contratosApi";
import { aComanda, aMesa, aPlato, aSolicitudDePedido } from "./traductores";

export async function obtenerMesas(): Promise<Mesa[]> {
  const mesas = await solicitar<MesaJson[]>("/api/mesas");
  return mesas.map(aMesa);
}

export async function obtenerMenu(): Promise<Plato[]> {
  const platos = await solicitar<PlatoJson[]>("/api/menu");
  return platos.map(aPlato);
}

export async function registrarPedido(
  numeroMesa: number,
  lineas: LineaPedido[],
): Promise<Comanda> {
  const pedido = await solicitar<PedidoJson>("/api/pedidos", {
    method: "POST",
    body: JSON.stringify(aSolicitudDePedido(numeroMesa, lineas)),
  });
  return aComanda(pedido);
}

export async function obtenerComandasActivas(): Promise<Comanda[]> {
  const comandas = await solicitar<PedidoJson[]>("/api/comandas");
  return comandas.map(aComanda);
}

export async function reiniciarDatosDeDemostracion(): Promise<void> {
  await solicitar<void>("/api/demostracion/reiniciar", { method: "POST" });
}
