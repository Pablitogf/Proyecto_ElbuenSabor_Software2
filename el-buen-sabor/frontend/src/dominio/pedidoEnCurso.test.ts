import { describe, expect, it } from "vitest";
import {
  agregarPlato,
  ajustarAlMenuActual,
  calcularTotal,
  puedeAgregarse,
  quitarPlato,
} from "./pedidoEnCurso";
import type { Plato } from "./tipos";

function crearPlato(cambios: Partial<Plato> = {}): Plato {
  return {
    id: 7,
    nombre: "Bandeja paisa",
    descripcion: "",
    precio: 32000,
    categoria: "PLATOS_PRINCIPALES",
    icono: "🍛",
    porcionesDisponibles: 5,
    disponible: true,
    ...cambios,
  };
}

describe("pedido en curso", () => {
  it("agrega un plato nuevo con cantidad 1 y suma si se repite", () => {
    const bandeja = crearPlato();
    const lineas = agregarPlato(agregarPlato([], bandeja), bandeja);

    expect(lineas).toEqual([{ plato: bandeja, cantidad: 2 }]);
  });

  it("calcula el total con varios platos", () => {
    const bandeja = crearPlato();
    const lomo = crearPlato({ id: 8, nombre: "Lomo saltado", precio: 30000 });
    const lineas = agregarPlato(agregarPlato(agregarPlato([], bandeja), bandeja), lomo);

    expect(calcularTotal(lineas)).toBe(94000);
  });

  it("no deja agregar platos sin stock", () => {
    const mojarra = crearPlato({ disponible: false, porcionesDisponibles: 0 });

    expect(puedeAgregarse([], mojarra)).toBe(false);
    expect(agregarPlato([], mojarra)).toEqual([]);
  });

  it("no supera las porciones disponibles", () => {
    const torta = crearPlato({ porcionesDisponibles: 1 });
    const lineas = agregarPlato(agregarPlato([], torta), torta);

    expect(lineas[0].cantidad).toBe(1);
  });

  it("quitar la última unidad elimina la línea", () => {
    const bandeja = crearPlato();

    expect(quitarPlato(agregarPlato([], bandeja), bandeja.id)).toEqual([]);
  });

  it("al refrescar el menú recorta cantidades y quita platos agotados", () => {
    const bandeja = crearPlato();
    const lomo = crearPlato({ id: 8 });
    const lineas = [
      { plato: bandeja, cantidad: 3 },
      { plato: lomo, cantidad: 1 },
    ];
    const menuActual = [
      crearPlato({ porcionesDisponibles: 2 }),
      crearPlato({ id: 8, disponible: false, porcionesDisponibles: 0 }),
    ];

    expect(ajustarAlMenuActual(lineas, menuActual)).toEqual([
      { plato: menuActual[0], cantidad: 2 },
    ]);
  });
});
