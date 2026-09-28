import { CATEGORIAS } from "../../../dominio/categorias";
import type { Categoria } from "../../../dominio/tipos";

interface Props {
  categoriaActiva: Categoria;
  onCambiarCategoria: (categoria: Categoria) => void;
}

export function MenuCategorias({ categoriaActiva, onCambiarCategoria }: Props) {
  return (
    <nav className="categorias" aria-label="Categorías del menú">
      {CATEGORIAS.map(({ valor, nombre, icono }) => (
        <button
          key={valor}
          type="button"
          className="categorias__boton"
          aria-pressed={valor === categoriaActiva}
          onClick={() => onCambiarCategoria(valor)}
        >
          <span className="categorias__icono" aria-hidden="true">{icono}</span>
          {nombre}
        </button>
      ))}
    </nav>
  );
}
