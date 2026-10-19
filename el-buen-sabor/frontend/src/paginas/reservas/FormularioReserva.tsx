import { useState, type FormEvent } from "react";
import type { DatosReserva } from "../../api/endpoints";
import type { Mesa, Reserva } from "../../dominio/tipos";
import { franjasDisponibles, propuestaInicial, separarFechaHora, unirFechaHora } from "./horarios";

interface Props {
  mesas: Mesa[];
  fechaInicial: string;
  reserva?: Reserva; // Si viene, es una reprogramación.
  enviando: boolean;
  onGuardar: (datos: DatosReserva) => void;
  onCancelar: () => void;
}

const AUTOMATICA = "";

export function FormularioReserva({ mesas, fechaInicial, reserva, enviando, onGuardar, onCancelar }: Props) {
  const inicial = reserva ? separarFechaHora(reserva.inicio) : propuestaInicial(fechaInicial, new Date());
  const [nombre, setNombre] = useState(reserva?.nombreCliente ?? "");
  const [telefono, setTelefono] = useState(reserva?.telefono ?? "");
  const [personas, setPersonas] = useState(reserva?.personas ?? 2);
  const [fecha, setFecha] = useState(inicial.fecha);
  const [hora, setHora] = useState(inicial.hora);
  const [mesa, setMesa] = useState<string>(AUTOMATICA);
  const [notas, setNotas] = useState(reserva?.notas ?? "");

  function guardar(evento: FormEvent) {
    evento.preventDefault();
    onGuardar({
      nombreCliente: nombre, telefono, personas, notas,
      inicio: unirFechaHora(fecha, hora),
      numeroMesa: mesa === AUTOMATICA ? null : Number(mesa),
    });
  }

  const mesasQueSirven = mesas.filter((m) => m.capacidad >= personas);
  const franjas = franjasDisponibles(fecha, new Date());
  const opcionesDeHora = franjas.includes(hora) || !hora ? franjas : [hora, ...franjas];

  return (
    <form className="formulario" onSubmit={guardar}>
      {!reserva && (
        <div className="formulario__fila">
          <label className="campo-etiquetado">Nombre del cliente
            <input className="campo" value={nombre} onChange={(e) => setNombre(e.target.value)} required autoFocus />
          </label>
          <label className="campo-etiquetado">Teléfono
            <input className="campo" inputMode="tel" value={telefono} placeholder="3001234567"
                   onChange={(e) => setTelefono(e.target.value)} required />
          </label>
        </div>
      )}
      <div className="formulario__fila formulario__fila--tres">
        <label className="campo-etiquetado">Personas
          <input className="campo" type="number" min={1} max={12} value={personas}
                 onChange={(e) => setPersonas(Number(e.target.value))} required />
        </label>
        <label className="campo-etiquetado">Fecha
          <input className="campo" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} required />
        </label>
        <label className="campo-etiquetado">Hora
          <select className="campo" value={hora} onChange={(e) => setHora(e.target.value)}>
            {opcionesDeHora.length === 0 && <option value="">Sin franjas este día</option>}
            {opcionesDeHora.map((h) => <option key={h} value={h}>{h}</option>)}
          </select>
        </label>
      </div>
      <label className="campo-etiquetado">Mesa
        <select className="campo" value={mesa} onChange={(e) => setMesa(e.target.value)}>
          <option value={AUTOMATICA}>
            {reserva ? `Mantener la mesa ${reserva.numeroMesa} si sirve, o asignar otra` : "Asignar la mejor mesa automáticamente"}
          </option>
          {mesasQueSirven.map((m) => (
            <option key={m.numero} value={m.numero}>Mesa {m.numero} · {m.capacidad} puestos</option>
          ))}
        </select>
      </label>
      {!reserva && (
        <label className="campo-etiquetado">Notas (opcional)
          <input className="campo" value={notas} placeholder="Ej: cumpleaños, silla para bebé"
                 onChange={(e) => setNotas(e.target.value)} />
        </label>
      )}
      <p className="formulario__ayuda">
        Reservas de 11:00 a 20:00, mínimo 15 minutos antes y hasta 30 días adelante. Cada reserva aparta la mesa 2 horas.
      </p>
      <div className="fila-botones fila-botones--derecha">
        <button type="button" className="boton boton--secundario" onClick={onCancelar}>Volver</button>
        <button className="boton boton--primario" disabled={enviando}>
          {enviando ? "Guardando…" : reserva ? "Guardar cambios" : "Registrar reserva"}
        </button>
      </div>
    </form>
  );
}
