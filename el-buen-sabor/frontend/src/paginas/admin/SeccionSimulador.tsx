import { demostracionApi } from "../../api/endpoints";
import { useCarga } from "../../compartido/useCarga";
import type { Simulador } from "../../dominio/tipos";

interface Props {
  onAviso: (tipo: "exito" | "error", mensaje: string) => void;
  onError: (error: unknown) => void;
}

/** Interruptores para mostrar en la presentación los cursos alternos de las integraciones. */
export function SeccionSimulador({ onAviso, onError }: Props) {
  const estado = useCarga<Simulador | null>(demostracionApi.simulador, null);

  async function cambiar(cambio: Partial<Simulador>) {
    if (!estado.datos) return;
    try {
      estado.setDatos(await demostracionApi.configurar({ ...estado.datos, ...cambio }));
    } catch (error) {
      onError(error);
    }
  }

  async function reiniciar() {
    if (!window.confirm("¿Volver a los datos iniciales? Se borran pedidos, cobros, reservas y movimientos.")) return;
    try {
      await demostracionApi.reiniciar();
      onAviso("exito", "Datos de demostración reiniciados.");
      await estado.recargar();
    } catch (error) {
      onError(error);
    }
  }

  if (!estado.datos) return null;
  return (
    <section>
      <header className="admin__encabezado">
        <div>
          <h2>Simulador de integraciones</h2>
          <p className="admin__fecha">La DIAN y el banco son simulados en este prototipo (patrón Adapter).</p>
        </div>
      </header>
      <div className="interruptores">
        <label className="interruptor">
          <input type="checkbox" checked={estado.datos.dianDisponible}
                 onChange={(e) => cambiar({ dianDisponible: e.target.checked })} />
          <span>
            <strong>Web service de la DIAN disponible</strong>
            Apágalo para ver una factura quedar pendiente, reintentar el envío y el cierre bloqueado (CU-06 9a).
          </span>
        </label>
        <label className="interruptor">
          <input type="checkbox" checked={estado.datos.rechazarProximaTarjeta}
                 onChange={(e) => cambiar({ rechazarProximaTarjeta: e.target.checked })} />
          <span>
            <strong>Rechazar la próxima tarjeta</strong>
            El banco responde "fondos insuficientes" una vez; el cajero cambia de medio de pago (CU-02 5a).
          </span>
        </label>
      </div>
      <button type="button" className="boton boton--peligro-suave" onClick={reiniciar}>
        Reiniciar datos de demostración
      </button>
    </section>
  );
}
