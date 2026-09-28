import type { Categoria } from "./tipos";

export interface OpcionCategoria {
  valor: Categoria;
  nombre: string;
  icono: string;
}

export const CATEGORIAS: OpcionCategoria[] = [
  { valor: "BEBIDAS", nombre: "Bebidas", icono: "🥤" },
  { valor: "ENTRADAS", nombre: "Entradas", icono: "🥟" },
  { valor: "PLATOS_PRINCIPALES", nombre: "Platos principales", icono: "🍛" },
  { valor: "POSTRES", nombre: "Postres", icono: "🍰" },
  { valor: "LICORES", nombre: "Licores", icono: "🍺" },
];

export const CATEGORIA_INICIAL: Categoria = "PLATOS_PRINCIPALES";
