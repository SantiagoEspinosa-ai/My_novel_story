// Datos de prueba **inventados**, con la forma del congelado (SPEC-22 NF-04): el tipo sale
// de contrato.ts, generado de contrato/openapi.json, y fixtures.test.ts los valida en
// ejecucion contra el mismo esquema. Toda fixture con capitulos trae al menos dos (NF-05),
// y los ids de capitulo ordenan al reves que su orden de lectura (Regla 11).
import type {
  CapituloLeido, EscenaLeida, Fichas, Indice, ProgresoDeGeneracion,
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
