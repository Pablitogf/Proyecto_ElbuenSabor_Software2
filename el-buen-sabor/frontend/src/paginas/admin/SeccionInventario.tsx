import { useState } from "react";
import { inventarioApi } from "../../api/endpoints";
import { formatearHora } from "../../compartido/formatoHora";
import { formatearCantidad } from "../../compartido/formatoMoneda";
import { Modal } from "../../compartido/Modal";
import { useCarga } from "../../compartido/useCarga";
import { esEvento, useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { ETIQUETA_MOTIVO_MERMA, ETIQUETA_MOVIMIENTO } from "../../dominio/etiquetas";
import type { EventoTiempoReal, Ingrediente, Movimiento, SugerenciaCompra } from "../../dominio/tipos";
import { FormularioEntrada, FormularioIngrediente, FormularioMerma, FormularioMinimo } from "./FormulariosInventario";

interface Props {
  onAviso: (tipo: "exito" | "error", mensaje: string) => void;
  onError: (error: unknown) => void;
}

type Pestana = "ingredientes" | "sugerencias" | "movimientos";
type Dialogo =
  | { tipo: "entrada" | "merma" | "minimo"; ingrediente: Ingrediente }
  | { tipo: "nuevo" }
  | null;

/** F-04 · CU-04: stock en tiempo real, entradas, pérdidas, mínimos y sugerencia de compra. */
export function SeccionInventario({ onAviso, onError }: Props) {
  const ingredientes = useCarga<Ingrediente[]>(inventarioApi.ingredientes, []);
  const sugerencias = useCarga<SugerenciaCompra[]>(inventarioApi.sugerencias, []);
  const movimientos = useCarga<Movimiento[]>(inventarioApi.movimientos, []);
  const [pestana, setPestana] = useState<Pestana>("ingredientes");
  const [dialogo, setDialogo] = useState<Dialogo>(null);
  const [enviando, setEnviando] = useState(false);

  const recargarTodo = () => Promise.all([ingredientes.recargar(), sugerencias.recargar(), movimientos.recargar()]);
  useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (esEvento(evento, "InventarioActualizado", "DatosReiniciados")) void recargarTodo();
  });

  async function guardar(accion: () => Promise<Ingrediente>, mensaje: (i: Ingrediente) => string) {
    setEnviando(true);
    try {
      const ingrediente = await accion();
      onAviso("exito", mensaje(ingrediente));
      setDialogo(null);
      await recargarTodo();
    } catch (error) {
      onError(error);
    } finally {
      setEnviando(false);
    }
  }

  const cerrar = () => setDialogo(null);
  const bajoMinimo = ingredientes.datos.filter((i) => i.bajoMinimo).length;

  return (
    <section>
      <header className="admin__encabezado">
        <div>
          <h2>Inventario</h2>
          <p className="admin__fecha">{ingredientes.datos.length} ingredientes · {bajoMinimo} en el mínimo</p>
        </div>
        <button type="button" className="boton boton--primario" onClick={() => setDialogo({ tipo: "nuevo" })}>
          Nuevo ingrediente
        </button>
      </header>

      <div className="pestanas" role="tablist">
        {([["ingredientes", "Ingredientes"], ["sugerencias", `Sugerencia de compra (${sugerencias.datos.length})`],
           ["movimientos", "Movimientos"]] as [Pestana, string][]).map(([valor, nombre]) => (
          <button key={valor} role="tab" type="button" aria-selected={pestana === valor} onClick={() => setPestana(valor)}>
            {nombre}
          </button>
        ))}
      </div>

      {pestana === "ingredientes" && (
        <table className="tabla">
          <thead>
            <tr><th>Ingrediente</th><th className="num">Stock</th><th className="num">Mínimo</th><th>Estado</th><th aria-label="Acciones" /></tr>
          </thead>
          <tbody>
            {ingredientes.datos.map((i) => (
              <tr key={i.id} className={i.bajoMinimo ? "fila--alerta" : ""}>
                <td>{i.nombre}</td>
                <td className="num">{formatearCantidad(i.stock, i.unidad)}</td>
                <td className="num">{formatearCantidad(i.stockMinimo, i.unidad)}</td>
                <td>
                  {i.stock === 0 ? <span className="insignia insignia--peligro">Agotado</span>
                    : i.bajoMinimo ? <span className="insignia insignia--alerta">Bajo mínimo</span>
                      : <span className="insignia insignia--lista">Suficiente</span>}
                </td>
                <td className="tabla__acciones">
                  <button type="button" className="boton boton--secundario boton--chico"
                          onClick={() => setDialogo({ tipo: "entrada", ingrediente: i })}>Entrada</button>
                  <button type="button" className="boton boton--enlace"
                          onClick={() => setDialogo({ tipo: "merma", ingrediente: i })}>Pérdida</button>
                  <button type="button" className="boton boton--enlace"
                          onClick={() => setDialogo({ tipo: "minimo", ingrediente: i })}>Mínimo</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {pestana === "sugerencias" && (
        sugerencias.datos.length === 0 ? <p className="admin__vacio">El stock cubre los próximos días. No hace falta pedir.</p> : (
          <>
            <p className="admin__nota">
              Cubre 3 días según el consumo promedio de la última semana, más el nivel mínimo. Lo más urgente va primero.
            </p>
            <table className="tabla">
              <thead>
                <tr><th>Ingrediente</th><th className="num">Stock</th><th className="num">Consumo diario</th>
                  <th className="num">Alcanza para</th><th className="num">Pedir</th></tr>
              </thead>
              <tbody>
                {sugerencias.datos.map((s) => (
                  <tr key={s.ingrediente.id}>
                    <td>{s.ingrediente.nombre}</td>
                    <td className="num">{formatearCantidad(s.ingrediente.stock, s.ingrediente.unidad)}</td>
                    <td className="num">{s.consumoDiario ? formatearCantidad(s.consumoDiario, s.ingrediente.unidad) : "—"}</td>
                    <td className="num">{s.diasRestantes === null ? "—" : `${s.diasRestantes} días`}</td>
                    <td className="num"><strong>{formatearCantidad(s.cantidadSugerida, s.ingrediente.unidad)}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )
      )}

      {pestana === "movimientos" && (
        <table className="tabla">
          <thead>
            <tr><th>Hora</th><th>Ingrediente</th><th>Tipo</th><th className="num">Cantidad</th><th>Detalle</th></tr>
          </thead>
          <tbody>
            {movimientos.datos.map((m) => (
              <tr key={m.id}>
                <td>{new Date(m.fechaHora).toLocaleDateString("es-CO", { day: "numeric", month: "short" })} {formatearHora(m.fechaHora)}</td>
                <td>{m.ingrediente}</td>
                <td><span className={`insignia insignia--mov-${m.tipo.toLowerCase()}`}>{ETIQUETA_MOVIMIENTO[m.tipo]}</span></td>
                <td className="num">
                  {m.tipo === "ENTRADA" || m.tipo === "DEVOLUCION" ? "+" : "−"}{formatearCantidad(m.cantidad, m.unidad)}
                </td>
                <td className="texto-suave">
                  {m.proveedor ?? (m.motivo && ETIQUETA_MOTIVO_MERMA[m.motivo])}
                  {m.pedidoId && `Pedido #${m.pedidoId}`}
                  {m.detalle && !m.pedidoId && ` ${m.detalle}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {dialogo?.tipo === "nuevo" && (
        <Modal titulo="Nuevo ingrediente" onCerrar={cerrar}>
          <FormularioIngrediente enviando={enviando} onCancelar={cerrar}
            onGuardar={(d) => guardar(() => inventarioApi.crear(d.nombre, d.unidad, d.stockMinimo),
              (i) => `${i.nombre} creado.`)} />
        </Modal>
      )}
      {dialogo?.tipo === "entrada" && (
        <Modal titulo={`Entrada de ${dialogo.ingrediente.nombre}`} onCerrar={cerrar}>
          <FormularioEntrada ingrediente={dialogo.ingrediente} enviando={enviando} onCancelar={cerrar}
            onGuardar={(d) => guardar(() => inventarioApi.entrada(dialogo.ingrediente.id, d.cantidad, d.proveedor),
              (i) => `Ahora hay ${formatearCantidad(i.stock, i.unidad)} de ${i.nombre}.`)} />
        </Modal>
      )}
      {dialogo?.tipo === "merma" && (
        <Modal titulo={`Pérdida de ${dialogo.ingrediente.nombre}`} onCerrar={cerrar}>
          <FormularioMerma ingrediente={dialogo.ingrediente} enviando={enviando} onCancelar={cerrar}
            onGuardar={(d) => guardar(() => inventarioApi.merma(dialogo.ingrediente.id, d.cantidad, d.motivo, d.detalle),
              (i) => `Pérdida registrada. Quedan ${formatearCantidad(i.stock, i.unidad)}.`)} />
        </Modal>
      )}
      {dialogo?.tipo === "minimo" && (
        <Modal titulo={`Nivel mínimo de ${dialogo.ingrediente.nombre}`} onCerrar={cerrar}>
          <FormularioMinimo ingrediente={dialogo.ingrediente} enviando={enviando} onCancelar={cerrar}
            onGuardar={(minimo) => guardar(() => inventarioApi.minimo(dialogo.ingrediente.id, minimo),
              (i) => i.bajoMinimo ? `${i.nombre} ya está por debajo del nuevo mínimo.` : "Mínimo actualizado.")} />
        </Modal>
      )}
    </section>
  );
}
