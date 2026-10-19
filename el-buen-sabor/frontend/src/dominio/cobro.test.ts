import { describe, expect, it } from "vitest";
import { montosSugeridos, planearCobro } from "./cobro";

describe("planear el cobro", () => {
  it("en efectivo calcula el cambio", () => {
    const plan = planearCobro({ modo: "EFECTIVO", total: 80_000, recibido: 100_000, parteEfectivo: 0 });
    expect(plan.pagos).toEqual([{ metodo: "EFECTIVO", monto: 80_000, montoRecibido: 100_000 }]);
    expect(plan.cambio).toBe(20_000);
    expect(plan.problema).toBeNull();
  });

  it("avisa si el efectivo no alcanza", () => {
    const plan = planearCobro({ modo: "EFECTIVO", total: 80_000, recibido: 50_000, parteEfectivo: 0 });
    expect(plan.problema).toMatch(/Faltan/);
  });

  it("divide entre efectivo y tarjeta", () => {
    const plan = planearCobro({ modo: "MIXTO", total: 80_000, recibido: 50_000, parteEfectivo: 30_000 });
    expect(plan.pagos).toEqual([
      { metodo: "EFECTIVO", monto: 30_000, montoRecibido: 50_000 },
      { metodo: "TARJETA", monto: 50_000 },
    ]);
    expect(plan.cambio).toBe(20_000);
  });

  it("en mixto la parte en efectivo no puede ser todo el total", () => {
    const plan = planearCobro({ modo: "MIXTO", total: 80_000, recibido: 80_000, parteEfectivo: 80_000 });
    expect(plan.problema).not.toBeNull();
  });

  it("sugiere billetes para cobrar rápido", () => {
    expect(montosSugeridos(80_000)).toEqual([80_000, 100_000]);
    expect(montosSugeridos(43_500)).toEqual([43_500, 50_000, 60_000, 100_000]);
  });
});
