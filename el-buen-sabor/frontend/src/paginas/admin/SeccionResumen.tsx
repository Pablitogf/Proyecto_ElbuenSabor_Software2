import { useState } from "react";
import { jornadaApi } from "../../api/endpoints";
import { formatearFechaLarga, formatearHora } from "../../compartido/formatoHora";
import { formatearCantidad, formatearPesos } from "../../compartido/formatoMoneda";
import { useCarga } from "../../compartido/useCarga";
import { esEvento, useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import type { EventoTiempoReal, ResumenDelDia } from "../../dominio/tipos";
import { ModalApertura } from "./ModalApertura";
import { ModalCierre } from "./ModalCierre";
import { ReporteDeCierre } from "./ReporteDeCierre";

interface Props {
  onIrAInventario: () => void;
  onAviso: (tipo: "exito" | "error", mensaje: string) => void;
  onError: (error: unknown) => void;
}

const EVENTOS_QUE_CAMBIAN_EL_RESUMEN = [
  "CuentaCobrada", "FacturaActualizada", "StockBajoMinimo", "InventarioActualizado",
  "JornadaActualizada", "PedidoRegistrado", "EstadoDePedidoCambiado", "DatosReiniciados",
];

/** IU-04 Resumen: alertas de inventario (RF-14), métricas del día y cierre de caja (RF-10/11). */
export function SeccionResumen({ onIrAInventario, onAviso, onError }: Props) {
  const resumen = useCarga<ResumenDelDia | null>(jornadaApi.resumen, null);
  const [dialogo, setDialogo] = useState<"cierre" | "apertura" | null>(null);

  useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (esEvento(evento, ...EVENTOS_QUE_CAMBIAN_EL_RESUMEN)) void resumen.recargar();
  });

  const datos = resumen.datos;
  if (!datos) return <p className="admin__cargando">Cargando el resumen…</p>;
  const abierta = datos.jornada.estado === "ABIERTA";
  const alertas = datos.alertasInventario;

  function terminar(mensaje: string) {
    setDialogo(null);
    onAviso("exito", mensaje);
    void resumen.recargar();
  }

  return (
    <section>
      <header className="admin__encabezado">
        <div>
          <h2>Resumen del día</h2>
          <p className="admin__fecha">
            {formatearFechaLarga(new Date())} · Caja {abierta ? "abierta" : "cerrada"} desde{" "}
            {formatearHora(abierta ? datos.jornada.fechaApertura : datos.jornada.fechaCierre!)}
          </p>
        </div>
        <button type="button" className="boton boton--primario"
                onClick={() => setDialogo(abierta ? "cierre" : "apertura")}>
          {abierta ? "Ejecutar cierre de caja" : "Abrir nueva jornada"}
        </button>
      </header>

      {alertas.length > 0 && (
        <div className="alerta-inventario" role="status">
          <span aria-hidden="true">⚠</span>
          <p>
            <strong>{alertas.length === 1 ? "1 ingrediente" : `${alertas.length} ingredientes`} en el nivel mínimo:</strong>{" "}
            {alertas.slice(0, 3).map((a) => `${a.nombre} (quedan ${formatearCantidad(a.stock, a.unidad)})`).join(", ")}
            {alertas.length > 3 && ` y ${alertas.length - 3} más`}.
          </p>
          <button type="button" className="boton boton--blanco boton--chico" onClick={onIrAInventario}>
            Ver inventario
          </button>
        </div>
      )}

      <div className="metricas">
        <article className="metrica metrica--destacada">
          <span>Ventas del día</span>
          <strong>{formatearPesos(datos.ventasTotales)}</strong>
          <small>Ticket promedio {formatearPesos(datos.ticketPromedio)}</small>
        </article>
        <article className="metrica">
          <span>Pedidos cobrados</span>
          <strong>{datos.pedidosProcesados}</strong>
          <small>{datos.mesasEnServicio} mesas en servicio ahora</small>
        </article>
        <article className="metrica">
          <span>Facturas validadas por la DIAN</span>
          <strong>{datos.facturasValidadas}/{datos.facturasEmitidas}</strong>
          <small>{datos.facturasEmitidas - datos.facturasValidadas > 0
            ? `${datos.facturasEmitidas - datos.facturasValidadas} pendientes de envío` : "Todo al día"}</small>
        </article>
      </div>

      {!abierta && datos.jornada.reporte && <ReporteDeCierre reporte={datos.jornada.reporte} />}

      {dialogo === "cierre" && (
        <ModalCierre onCerrar={() => setDialogo(null)} onError={onError}
                     onCerrada={() => terminar("Caja cerrada. Reporte enviado a la DIAN.")} />
      )}
      {dialogo === "apertura" && (
        <ModalApertura onCerrar={() => setDialogo(null)} onError={onError}
                       onAbierta={() => terminar("Nueva jornada abierta.")} />
      )}
    </section>
  );
}
