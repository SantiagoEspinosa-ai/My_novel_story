// PLAN-22 E11 (DP-3): todas las rutas del cliente van bajo /api, que es lo unico que el
// proxy de Vite manda a uvicorn. Una ruta sin el prefijo iria al servidor de Vite.
import { crearCliente, motivoDelError } from "./cliente";

describe("cliente", () => {
  it("todas las rutas van bajo /api", async () => {
    const pedidas: string[] = [];
    const cliente = crearCliente(async (url: string) => {
      pedidas.push(url);
      return new Response("{}", { status: 200 });
    });
    const metodos = Object.keys(cliente) as (keyof typeof cliente)[];
    expect(metodos.length).toBeGreaterThanOrEqual(4);
    for (const m of metodos) {
      await (cliente[m] as (...a: unknown[]) => Promise<unknown>)("x-1", 1, "x-2");
    }
    expect(pedidas).toHaveLength(metodos.length);
    for (const url of pedidas) expect(url.startsWith("/api/")).toBe(true);
  });

  it("un error de la API llega con su codigo y no como datos", async () => {
    const cliente = crearCliente(async () => new Response('{"detail":"no"}', { status: 404 }));
    await expect(cliente.indice("x")).rejects.toMatchObject({ estado: 404 });
  });

  it("pedir un cambio es un POST con la peticion en JSON, y proponerlo tambien", async () => {
    const vistas: { url: string; init?: RequestInit }[] = [];
    const cliente = crearCliente(async (url: string, init?: RequestInit) => {
      vistas.push({ url, init });
      return new Response("{}", { status: 200 });
    });
    const peticion = { clase: "hecho" as const, hecho: "hec-1", enunciado_nuevo: "otro",
      texto: "palabras" };
    await cliente.proponerCambio("obra-1", peticion);
    await cliente.pedirCambio("obra-1", { ...peticion, capitulos_propuestos: ["cap-1"] });
    expect(vistas.map((v) => [v.url, v.init?.method])).toEqual([
      ["/api/obras/obra-1/cambios/propuesta", "POST"], ["/api/obras/obra-1/cambios", "POST"]]);
    expect(JSON.parse(String(vistas[0].init?.body))).toEqual(peticion);
  });

  it("el motivo de un 409 es el detail que manda la API", async () => {
    const cliente = crearCliente(async () =>
      new Response('{"detail":"salida sin elegir: falta la medida"}', { status: 409 }));
    const error = await cliente.pedirCambio("x", {
      clase: "hecho", texto: "t", capitulos_propuestos: [] }).catch((e: unknown) => e);
    expect(motivoDelError(error)).toBe("salida sin elegir: falta la medida");
  });
});
