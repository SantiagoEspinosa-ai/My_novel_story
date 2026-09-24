// El unico sitio del frontend que habla con la red (VER-106). Recibe `fetch` inyectado:
// en las pruebas se le da uno que devuelve fixtures del congelado, y el global falla
// (tests/setup.ts). Todas las rutas van bajo /api, que el proxy de Vite manda a uvicorn.
import type { components } from "./contrato";

export type Esquemas = components["schemas"];
export type Indice = Esquemas["Indice"];
export type CapituloLeido = Esquemas["CapituloLeido"];
export type EscenaLeida = Esquemas["EscenaLeida"];
export type Fichas = Esquemas["Fichas"];
export type Hallazgo = Esquemas["HallazgoAbierto"];

export const PREFIJO = "/api";

export class ErrorDeLaApi extends Error {
  constructor(
    public readonly estado: number,
    public readonly ruta: string,
    public readonly detalle: unknown,
  ) {
    super(`la API contesto ${estado} en ${ruta}`);
  }
}

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>;

export function crearCliente(fetchInyectado: Fetch) {
  async function leer<T>(ruta: string): Promise<T> {
    const url = PREFIJO + ruta;
    const r = await fetchInyectado(url, { headers: { Accept: "application/json" } });
    if (!r.ok) {
      let detalle: unknown = null;
      try {
        detalle = await r.json();
      } catch {
        detalle = null;
      }
      throw new ErrorDeLaApi(r.status, url, detalle);
    }
    return (await r.json()) as T;
  }
  const e = encodeURIComponent;
  return {
    indice: (obra: string) => leer<Indice>(`/obras/${e(obra)}/indice`),
    capitulo: (capitulo: string) => leer<CapituloLeido>(`/capitulos/${e(capitulo)}`),
    escena: (escena: string) => leer<EscenaLeida>(`/escenas/${e(escena)}`),
    fichas: (obra: string) => leer<Fichas>(`/obras/${e(obra)}/fichas`),
  };
}

export type Cliente = ReturnType<typeof crearCliente>;
