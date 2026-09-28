import { useCallback, useState } from "react";
import { ErrorDeApi } from "../../api/clienteHttp";
import { registrarPedido, reiniciarDatosDeDemostracion } from "../../api/restauranteApi";
import { Aviso } from "../../compartido/Aviso";
import { useAviso } from "../../compartido/useAviso";
import { useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { CATEGORIA_INICIAL } from "../../dominio/categorias";
import type { Categoria, EventoTiempoReal, Mesa } from "../../dominio/tipos";
import { BarraSuperior } from "./componentes/BarraSuperior";
import { CuadriculaMesas } from "./componentes/CuadriculaMesas";
import { ListaPlatos } from "./componentes/ListaPlatos";
import { MenuCategorias } from "./componentes/MenuCategorias";
import { ResumenPedido } from "./componentes/ResumenPedido";
import { useMenu } from "./useMenu";
import { useMesas } from "./useMesas";
import { usePedidoEnCurso } from "./usePedidoEnCurso";

const CODIGO_CONFLICTO = 409;

/** IU-01: tablet del mesero. Orquesta los pasos 1 a 5 del registro de pedido (F-01). */
export function PaginaMesero() {
  const { aviso, mostrarAviso } = useAviso();
  const mostrarError = useCallback(
    (mensaje: string) => mostrarAviso("error", mensaje),
    [mostrarAviso],
  );

  const { mesas, recargarMesas, actualizarMesa } = useMesas(mostrarError);
  const { platos, cargando, recargarMenu } = useMenu(mostrarError);
  const { lineas, total, agregar, quitar, vaciar, ajustarAlMenu } = usePedidoEnCurso();

  const [numeroMesaSeleccionada, setNumeroMesaSeleccionada] = useState<number | null>(null);
  const [categoria, setCategoria] = useState<Categoria>(CATEGORIA_INICIAL);
  const [enviando, setEnviando] = useState(false);

  const mesaSeleccionada = mesas.find((mesa) => mesa.numero === numeroMesaSeleccionada) ?? null;

  const refrescarMenuYAjustarPedido = useCallback(async () => {
    ajustarAlMenu(await recargarMenu());
  }, [ajustarAlMenu, recargarMenu]);

  const terminarAtencionDeMesa = useCallback(() => {
    setNumeroMesaSeleccionada(null);
    vaciar();
  }, [vaciar]);

  const conectado = useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (evento.tipo === "DATOS_REINICIADOS") {
      terminarAtencionDeMesa();
      void recargarMesas();
      return;
    }
    actualizarMesa(evento.mesa);
    if (evento.mesa.numero === numeroMesaSeleccionada && !enviando) {
      mostrarError(`Otra tablet acaba de tomar la mesa ${evento.mesa.numero}.`);
      terminarAtencionDeMesa();
    } else if (numeroMesaSeleccionada !== null) {
      void refrescarMenuYAjustarPedido(); // Otro pedido pudo gastar ingredientes.
    }
  });

  // Paso 1: el mesero toca una mesa.
  function seleccionarMesa(mesa: Mesa) {
    if (mesa.estado !== "DISPONIBLE") {
      mostrarError(`La mesa ${mesa.numero} está ocupada. Elige una mesa en verde.`);
      return;
    }
    if (mesa.numero !== numeroMesaSeleccionada) vaciar();
    setNumeroMesaSeleccionada(mesa.numero);
    void recargarMenu(); // Paso 2: consulta el menú con el stock actual.
  }

  // Paso 4: el mesero confirma el pedido.
  async function confirmarPedido() {
    if (!mesaSeleccionada) return;
    setEnviando(true);
    try {
      await registrarPedido(mesaSeleccionada.numero, lineas);
      actualizarMesa({ ...mesaSeleccionada, estado: "OCUPADA" }); // Paso 5.
      mostrarAviso("exito", `Pedido de la mesa ${mesaSeleccionada.numero} enviado a cocina.`);
      terminarAtencionDeMesa();
    } catch (error) {
      mostrarError((error as Error).message);
      if (error instanceof ErrorDeApi && error.codigoHttp === CODIGO_CONFLICTO) {
        await Promise.all([recargarMesas(), refrescarMenuYAjustarPedido()]);
      }
    } finally {
      setEnviando(false);
    }
  }

  async function reiniciarDatos() {
    try {
      await reiniciarDatosDeDemostracion();
      mostrarAviso("exito", "Datos de demostración reiniciados.");
    } catch (error) {
      mostrarError((error as Error).message);
    }
  }

  return (
    <div className="mesero">
      <BarraSuperior
        mesaSeleccionada={mesaSeleccionada}
        conectado={conectado}
        onReiniciarDatos={reiniciarDatos}
      />
      <MenuCategorias categoriaActiva={categoria} onCambiarCategoria={setCategoria} />
      <main className="mesero__centro">
        <CuadriculaMesas
          mesas={mesas}
          numeroMesaSeleccionada={numeroMesaSeleccionada}
          onSeleccionarMesa={seleccionarMesa}
        />
        <ListaPlatos
          platos={platos}
          categoria={categoria}
          lineas={lineas}
          hayMesaSeleccionada={mesaSeleccionada !== null}
          cargando={cargando}
          onAgregarPlato={agregar}
        />
      </main>
      <ResumenPedido
        mesa={mesaSeleccionada}
        lineas={lineas}
        total={total}
        enviando={enviando}
        conectado={conectado}
        onAgregarPlato={agregar}
        onQuitarPlato={quitar}
        onConfirmar={confirmarPedido}
      />
      <Aviso aviso={aviso} />
    </div>
  );
}
