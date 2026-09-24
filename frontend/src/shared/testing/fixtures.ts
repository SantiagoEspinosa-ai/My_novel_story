// Datos de prueba **inventados**, con la forma del congelado (SPEC-22 NF-04): el tipo sale
// de contrato.ts, generado de contrato/openapi.json, y fixtures.test.ts los valida en
// ejecucion contra el mismo esquema. Toda fixture con capitulos trae al menos dos (NF-05),
// y los ids de capitulo ordenan al reves que su orden de lectura (Regla 11).
import type {
  CapituloLeido, CapituloLeidoDeVersion, EscenaLeida, Fichas, HechosDeEscena, Indice,
  IndiceDeVersion, ProgresoDeGeneracion, Propuesta, Trabajo, Versiones,
} from "@/shared/api";

const TEXTO = "Primer texto  inventado,\ncon dos espacios y un salto.\n";

export const escenaConsolidada: EscenaLeida = {
  id: "esc-b1",
  capitulo: "cap-b",
  estado: "consolidada",
  se_acepto_rindiendose: false,
  hallazgos_abiertos: [],
  borrador: { version: 1, texto: TEXTO },
  personajes_presentes: ["per-uno", "per-dos"],
};

export const escenaRendida: EscenaLeida = {
  id: "esc-b2",
  capitulo: "cap-b",
  estado: "aceptada_por_rendicion",
  se_acepto_rindiendose: true,
  hallazgos_abiertos: [
    { invariante: "INV-17", verificador: "regla", severidad: "mayor", estado: "abierto",
      descripcion: "fuera de rango (inventado)" },
  ],
  borrador: { version: 3, texto: "Texto rendido inventado." },
  personajes_presentes: ["per-uno"],
};

export const escenaSinVeredicto: EscenaLeida = {
  id: "esc-a1",
  capitulo: "cap-a",
  estado: "generada",
  se_acepto_rindiendose: false,
  hallazgos_abiertos: [
    { invariante: "INV-27", verificador: "juez_llm", severidad: "mayor",
      estado: "sin_veredicto", descripcion: "el juez no contesto (inventado)" },
  ],
  borrador: { version: 1, texto: "Texto generado inventado." },
  personajes_presentes: null,
};

export const escenaPlanificada: EscenaLeida = {
  id: "esc-a2",
  capitulo: "cap-a",
  estado: "planificada",
  se_acepto_rindiendose: false,
  hallazgos_abiertos: [],
  borrador: null,
  personajes_presentes: [],
};

const delIndice = ({ borrador: _b, personajes_presentes: _p, ...resto }: EscenaLeida) => resto;

export const indice: Indice = {
  id: "obra-inventada",
  titulo: "Titulo inventado",
  dedicatoria: "Para nadie real",
  capitulos: [
    { id: "cap-b", orden: 1, estado: "abierto",
      escenas: [delIndice(escenaConsolidada), delIndice(escenaRendida)] },
    { id: "cap-a", orden: 2, estado: "abierto",
      escenas: [delIndice(escenaSinVeredicto), delIndice(escenaPlanificada)] },
  ],
};

export const indiceSinDedicatoria: Indice = { ...indice, dedicatoria: null };

export const capituloB: CapituloLeido = {
  id: "cap-b", orden: 1, estado: "abierto", escenas: [escenaConsolidada, escenaRendida],
};

export const capituloA: CapituloLeido = {
  id: "cap-a", orden: 2, estado: "abierto", escenas: [escenaSinVeredicto, escenaPlanificada],
};

export const fichas: Fichas = {
  personajes: [
    { id: "per-uno", nombre_canonico: "Nombre inventado", alias: ["Alias inventado"],
      rol_dramatico: "protagonista", estado_vital: "vivo",
      capitulos_donde_aparece: [{ id: "cap-b", orden: 1 }, { id: "cap-a", orden: 2 }] },
    { id: "per-dos", nombre_canonico: null, alias: null, rol_dramatico: null,
      estado_vital: "desaparecido", capitulos_donde_aparece: null },
  ],
  lugares: [
    { id: "lug-faro", nombre: "Faro inventado", atmosfera: null,
      capitulos_donde_aparece: [{ id: "cap-a", orden: 2 }] },
    { id: "lug-casa", nombre: null, atmosfera: null, capitulos_donde_aparece: [] },
  ],
};

