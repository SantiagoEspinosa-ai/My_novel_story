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
// SPEC-33: la novela regalo en la web.
export type TurnoDeEntrevista = Esquemas["TurnoDeEntrevistaSalida"];
export type Historial = Esquemas["HistorialSalida"];
/**
 * Lo que la pagina lee de `GET /trabajos/{id}`. En esta rama el congelado no lo tipa; lo tipa
 * `PLAN-22` E14 (`TrabajoSalida`), y al fusionarlo este tipo pasa a salir de alli.
 */
export type Trabajo = {
  estado: "en_cola" | "esperando_presupuesto" | "en_curso" | "terminado" | "fallido"
    | "abandonado" | "detenido_por_presupuesto";
  motivo: string | null;
};

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
  async function enviar<T>(ruta: string, cuerpo?: unknown): Promise<T> {
    const url = PREFIJO + ruta;
    const r = await fetchInyectado(url, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    });
    let datos: unknown = null;
    try {
      datos = await r.json();
    } catch {
      datos = null;
    }
    if (!r.ok) throw new ErrorDeLaApi(r.status, url, datos);
    return datos as T;
  }
  const e = encodeURIComponent;
  return {
    indice: (obra: string) => leer<Indice>(`/obras/${e(obra)}/indice`),
    capitulo: (capitulo: string) => leer<CapituloLeido>(`/capitulos/${e(capitulo)}`),
    escena: (escena: string) => leer<EscenaLeida>(`/escenas/${e(escena)}`),
    fichas: (obra: string) => leer<Fichas>(`/obras/${e(obra)}/fichas`),
    progreso: (obra: string) => leer<ProgresoDeGeneracion>(`/obras/${e(obra)}/progreso`),
    // SPEC-33: la entrevista en la web. Las respuestas de PLAN-25 no estan tipadas en el
    // congelado (RF-57 no deja pasar su campo `contradicciones`): la pagina lee el historial.
    crearEntrevista: () => enviar<{ id: string; obra: string }>("/entrevistas"),
    historial: (entrevista: string) =>
      leer<Historial>(`/entrevistas/${e(entrevista)}/turnos`),
    responder: (entrevista: string, respuesta: string) =>
      enviar<{ id_trabajo: string }>(`/entrevistas/${e(entrevista)}/turnos`, { respuesta }),
    confirmarHecho: (entrevista: string, hecho: string) =>
      enviar<unknown>(`/entrevistas/${e(entrevista)}/hechos/${e(hecho)}/confirmar`),
    descartarHecho: (entrevista: string, hecho: string) =>
      enviar<unknown>(`/entrevistas/${e(entrevista)}/hechos/${e(hecho)}/descartar`),
    cerrarEntrevista: (entrevista: string) =>
      enviar<unknown>(`/entrevistas/${e(entrevista)}/cerrar`),
    trabajo: (id: string) => leer<Trabajo>(`/trabajos/${e(id)}`),
  };
}

export type Cliente = ReturnType<typeof crearCliente>;
