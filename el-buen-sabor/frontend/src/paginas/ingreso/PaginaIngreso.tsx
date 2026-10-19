import { useEffect, useState, type FormEvent } from "react";
import { mensajeDe } from "../../api/clienteHttp";
import { sesionApi } from "../../api/endpoints";
import { INICIO_POR_ROL, navegar } from "../../compartido/navegacion";
import { ETIQUETA_ROL } from "../../dominio/etiquetas";
import type { Rol } from "../../dominio/tipos";
import { useSesion } from "../../sesion/ContextoSesion";

interface UsuarioDemo {
  nombre: string;
  nombreUsuario: string;
  rol: Rol;
}

const ICONO_ROL: Record<Rol, string> = { MESERO: "🧾", COCINERO: "👨‍🍳", CAJERO: "💵", ADMINISTRADOR: "📊" };
const LARGO_PIN = 4;

/** RF-01: el mesero (y todo el personal) debe autenticarse antes de operar. */
export function PaginaIngreso() {
  const { iniciar } = useSesion();
  const [usuarios, setUsuarios] = useState<UsuarioDemo[]>([]);
  const [elegido, setElegido] = useState<UsuarioDemo | null>(null);
  const [pin, setPin] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    sesionApi.usuariosDemo().then(setUsuarios).catch((e) => setError(mensajeDe(e)));
  }, []);

  async function ingresar(evento?: FormEvent) {
    evento?.preventDefault();
    if (!elegido || pin.length !== LARGO_PIN) return;
    setEnviando(true);
    try {
      const sesion = await sesionApi.iniciar(elegido.nombreUsuario, pin);
      iniciar(sesion);
      navegar(INICIO_POR_ROL[sesion.usuario.rol], true);
    } catch (causa) {
      setError(mensajeDe(causa));
      setPin("");
    } finally {
      setEnviando(false);
    }
  }

  function teclear(digito: string) {
    setError(null);
    setPin((actual) => (actual.length < LARGO_PIN ? actual + digito : actual));
  }

  return (
    <main className="ingreso">
      <section className="ingreso__tarjeta">
        <h1 className="ingreso__marca">El Buen Sabor</h1>
        <p className="ingreso__subtitulo">¿Quién está en turno?</p>

        <div className="ingreso__usuarios">
          {usuarios.map((u) => (
            <button
              key={u.nombreUsuario}
              type="button"
              className="ingreso__usuario"
              aria-pressed={elegido?.nombreUsuario === u.nombreUsuario}
              onClick={() => { setElegido(u); setPin(""); setError(null); }}
            >
              <span className="ingreso__icono" aria-hidden="true">{ICONO_ROL[u.rol]}</span>
              <strong>{u.nombre}</strong>
              <small>{ETIQUETA_ROL[u.rol]}</small>
            </button>
          ))}
        </div>

        {elegido && (
          <form className="ingreso__pin" onSubmit={ingresar}>
            <label htmlFor="pin">PIN de {elegido.nombre.split(" ")[0]}</label>
            <input
              id="pin"
              type="password"
              inputMode="numeric"
              autoComplete="off"
              maxLength={LARGO_PIN}
              value={pin}
              onChange={(e) => { setError(null); setPin(e.target.value.replace(/\D/g, "")); }}
              autoFocus
            />
            <div className="teclado" aria-hidden="true">
              {["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"].map((tecla) =>
                tecla === "" ? <span key="vacio" /> : (
                  <button
                    key={tecla}
                    type="button"
                    tabIndex={-1}
                    onClick={() => (tecla === "⌫" ? setPin((p) => p.slice(0, -1)) : teclear(tecla))}
                  >
                    {tecla}
                  </button>
                ))}
            </div>
            <button className="boton boton--primario boton--grande" disabled={pin.length !== LARGO_PIN || enviando}>
              {enviando ? "Ingresando…" : "Ingresar"}
            </button>
          </form>
        )}
        {error && <p className="ingreso__error" role="alert">{error}</p>}
        <p className="ingreso__ayuda">PIN de demostración: mesero 1111 · cocina 2222 · caja 3333 · admin 0000</p>
      </section>
    </main>
  );
}