export const progresoEscribiendo: ProgresoDeGeneracion = {
  obra: "obra-inventada", fase: "escribiendo", capitulo: 3, total_de_capitulos: 10,
  motivo: null, desde: "2026-09-24 10:00:00", ultima_actividad: "2026-09-24 10:02:00",
  segundos_desde_la_ultima_actividad: 40,
};

// --- La peticion de cambio (PLAN-22 E16) ------------------------------------------------

export const hechosDeB1: HechosDeEscena = {
  escena: "esc-b1",
  hechos_que_usa: [
    { id: "hec-faro", enunciado: "El faro existe (inventado)." },
    { id: "hec-llave", enunciado: "La llave abre el faro (inventado)." },
  ],
};

export const hechosVacios: HechosDeEscena = { escena: "esc-a2", hechos_que_usa: [] };

// Los literales de SPEC-23 D-3, tal como los devuelve el backend.
const PROMESA = "reescribimos lo que dependía de esto";
const PUNTO_CIEGO = "si la prosa contradice sin que el delta lo declare, no se toca";

export const propuestaConSalida: Propuesta = {
  obra: "obra-inventada", version_de_partida: 1, clase: "hecho",
  capitulos: { cascada: ["cap-b", "cap-a"], selectiva: ["cap-b"] },
  salida: "cascada", capitulos_propuestos: ["cap-b", "cap-a"], motivo: null,
  promesa: PROMESA, punto_ciego: PUNTO_CIEGO,
};

export const propuestaSinSalida: Propuesta = {
  ...propuestaConSalida, salida: null, capitulos_propuestos: null,
  motivo: "salida sin elegir: falta la medida",
};

export const trabajoEnCola: Trabajo = {
  id: "trab-1", tipo: "regenerar_obra", estado: "en_cola", resultado: null, motivo: null,
  volvio_tras_abandono: false,
};

export const trabajoFallido: Trabajo = {
  ...trabajoEnCola, estado: "fallido",
  motivo: "la rama de la salida cascada no existe todavia (inventado)",
};

export const trabajoTerminado: Trabajo = {
  ...trabajoEnCola, estado: "terminado", resultado: { version: 2 },
};

// --- Dos versiones (PLAN-22 E17): la 2 sustituye el capitulo 2 y comparte el 1 -----------

export const versiones: Versiones = {
  obra: "obra-inventada",
  versiones: [
    { numero: 1, anterior: null, peticion: null, commit: "abc1234",
      creada_en: "2026-09-24 10:00:00" },
    { numero: 2, anterior: 1, peticion: 1, commit: "def5678",
      creada_en: "2026-09-24 11:00:00" },
  ],
};

const conVerificacion = (e: Omit<EscenaLeida, "borrador" | "personajes_presentes">,
  estado_de_verificacion: "verificada" | "sin_reverificar" | "fallida") =>
  ({ ...e, estado_de_verificacion });

export const indiceV2: IndiceDeVersion = {
  ...indice, numero: 2, anterior: 1,
  capitulos: [
    { id: "cap-b", orden: 1, estado: "abierto", compartido: true,
      escenas: [conVerificacion(delIndice(escenaConsolidada), "sin_reverificar"),
        conVerificacion(delIndice(escenaRendida), "sin_reverificar")] },
    { id: "cap-a-v2", orden: 2, estado: "abierto", compartido: false,
      escenas: [conVerificacion({ ...delIndice(escenaSinVeredicto), id: "esc-a1-v2",
        capitulo: "cap-a-v2" }, "verificada")] },
  ],
};

export const indiceV1: IndiceDeVersion = {
  ...indice, numero: 1, anterior: null,
  capitulos: indice.capitulos.map((c) => ({
    ...c, compartido: null,
    escenas: c.escenas.map((e) => conVerificacion(e, "verificada")),
  })),
};

export const capituloAV1: CapituloLeidoDeVersion = {
  ...capituloA, numero: 1, compartido: null,
  escenas: capituloA.escenas.map((e) => ({ ...e, estado_de_verificacion: "verificada" })),
};

