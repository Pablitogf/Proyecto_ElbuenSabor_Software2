import { useState, type FormEvent } from "react";
import { jornadaApi } from "../../api/endpoints";
import { leerPesos } from "../../compartido/formatoMoneda";
import { Modal } from "../../compartido/Modal";

interface Props {
  onCerrar: () => void;
  onAbierta: () => void;
  onError: (error: unknown) => void;
}

export function ModalApertura({ onCerrar, onAbierta, onError }: Props) {
  const [base, setBase] = useState("200000");
  const [enviando, setEnviando] = useState(false);

  async function abrir(evento: FormEvent) {
    evento.preventDefault();
    setEnviando(true);
    try {
      await jornadaApi.abrir(leerPesos(base));
      onAbierta();
    } catch (error) {
      onError(error);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Modal titulo="Abrir nueva jornada" onCerrar={onCerrar}>
      <form className="formulario" onSubmit={abrir}>
        <label className="campo-etiquetado">Base de caja (efectivo inicial)
          <input className="campo campo--dinero" inputMode="numeric" value={base}
                 onChange={(e) => setBase(e.target.value)} autoFocus />
        </label>
        <div className="fila-botones fila-botones--derecha">
          <button type="button" className="boton boton--secundario" onClick={onCerrar}>Volver</button>
          <button className="boton boton--primario" disabled={enviando}>Abrir caja</button>
        </div>
      </form>
    </Modal>
  );
}
