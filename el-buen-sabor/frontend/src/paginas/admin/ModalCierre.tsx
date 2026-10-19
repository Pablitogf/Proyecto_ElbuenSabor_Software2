import { useState, type FormEvent } from "react";
import { jornadaApi } from "../../api/endpoints";
import { leerPesos } from "../../compartido/formatoMoneda";
import { Modal } from "../../compartido/Modal";
import type { ReporteCierre } from "../../dominio/tipos";
import { ReporteDeCierre } from "./ReporteDeCierre";

interface Props {
  onCerrar: () => void;
  onCerrada: () => void;
  onError: (error: unknown) => void;
}

/** CU-02 pasos 8-10: arqueo, revisión de bloqueos e inconsistencias, y cierre. */
export function ModalCierre({ onCerrar, onCerrada, onError }: Props) {
  const [efectivo, setEfectivo] = useState("");
  const [previo, setPrevio] = useState<ReporteCierre | null>(null);
  const [observacion, setObservacion] = useState("");
  const [confirmado, setConfirmado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  async function revisar(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    try {
      setPrevio(await jornadaApi.previsualizar(leerPesos(efectivo), observacion));
      setConfirmado(false);
    } catch (error) {
      onError(error);
    } finally {
      setEnviando(false);
    }
  }

  async function cerrar() {
    setEnviando(true);
    try {
      await jornadaApi.cerrar(leerPesos(efectivo), observacion, confirmado);
      onCerrada();
    } catch (error) {
      onError(error);
    } finally {
      setEnviando(false);
    }
  }

  const hayInconsistencias = (previo?.inconsistencias.length ?? 0) > 0;
  const listoParaCerrar = previo?.sePuedeCerrar && (!hayInconsistencias || (confirmado && observacion.trim()));

  return (
    <Modal titulo="Cierre de caja" onCerrar={onCerrar} ancho="amplio">
      <form className="formulario formulario--en-linea" onSubmit={revisar}>
        <label className="campo-etiquetado">Efectivo contado en caja (incluye la base)
          <input className="campo campo--dinero" inputMode="numeric" value={efectivo} placeholder="$ 0"
                 onChange={(e) => { setEfectivo(e.target.value); setPrevio(null); }} required autoFocus />
        </label>
        <button className="boton boton--secundario" disabled={enviando || !efectivo}>Revisar cuadre</button>
      </form>

      {previo && (
        <>
          <ReporteDeCierre reporte={previo} previo />
          {previo.bloqueos.length > 0 && (
            <div className="caja-mensajes caja-mensajes--peligro">
              <strong>No se puede cerrar todavía</strong>
              <ul>{previo.bloqueos.map((b) => <li key={b}>{b}</li>)}</ul>
            </div>
          )}
          {previo.sePuedeCerrar && hayInconsistencias && (
            <div className="caja-mensajes caja-mensajes--alerta">
              <strong>Revisa estas inconsistencias antes de cerrar</strong>
              <ul>{previo.inconsistencias.map((i) => <li key={i}>{i}</li>)}</ul>
              <label className="campo-etiquetado">Observación (obligatoria)
                <textarea className="campo" rows={2} value={observacion}
                          onChange={(e) => setObservacion(e.target.value)} />
              </label>
              <label className="casilla">
                <input type="checkbox" checked={confirmado} onChange={(e) => setConfirmado(e.target.checked)} />
                Revisé cada inconsistencia y quiero cerrar de todas formas
              </label>
            </div>
          )}
          <div className="fila-botones fila-botones--derecha">
            <button type="button" className="boton boton--secundario" onClick={onCerrar}>Volver</button>
            <button type="button" className="boton boton--primario" disabled={!listoParaCerrar || enviando}
                    onClick={cerrar}>
              {enviando ? "Enviando reporte a la DIAN…" : "Cerrar caja y enviar reporte"}
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}
