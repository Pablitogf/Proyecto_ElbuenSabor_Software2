import { useState, type FormEvent } from "react";
import { ETIQUETA_MOTIVO_MERMA } from "../../dominio/etiquetas";
import type { Ingrediente, MotivoMerma, Unidad } from "../../dominio/tipos";

interface Acciones<T> {
  enviando: boolean;
  onGuardar: (datos: T) => void;
  onCancelar: () => void;
}

function Botones({ enviando, onCancelar, texto }: { enviando: boolean; onCancelar: () => void; texto: string }) {
  return (
    <div className="fila-botones fila-botones--derecha">
      <button type="button" className="boton boton--secundario" onClick={onCancelar}>Volver</button>
      <button className="boton boton--primario" disabled={enviando}>{enviando ? "Guardando…" : texto}</button>
    </div>
  );
}

/** CU-04 pasos 3-4 y RF-17: lo que llegó del proveedor. */
export function FormularioEntrada({ ingrediente, ...acciones }:
  { ingrediente: Ingrediente } & Acciones<{ cantidad: number; proveedor: string }>) {
  const [cantidad, setCantidad] = useState("");
  const [proveedor, setProveedor] = useState("");
  const enviar = (e: FormEvent) => {
    e.preventDefault();
    acciones.onGuardar({ cantidad: Number(cantidad), proveedor });
  };
  return (
    <form className="formulario" onSubmit={enviar}>
      <div className="formulario__fila">
        <label className="campo-etiquetado">Cantidad recibida ({ingrediente.unidad})
          <input className="campo" type="number" step="any" value={cantidad}
                 onChange={(e) => setCantidad(e.target.value)} required autoFocus />
        </label>
        <label className="campo-etiquetado">Proveedor
          <input className="campo" value={proveedor} onChange={(e) => setProveedor(e.target.value)} required />
        </label>
      </div>
      <Botones enviando={acciones.enviando} onCancelar={acciones.onCancelar} texto="Registrar entrada" />
    </form>
  );
}

/** RF-17: pérdidas con su causa. */
export function FormularioMerma({ ingrediente, ...acciones }:
  { ingrediente: Ingrediente } & Acciones<{ cantidad: number; motivo: MotivoMerma; detalle: string }>) {
  const [cantidad, setCantidad] = useState("");
  const [motivo, setMotivo] = useState<MotivoMerma>("VENCIMIENTO");
  const [detalle, setDetalle] = useState("");
  const enviar = (e: FormEvent) => {
    e.preventDefault();
    acciones.onGuardar({ cantidad: Number(cantidad), motivo, detalle });
  };
  return (
    <form className="formulario" onSubmit={enviar}>
      <div className="formulario__fila">
        <label className="campo-etiquetado">Cantidad perdida ({ingrediente.unidad})
          <input className="campo" type="number" step="any" value={cantidad}
                 onChange={(e) => setCantidad(e.target.value)} required autoFocus />
        </label>
        <label className="campo-etiquetado">Motivo
          <select className="campo" value={motivo} onChange={(e) => setMotivo(e.target.value as MotivoMerma)}>
            {Object.entries(ETIQUETA_MOTIVO_MERMA).map(([valor, nombre]) => (
              <option key={valor} value={valor}>{nombre}</option>
            ))}
          </select>
        </label>
      </div>
      <label className="campo-etiquetado">Detalle {motivo === "OTRO" ? "(obligatorio)" : "(opcional)"}
        <input className="campo" value={detalle} onChange={(e) => setDetalle(e.target.value)} />
      </label>
      <p className="formulario__ayuda">Hay {ingrediente.stock} {ingrediente.unidad}; no se puede perder más de eso.</p>
      <Botones enviando={acciones.enviando} onCancelar={acciones.onCancelar} texto="Registrar pérdida" />
    </form>
  );
}

/** CU-04 paso 7: nivel mínimo para la alerta (RF-14). */
export function FormularioMinimo({ ingrediente, ...acciones }: { ingrediente: Ingrediente } & Acciones<number>) {
  const [minimo, setMinimo] = useState(String(ingrediente.stockMinimo));
  return (
    <form className="formulario" onSubmit={(e) => { e.preventDefault(); acciones.onGuardar(Number(minimo)); }}>
      <label className="campo-etiquetado">Nivel mínimo ({ingrediente.unidad})
        <input className="campo" type="number" step="any" min={0} value={minimo}
               onChange={(e) => setMinimo(e.target.value)} required autoFocus />
      </label>
      <p className="formulario__ayuda">Si el stock actual ({ingrediente.stock} {ingrediente.unidad}) queda por debajo, se alerta de inmediato.</p>
      <Botones enviando={acciones.enviando} onCancelar={acciones.onCancelar} texto="Guardar mínimo" />
    </form>
  );
}

/** CU-04 pasos 5-6. */
export function FormularioIngrediente(acciones: Acciones<{ nombre: string; unidad: Unidad; stockMinimo: number }>) {
  const [nombre, setNombre] = useState("");
  const [unidad, setUnidad] = useState<Unidad>("g");
  const [minimo, setMinimo] = useState("0");
  const enviar = (e: FormEvent) => {
    e.preventDefault();
    acciones.onGuardar({ nombre, unidad, stockMinimo: Number(minimo) });
  };
  return (
    <form className="formulario" onSubmit={enviar}>
      <label className="campo-etiquetado">Nombre
        <input className="campo" value={nombre} onChange={(e) => setNombre(e.target.value)} required autoFocus />
      </label>
      <div className="formulario__fila">
        <label className="campo-etiquetado">Unidad
          <select className="campo" value={unidad} onChange={(e) => setUnidad(e.target.value as Unidad)}>
            <option value="g">Gramos (g)</option>
            <option value="ml">Mililitros (ml)</option>
            <option value="und">Unidades (und)</option>
          </select>
        </label>
        <label className="campo-etiquetado">Nivel mínimo
          <input className="campo" type="number" step="any" min={0} value={minimo}
                 onChange={(e) => setMinimo(e.target.value)} />
        </label>
      </div>
      <p className="formulario__ayuda">Empieza en cero; registra una entrada cuando llegue del proveedor.</p>
      <Botones enviando={acciones.enviando} onCancelar={acciones.onCancelar} texto="Crear ingrediente" />
    </form>
  );
}
