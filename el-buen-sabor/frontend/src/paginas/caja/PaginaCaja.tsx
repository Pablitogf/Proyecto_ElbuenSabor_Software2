import { useState } from "react";
import { cajaApi } from "../../api/endpoints";
import { Aviso } from "../../compartido/Aviso";
import { AvisoCajaCerrada } from "../../compartido/AvisoCajaCerrada";
import { EncabezadoApp } from "../../compartido/EncabezadoApp";
import { Modal } from "../../compartido/Modal";
import { useAviso } from "../../compartido/useAviso";
import { useCarga } from "../../compartido/useCarga";
import { esEvento, useEventosTiempoReal } from "../../compartido/useEventosTiempoReal";
import { useJornada } from "../../compartido/useJornada";
import type { EventoTiempoReal, Factura, LineaPagoSolicitud, Pedido, ResultadoCobro } from "../../dominio/tipos";
import { ComprobanteCobro } from "./ComprobanteCobro";
import { ListaCuentas } from "./ListaCuentas";
import { PanelCobro } from "./PanelCobro";
import { TablaFacturas } from "./TablaFacturas";

/** IU-03: módulo de caja. F-02 (cobro) y F-03 (factura electrónica DIAN). */
export function PaginaCaja() {
  const { aviso, mostrarAviso, mostrarError } = useAviso();
  const cuentas = useCarga<Pedido[]>(cajaApi.cuentas, []);
  const facturas = useCarga<Factura[]>(cajaApi.facturas, []);
  const { jornada, recargarJornada } = useJornada();
  const [seleccionada, setSeleccionada] = useState<number | null>(null);
  const [cobrando, setCobrando] = useState(false);
  const [ultimo, setUltimo] = useState<ResultadoCobro | null>(null);
  const [reenviando, setReenviando] = useState<number | null>(null);
  const [xml, setXml] = useState<{ numero: string; contenido: string } | null>(null);

  const cuenta = cuentas.datos.find((c) => c.id === seleccionada) ?? null;

  const conectado = useEventosTiempoReal((evento: EventoTiempoReal) => {
    if (esEvento(evento, "EstadoDePedidoCambiado", "PedidoRegistrado", "DatosReiniciados")) void cuentas.recargar();
    if (esEvento(evento, "FacturaActualizada", "DatosReiniciados")) void facturas.recargar();
    if (esEvento(evento, "JornadaActualizada", "DatosReiniciados")) void recargarJornada();
  });

  async function cobrar(pagos: LineaPagoSolicitud[]) {
    if (!cuenta) return;
    setCobrando(true);
    try {
      const resultado = await cajaApi.cobrar(cuenta.id, pagos);
      setUltimo(resultado);
      setSeleccionada(null);
      const validada = resultado.factura.estado === "VALIDADA";
      mostrarAviso(validada ? "exito" : "error", validada
        ? `Mesa ${cuenta.numeroMesa} cobrada. Factura ${resultado.factura.numero} validada.`
        : `Pago registrado, pero la DIAN no respondió. Reintenta el envío de ${resultado.factura.numero}.`);
      await Promise.all([cuentas.recargar(), facturas.recargar()]);
    } catch (error) {
      mostrarError(error); // Tarjeta rechazada: nada se registró; se puede cambiar de medio (CU-02 5a).
    } finally {
      setCobrando(false);
    }
  }

  async function reenviar(factura: Factura) {
    setReenviando(factura.id);
    try {
      const actualizada = await cajaApi.reenviar(factura.id);
      mostrarAviso(actualizada.estado === "VALIDADA" ? "exito" : "error",
        actualizada.estado === "VALIDADA" ? `Factura ${actualizada.numero} validada.`
          : `La DIAN sigue sin responder (${actualizada.intentosEnvio} intentos).`);
      await facturas.recargar();
    } catch (error) {
      mostrarError(error);
    } finally {
      setReenviando(null);
    }
  }

  async function verXml(factura: Factura) {
    try {
      setXml({ numero: factura.numero, contenido: await cajaApi.xml(factura.id) });
    } catch (error) {
      mostrarError(error);
    }
  }

  return (
    <div className="caja">
      <EncabezadoApp titulo="Módulo de caja" conectado={conectado}
                     centro={<span className="encabezado__contexto">{cuenta ? `Mesa ${cuenta.numeroMesa}` : ""}</span>} />
      <AvisoCajaCerrada jornada={jornada} />
      <div className="caja__cuerpo">
        <aside className="caja__cuentas">
          <h2 className="caja__subtitulo">Mesas con cuenta</h2>
          <ListaCuentas cuentas={cuentas.datos} seleccionada={seleccionada}
                        onSeleccionar={(p) => setSeleccionada(p.id)} />
        </aside>
        <main className="caja__principal">
          {cuenta ? (
            <PanelCobro cuenta={cuenta} cobrando={cobrando} cajaCerrada={jornada?.estado === "CERRADA"}
                        onCobrar={cobrar} />
          ) : (
            <p className="caja__indicacion">Selecciona una mesa para procesar el pago.</p>
          )}
          {ultimo && <ComprobanteCobro resultado={ultimo} />}
          <h2 className="caja__subtitulo">Facturas recientes</h2>
          <TablaFacturas facturas={facturas.datos} reenviando={reenviando} onReenviar={reenviar} onVerXml={verXml} />
        </main>
      </div>
      {xml && (
        <Modal titulo={`XML de la factura ${xml.numero}`} ancho="amplio" onCerrar={() => setXml(null)}>
          <pre className="xml">{xml.contenido}</pre>
        </Modal>
      )}
      <Aviso aviso={aviso} />
    </div>
  );
}
