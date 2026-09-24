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
export type ProgresoDeGeneracion = Esquemas["ProgresoDeGeneracion"];
export type HechosDeEscena = Esquemas["HechosDeEscena"];
export type PeticionEntrada = Esquemas["PeticionEntrada"];
export type CambioEntrada = Esquemas["CambioEntrada"];
export type Propuesta = Esquemas["PropuestaSalida"];
export type Trabajo = Esquemas["TrabajoSalida"];
export type Versiones = Esquemas["VersionesSalida"];
export type IndiceDeVersion = Esquemas["IndiceDeVersion"];
export type CapituloLeidoDeVersion = Esquemas["CapituloLeidoDeVersion"];
export type TrabajoEncolado = { id_trabajo: string };

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

/** El motivo que da la API al negarse (el `detail` de un 409), o el mensaje del error. */
export function motivoDelError(e: unknown): string {
  if (e instanceof ErrorDeLaApi) {
    const d = e.detalle as { detail?: unknown } | null;
    if (d && typeof d.detail === "string") return d.detail;
    if (d && d.detail !== undefined) return JSON.stringify(d.detail);
  }
  return e instanceof Error ? e.message : String(e);
}

export type Fetch = (entrada: string, init?: RequestInit) => Promise<Response>;

export function crearCliente(fetchInyectado: Fetch) {
  async function leer<T>(ruta: string, init?: RequestInit): Promise<T> {
    const url = PREFIJO + ruta;
    const r = await fetchInyectado(url, {
      ...init, headers: { Accept: "application/json", ...(init?.headers ?? {}) },
    });
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
  const enviar = <T>(ruta: string, cuerpo: unknown) => leer<T>(ruta, {
    method: "POST", body: JSON.stringify(cuerpo),
    headers: { "Content-Type": "application/json" },
  });
  const e = encodeURIComponent;
  return {
    indice: (obra: string) => leer<Indice>(`/obras/${e(obra)}/indice`),
    capitulo: (capitulo: string) => leer<CapituloLeido>(`/capitulos/${e(capitulo)}`),
    escena: (escena: string) => leer<EscenaLeida>(`/escenas/${e(escena)}`),
    fichas: (obra: string) => leer<Fichas>(`/obras/${e(obra)}/fichas`),
    progreso: (obra: string) => leer<ProgresoDeGeneracion>(`/obras/${e(obra)}/progreso`),
    hechosDeEscena: (escena: string) => leer<HechosDeEscena>(`/escenas/${e(escena)}/hechos`),
    versiones: (obra: string) => leer<Versiones>(`/obras/${e(obra)}/versiones`),
    indiceDeVersion: (obra: string, numero: number) =>
      leer<IndiceDeVersion>(`/obras/${e(obra)}/versiones/${numero}/indice`),
    capituloDeVersion: (obra: string, numero: number, capitulo: string) =>
      leer<CapituloLeidoDeVersion>(
        `/obras/${e(obra)}/versiones/${numero}/capitulos/${e(capitulo)}`),
    trabajo: (id: string) => leer<Trabajo>(`/trabajos/${e(id)}`),
    // La peticion de cambio (SPEC-23, PLAN-23 A7). Proponer no toca nada; pedir encola.
    proponerCambio: (obra: string, peticion: PeticionEntrada) =>
      enviar<Propuesta>(`/obras/${e(obra)}/cambios/propuesta`, peticion),
    pedirCambio: (obra: string, cambio: CambioEntrada) =>
      enviar<TrabajoEncolado>(`/obras/${e(obra)}/cambios`, cambio),
  };
}

export type Cliente = ReturnType<typeof crearCliente>;
