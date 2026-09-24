// PLAN-22 E11 (DP-3): todas las rutas del cliente van bajo /api, que es lo unico que el
// proxy de Vite manda a uvicorn. Una ruta sin el prefijo iria al servidor de Vite.
import { crearCliente } from "./cliente";

describe("cliente", () => {
  it("todas las rutas van bajo /api", async () => {
    const pedidas: string[] = [];
    const cliente = crearCliente(async (url: string) => {
      pedidas.push(url);
      return new Response("{}", { status: 200 });
    });
    const metodos = Object.keys(cliente) as (keyof typeof cliente)[];
    expect(metodos.length).toBeGreaterThanOrEqual(4);
    // PLAN-33: algunos metodos piden dos argumentos; con uno basta para ver la ruta.
    for (const m of metodos) await (cliente[m] as (a: string) => Promise<unknown>)("x-1");
    expect(pedidas).toHaveLength(metodos.length);
    for (const url of pedidas) expect(url.startsWith("/api/")).toBe(true);
  });

  it("un error de la API llega con su codigo y no como datos", async () => {
    const cliente = crearCliente(async () => new Response('{"detail":"no"}', { status: 404 }));
    await expect(cliente.indice("x")).rejects.toMatchObject({ estado: 404 });
  });
});
