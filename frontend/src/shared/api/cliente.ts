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
// SPEC-33: la novela regalo en la web.
export type TurnoDeEntrevista = Esquemas["TurnoDeEntrevistaSalida"];
export type Historial = Esquemas["HistorialSalida"];
export type GeneracionEnVivo = Esquemas["GeneracionEnVivo"];
export type CapituloEnGeneracion = Esquemas["CapituloEnGeneracion"];
export type CosteDeLaGeneracion = Esquemas["CosteDeLaGeneracion"];
export type ConfirmacionDeGasto = Esquemas["ConfirmacionDeGasto"];
export type Estanteria = Esquemas["Estanteria"];
export type ObraEnLaEstanteria = Esquemas["ObraEnLaEstanteria"];
export type PdfDisponible = Esquemas["PdfDisponible"];
export type PeticionDeLaVersion = Esquemas["PeticionDeLaVersion"];
// SPEC-34, SPEC-35 RF-05..RF-07: los nombres fuera del modelo y el cuaderno.
export type NombresEntrada = Esquemas["NombresEntrada"];
export type Nombres = Esquemas["NombresSalida"];
export type Cuaderno = Esquemas["CuadernoSalida"];
// SPEC-36 RF-03: la administracion.
export type Administracion = Esquemas["Administracion"];
export type ObraEnLaAdministracion = Esquemas["ObraEnLaAdministracion"];
// SPEC-37: la historia de cada novela.
export type HistoriaDeObra = Esquemas["HistoriaDeObra"];
export type EventoDeLaHistoria = Esquemas["EventoDeLaHistoria"];
// SPEC-38: la matriz por capitulo.
export type MatrizDeObra = Esquemas["MatrizDeObra"];
export type FilaDeLaMatriz = Esquemas["FilaDeLaMatriz"];
// SPEC-39: publicar y reanudar.
export type AccionesDeObra = Esquemas["AccionesDeObra"];

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
  const enviar = <T>(ruta: string, cuerpo?: unknown) => leer<T>(ruta, {
    method: "POST", body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    headers: { "Content-Type": "application/json" },
  });
  const poner = <T>(ruta: string, cuerpo: unknown) => leer<T>(ruta, {
    method: "PUT", body: JSON.stringify(cuerpo), headers: { "Content-Type": "application/json" },
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
    // SPEC-34 RF-01: los nombres, en su campo. No llama a ningun agente: responde al momento.
    declararNombres: (entrevista: string, nombres: NombresEntrada) =>
      poner<unknown>(`/entrevistas/${e(entrevista)}/nombres`, nombres),
    confirmarAviso: (entrevista: string, vetado: string) =>
      enviar<unknown>(`/entrevistas/${e(entrevista)}/avisos/confirmar`, { vetado }),
    generacion: (obra: string) => leer<GeneracionEnVivo>(`/obras/${e(obra)}/generacion`),
    estanteria: () => leer<Estanteria>("/obras"),
    // SPEC-35 RF-12: si hay PDF, sin generarlo. La descarga es un enlace: `urlDelPdf`.
    pdfDisponible: (obra: string) => leer<PdfDisponible>(`/obras/${e(obra)}/pdf/disponible`),
    // SPEC-35 RF-10: las palabras del lector que originaron una version.
    peticionDeLaVersion: (obra: string, numero: number) =>
      leer<PeticionDeLaVersion>(`/obras/${e(obra)}/versiones/${numero}/peticion`),
    gasto: () => leer<ConfirmacionDeGasto>("/generaciones/gasto"),
    administracion: () => leer<Administracion>("/admin/obras"),
    historia: (obra: string) => leer<HistoriaDeObra>(`/admin/obras/${e(obra)}/historia`),
    matriz: (obra: string, version?: number) => leer<MatrizDeObra>(
      `/admin/obras/${e(obra)}/matriz${version === undefined ? "" : `?version=${version}`}`),
    // SPEC-33 RF-11: gasta dinero. Solo lo llama la confirmacion, despues de ensenar las cifras.
    acciones: (obra: string) => leer<AccionesDeObra>(`/obras/${e(obra)}/acciones`),
    // SPEC-39 RF-01: una ronda de la puerta. Gasta una delegacion del Editor.
    publicar: (obra: string) =>
      enviar<{ id_trabajo: string }>(`/obras/${e(obra)}/publicaciones`),
    lanzar: (obra: string) =>
      enviar<{ id_trabajo: string; generacion: string }>(`/obras/${e(obra)}/generaciones`),
  };
}

export type Cliente = ReturnType<typeof crearCliente>;

/**
 * SPEC-35 RF-12: la URL del PDF de una obra, para un enlace de descarga. No es un metodo del
 * cliente porque no pide nada: la descarga la hace el navegador. Vive aqui porque este es el
 * unico sitio que conoce las rutas de la API (VER-106).
 */
export function urlDelPdf(obra: string): string {
  return `${PREFIJO}/obras/${encodeURIComponent(obra)}/pdf`;
}
