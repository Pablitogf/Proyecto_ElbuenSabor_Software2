import { useCallback, useState } from "react";
import { ErrorDeApi } from "../../api/clienteHttp";
import { pedidosApi, reservasApi, salonApi } from "../../api/endpoints";
import { Aviso } from "../../compartido/Aviso";
import { AvisoCajaCerrada } from "../../compartido/AvisoCajaCerrada";
import { EncabezadoApp } from "../../compartido/EncabezadoApp";
import { useAviso } from "../../compartido/useAviso";
import { useCarga } from "../../compartido/useCarga";
import { esEvento, useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { useJornada } from "../../compartido/useJornada";
import { CATEGORIA_INICIAL } from "../../dominio/categorias";
import type { Categoria, EventoTiempoReal, Mesa, Pedido } from "../../dominio/tipos";
import { AvisosListos } from "./componentes/AvisosListos";
import { CuadriculaMesas } from "./componentes/CuadriculaMesas";
import { ListaPlatos } from "./componentes/ListaPlatos";
import { MenuCategorias } from "./componentes/MenuCategorias";
import { PanelPedidoActivo } from "./componentes/PanelPedidoActivo";
import { PanelReserva } from "./componentes/PanelReserva";
import { ResumenPedido } from "./componentes/ResumenPedido";
import { useMenu } from "./useMenu";
import { usePedidoEnCurso } from "./usePedidoEnCurso";

const CONFLICTO = 409;

/** IU-01: tablet del mesero. F-01 (tomar pedido), F-05 (servir lo que cocina despacha), F-06 (llegada de reservas). */
export function PaginaMesero() {
  const { aviso, mostrarAviso, mostrarError } = useAviso();
  const mesas = useCarga<Mesa[]>(salonApi.mesas, []);
  const listos = useCarga<Pedido[]>(pedidosApi.listos, []);
  const { jornada, recargarJornada } = useJornada();
  const { platos, cargando, recargarMenu } = useMenu(mostrarError);
  const pedido = usePedidoEnCurso();

  const [numeroSeleccionado, setNumeroSeleccionado] = useState<number | null>(null);
  const [categoria, setCategoria] = useState<Categoria>(CATEGORIA_INICIAL);
  const [ocupado, setOcupado] = useState(false);

  const mesa = mesas.datos.find((m) => m.numero === numeroSeleccionado) ?? null;
  const cajaCerrada = jornada?.estado === "CERRADA";

  const refrescarMenuYAjustar = useCallback(async () => {
    pedido.ajustarAlMenu(await recargarMenu());
  }, [pedido, recargarMenu]);

  const conectado = useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (esEvento(evento, "PedidoRegistrado", "MesasActualizadas", "EstadoDePedidoCambiado",
                 "ReservasActualizadas", "DatosReiniciados")) void mesas.recargar();
    if (esEvento(evento, "PedidoListoParaServir", "EstadoDePedidoCambiado", "DatosReiniciados")) {
      void listos.recargar();
    }
    if (esEvento(evento, "JornadaActualizada", "DatosReiniciados")) void recargarJornada();
    if (esEvento(evento, "InventarioActualizado") && mesa?.estado === "DISPONIBLE") void refrescarMenuYAjustar();
    if (esEvento(evento, "PedidoRegistrado") && evento.datos.numero_mesa === numeroSeleccionado
        && !ocupado && pedido.lineas.length > 0) {
      mostrarError(`Otra tablet acaba de tomar la mesa ${numeroSeleccionado}.`);
      pedido.vaciar();
    }
    if (esEvento(evento, "DatosReiniciados")) setNumeroSeleccionado(null);
  });

  // Paso 1: el mesero toca una mesa.
  function seleccionarMesa(elegida: Mesa) {
    if (elegida.numero !== numeroSeleccionado) pedido.vaciar();
    setNumeroSeleccionado(elegida.numero);
    if (elegida.estado === "DISPONIBLE") void recargarMenu(); // Paso 2: menú con stock actual.
  }

  async function ejecutar(accion: () => Promise<unknown>, exito: string) {
    setOcupado(true);
    try {
      await accion();
      mostrarAviso("exito", exito);
      await Promise.all([mesas.recargar(), listos.recargar()]);
    } catch (error) {
      mostrarError(error);
      if (error instanceof ErrorDeApi && error.codigoHttp === CONFLICTO) {
        await Promise.all([mesas.recargar(), refrescarMenuYAjustar()]);
      }
    } finally {
      setOcupado(false);
    }
  }

  // Pasos 4 y 5: confirmar; la mesa pasa a roja y el panel muestra el pedido recién creado.
  const confirmarPedido = () => mesa && ejecutar(async () => {
    await pedidosApi.registrar(mesa.numero, pedido.lineas);
    pedido.vaciar();
  }, `Pedido de la mesa ${mesa.numero} enviado a cocina.`);

  const servir = (p: Pedido) =>
    ejecutar(() => pedidosApi.entregar(p.id), `Mesa ${p.numeroMesa} servida.`);

  const cancelar = (p: Pedido, motivo: string) =>
    ejecutar(() => pedidosApi.cancelar(p.id, motivo), `Pedido de la mesa ${p.numeroMesa} cancelado.`);

  const confirmarLlegada = (reservaId: number) => ejecutar(async () => {
    await reservasApi.confirmarLlegada(reservaId);
    void recargarMenu();
  }, "Llegada confirmada. Ya puedes tomar el pedido.");

  return (
    <div className="mesero">
      <EncabezadoApp
        titulo="Restaurante El Buen Sabor"
        centro={<span className="encabezado__contexto">{mesa ? `Mesa ${mesa.numero}` : "Selecciona una mesa"}</span>}
        conectado={conectado}
      />
      <div className="mesero__avisos">
        <AvisoCajaCerrada jornada={jornada} />
        <AvisosListos pedidos={listos.datos} onServir={servir} />
      </div>
      <MenuCategorias categoriaActiva={categoria} onCambiarCategoria={setCategoria} />
      <main className="mesero__centro">
        <CuadriculaMesas mesas={mesas.datos} numeroMesaSeleccionada={numeroSeleccionado}
                         onSeleccionarMesa={seleccionarMesa} />
        <ListaPlatos
          platos={platos}
          categoria={categoria}
          lineas={pedido.lineas}
          hayMesaSeleccionada={mesa?.estado === "DISPONIBLE"}
          cargando={cargando}
          onAgregarPlato={pedido.agregar}
        />
      </main>
      {mesa?.estado === "OCUPADA" ? (
        <PanelPedidoActivo mesa={mesa} ocupado={ocupado} onServir={servir} onCancelar={cancelar} />
      ) : mesa?.estado === "RESERVADA" ? (
        <PanelReserva mesa={mesa} ocupado={ocupado} onConfirmarLlegada={confirmarLlegada} />
      ) : (
        <ResumenPedido
          mesa={mesa}
          lineas={pedido.lineas}
          total={pedido.total}
          enviando={ocupado}
          conectado={conectado}
          cajaCerrada={cajaCerrada}
          onAgregarPlato={pedido.agregar}
          onQuitarPlato={pedido.quitar}
          onConfirmar={confirmarPedido}
        />
      )}
      <Aviso aviso={aviso} />
    </div>
  );
}