export const FIXTURES: Record<string, { esquema: string; datos: unknown }> = {
  indice: { esquema: "Indice", datos: indice },
  indiceSinDedicatoria: { esquema: "Indice", datos: indiceSinDedicatoria },
  capituloB: { esquema: "CapituloLeido", datos: capituloB },
  capituloA: { esquema: "CapituloLeido", datos: capituloA },
  escenaConsolidada: { esquema: "EscenaLeida", datos: escenaConsolidada },
  escenaRendida: { esquema: "EscenaLeida", datos: escenaRendida },
  escenaSinVeredicto: { esquema: "EscenaLeida", datos: escenaSinVeredicto },
  escenaPlanificada: { esquema: "EscenaLeida", datos: escenaPlanificada },
  fichas: { esquema: "Fichas", datos: fichas },
  progresoEscribiendo: { esquema: "ProgresoDeGeneracion", datos: progresoEscribiendo },
  hechosDeB1: { esquema: "HechosDeEscena", datos: hechosDeB1 },
  hechosVacios: { esquema: "HechosDeEscena", datos: hechosVacios },
  propuestaConSalida: { esquema: "PropuestaSalida", datos: propuestaConSalida },
  propuestaSinSalida: { esquema: "PropuestaSalida", datos: propuestaSinSalida },
  trabajoEnCola: { esquema: "TrabajoSalida", datos: trabajoEnCola },
  trabajoFallido: { esquema: "TrabajoSalida", datos: trabajoFallido },
  trabajoTerminado: { esquema: "TrabajoSalida", datos: trabajoTerminado },
  versiones: { esquema: "VersionesSalida", datos: versiones },
  indiceV2: { esquema: "IndiceDeVersion", datos: indiceV2 },
  indiceV1: { esquema: "IndiceDeVersion", datos: indiceV1 },
  capituloAV1: { esquema: "CapituloLeidoDeVersion", datos: capituloAV1 },
};

/** Un `fetch` que contesta con fixtures por ruta, para inyectarlo al cliente. */
export function fetchDeFixtures(rutas: Record<string, unknown>) {
  return async (url: string) => {
    if (!(url in rutas)) {
      return new Response(JSON.stringify({ detail: "no existe" }), { status: 404 });
    }
    return new Response(JSON.stringify(rutas[url]), {
      status: 200, headers: { "Content-Type": "application/json" },
    });
  };
}

export type LlamadaVista = { metodo: string; url: string; cuerpo: unknown };
type Respuesta = { estado: number; cuerpo: unknown };

/** Un `fetch` que contesta por metodo y ruta ("POST /api/..." o, para GET, la ruta sola)
 * y apunta cada llamada con su cuerpo. Una lista de respuestas se sirve en orden y repite
 * la ultima: es lo que hace falta para seguir un trabajo que cambia de estado. */
export function fetchConMetodos(rutas: Record<string, unknown | Respuesta | Respuesta[]>) {
  const llamadas: LlamadaVista[] = [];
  const servidas: Record<string, number> = {};
  const fetch = async (url: string, init?: RequestInit) => {
    const metodo = init?.method ?? "GET";
    llamadas.push({ metodo, url, cuerpo: init?.body ? JSON.parse(String(init.body)) : null });
    const clave = metodo === "GET" && url in rutas ? url : `${metodo} ${url}`;
    if (!(clave in rutas)) {
      return new Response(JSON.stringify({ detail: "no existe" }), { status: 404 });
    }
    let r = rutas[clave] as unknown;
    if (Array.isArray(r) && r.length && typeof r[0] === "object" && r[0] && "estado" in r[0]) {
      const n = servidas[clave] ?? 0;
      servidas[clave] = n + 1;
      r = r[Math.min(n, r.length - 1)];
    }
    const { estado, cuerpo } = (r && typeof r === "object" && "estado" in r && "cuerpo" in r)
      ? r as Respuesta : { estado: 200, cuerpo: r };
    return new Response(JSON.stringify(cuerpo), {
      status: estado, headers: { "Content-Type": "application/json" },
    });
  };
  return { fetch, llamadas };
}
