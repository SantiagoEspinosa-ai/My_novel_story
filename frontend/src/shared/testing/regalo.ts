// Datos de prueba **inventados** de la novela regalo en la web (SPEC-33), con la forma del
// congelado: el tipo sale de contrato.ts y tests/regalo.test.ts los valida contra el mismo
// esquema. Viven aparte de fixtures.ts, que es de PLAN-22.
import type {
  Administracion, CapituloEnGeneracion, EventoDeLaHistoria, HistoriaDeObra, ConfirmacionDeGasto, Cuaderno, Estanteria, GeneracionEnVivo, Historial,
  Nombres, TurnoDeEntrevista,
} from "@/shared/api";

export const turnoConAviso: TurnoDeEntrevista = {
  orden: 1,
  respuesta: "Se llama Nerea y cumple 41",
  pregunta: "¿Quién es Nora Quintana?",
  tema: "el nombre vetado «Nora Quintana»",
  falta: ["ocasion"],
  avisos: ["el nombre vetado «Nora Quintana» comparte nombre de pila con «Nora» (mascota)"],
  contradicciones_abiertas: [
    { tipo: "edad_y_genero", descripcion: "el romance pide al menos 12 años" },
  ],
  cuando: "2026-09-24 10:00:00",
  fuera_del_modelo: false,
};

export const turnoSinNada: TurnoDeEntrevista = {
  orden: 2, respuesta: "Es su cumpleaños", pregunta: "¿Algo más?", tema: null,
  falta: [], avisos: [], contradicciones_abiertas: [], cuando: "2026-09-24 10:01:00",
  fuera_del_modelo: false,
};

/** SPEC-34 RF-01: la respuesta a la primera pregunta, escrita en el campo de nombres. */
export const turnoDelNombre: TurnoDeEntrevista = {
  orden: 1, respuesta: "Nerea Salgado",
  pregunta: "Gracias. ¿Cuántos años tiene Nerea? Y si hay más personas o mascotas con nombre que deban salir en la novela, apúntalas en el cuaderno.",
  tema: "edad", falta: ["edad", "ocasion"], avisos: [], contradicciones_abiertas: [],
  cuando: "2026-09-24 09:59:00", fuera_del_modelo: true,
};

export const turnoViejo: TurnoDeEntrevista = {
  orden: 1, respuesta: "Hola", pregunta: "¿Y después?", tema: null,
  falta: null, avisos: null, contradicciones_abiertas: null, cuando: null,
};

// SPEC-35 RF-05, RF-06: lo que el cuaderno sabe y los nombres, siempre los reales.
export const nombresConMascota: Nombres = {
  destinatario: "Nerea Salgado", regalado_por: "Tomás",
  otros: [{ nombre: "Nora", tipo: "mascota", relacion: "su perra", declarado: true }],
  vetados: ["Nora Quintana"],
  avisos: [{ vetado: "Nora Quintana",
    texto: "el nombre vetado «Nora Quintana» comparte nombre de pila con «Nora» (mascota): vetarlo tambien lo quita de la novela" }],
};

export const nombresVacios: Nombres = {
  destinatario: null, regalado_por: null, otros: [], vetados: [], avisos: [],
};

export const cuadernoAMedias: Cuaderno = {
  sabido: [
    { campo: "nombre", etiqueta: "Nombre", valores: ["Nerea Salgado"] },
    { campo: "edad", etiqueta: "Edad", valores: ["41 años"] },
    { campo: "ocasion", etiqueta: "Ocasión", valores: ["cumpleaños"] },
  ],
  falta: ["Género", "Tono", "Extensión de cada capítulo", "Papel en la historia", "Rasgos",
    "Recuerdos", "Premisa", "Título"],
  total: 11, faltan: 8,
  propuesta: { titulo: null, premisa: null, dedicatoria: null },
};

export const cuadernoVacio: Cuaderno = {
  sabido: [], falta: ["Nombre", "Edad", "Ocasión", "Género", "Tono",
    "Extensión de cada capítulo", "Papel en la historia", "Rasgos", "Recuerdos", "Premisa",
    "Título"], total: 11, faltan: 11,
  propuesta: { titulo: null, premisa: null, dedicatoria: null },
};

export const cuadernoCompleto: Cuaderno = {
  sabido: [
    ...cuadernoAMedias.sabido,
    { campo: "genero", etiqueta: "Género", valores: ["aventura"] },
    { campo: "tono", etiqueta: "Tono", valores: ["tierno"] },
    { campo: "extension", etiqueta: "Extensión de cada capítulo",
      valores: ["media: de 1150 a 1350 palabras por capítulo"] },
    { campo: "papel", etiqueta: "Papel en la historia", valores: ["protagonista"] },
    { campo: "rasgo", etiqueta: "Rasgos", valores: ["colecciona faros (imprescindible)"] },
    { campo: "recuerdo", etiqueta: "Recuerdos",
      valores: ["la tarde en que aprendió a nadar (a los 30 años) (imprescindible)"] },
    { campo: "premisa", etiqueta: "Premisa", valores: ["Un faro de papel devuelve a Nerea al mar."] },
    { campo: "titulo", etiqueta: "Título", valores: ["El faro de Nerea"] },
  ],
  falta: [], total: 11, faltan: 0,
  propuesta: { titulo: "El faro de Nerea", premisa: "Un faro de papel devuelve a Nerea al mar.",
    dedicatoria: "Para Nerea, que siempre vuelve." },
};

export const historialAbierto: Historial = {
  obra: "obra-regalo-inventada",
  cerrada: false,
  puede_cerrar: false,
  hechos_propuestos: [{ id: "hp-1", texto: "aprendió a nadar a los 30", estado: "propuesto" }],
  primera_pregunta: "Vamos a preparar una novela de 10 capitulos. ¿Cómo se llama?",
  turnos: [turnoConAviso, turnoSinNada],
  nombres: nombresConMascota,
  cuaderno: cuadernoAMedias,
};

/** Recién creada: sin nombre y sin turnos. La primera respuesta va al campo del nombre. */
export const historialNuevo: Historial = {
  ...historialAbierto, hechos_propuestos: [], turnos: [], nombres: nombresVacios,
  cuaderno: cuadernoVacio,
};

/** Con el nombre ya declarado, fuera del modelo, y la pregunta fija que viene despues. */
export const historialConNombre: Historial = {
  ...historialAbierto, hechos_propuestos: [], turnos: [turnoDelNombre],
  nombres: { ...nombresVacios, destinatario: "Nerea Salgado" },
  cuaderno: { ...cuadernoVacio, sabido: [{ campo: "nombre", etiqueta: "Nombre",
    valores: ["Nerea Salgado"] }], falta: cuadernoVacio.falta.slice(1), faltan: 10 },
};

export const historialListo: Historial = {
  ...historialAbierto,
  puede_cerrar: true,
  hechos_propuestos: [],
  turnos: [...historialAbierto.turnos, {
    orden: 3, respuesta: "Nada más", pregunta: "Perfecto, ¿cerramos la ficha?", tema: null,
    falta: [], avisos: [], contradicciones_abiertas: [], cuando: "2026-09-24 10:02:00",
    fuera_del_modelo: false,
  }],
  nombres: { ...nombresConMascota, avisos: [] },
  cuaderno: cuadernoCompleto,
};

export const historialCerrado: Historial = { ...historialListo, cerrada: true, puede_cerrar: false };

const CRITERIOS = ["continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
  "personalizacion"] as const;

function capitulo(numero: number, cambios: Partial<CapituloEnGeneracion> = {}): CapituloEnGeneracion {
  return { numero, es_el_actual: false, fase: null, motivo: null, desde: null,
    escenas: [{ id: `esc-${numero}`, estado: "planificada" }], notas: [], ...cambios };
}

/**
 * Diez capitulos: el 1 terminado con sus notas -su ultima fase fue `resumiendo`, como deja el
 * pipeline (`F-200`)-, el 2 en curso y editando, y el resto sin empezar.
 */
export const generacionEnCurso: GeneracionEnVivo = {
  obra: "obra-regalo-inventada",
  total_de_capitulos: 10,
  capitulos: [
    capitulo(1, { fase: "resumiendo", desde: "2026-09-24 10:00:00",
      escenas: [{ id: "esc-1", estado: "consolidada" }], notas: CRITERIOS.map(
      (criterio, i) => ({ criterio, nota: i === 4 ? 2 : 4, justificacion: `sobre ${criterio}`,
        instruccion: i === 4 ? "acelera el final" : null, bajo_el_umbral: i === 4 })) }),
    capitulo(2, { es_el_actual: true, fase: "editando", desde: "2026-09-24 10:04:00",
      escenas: [{ id: "esc-2", estado: "generada" }] }),
    ...Array.from({ length: 8 }, (_, i) => capitulo(i + 3)),
  ],
  coste: { generacion: "gen-inventada", usd: 1.25, delegaciones: 7, sin_coste: 0, es_suelo: false },
  titulo: "La casa del faro",
  fase_de_la_obra: "editando",
  motivo_del_fallo: null,
};

/** F-206: planificando, la obra todavia no esta montada y no tiene capitulos. */
export const generacionPlanificando: GeneracionEnVivo = {
  obra: "obra-regalo-inventada", total_de_capitulos: 0, capitulos: [], coste: null,
  titulo: null, fase_de_la_obra: "planificando", motivo_del_fallo: null,
};

/** SPEC-35 RF-13: el lanzamiento fallo antes de la primera fila de progreso. */
export const generacionFallida: GeneracionEnVivo = {
  ...generacionPlanificando, fase_de_la_obra: null,
  motivo_del_fallo: "FaltaEntorno: no se encuentra el ejecutable de Claude Code",
};

/** Parada en el capitulo 3, que es el actual. */
export const generacionParada: GeneracionEnVivo = {
  ...generacionEnCurso,
  capitulos: generacionEnCurso.capitulos.map((c) => c.numero === 2
    ? { ...c, es_el_actual: false, fase: "resumiendo" as const, escenas: [{ id: "esc-2", estado: "consolidada" as const }] }
    : c.numero === 3
      ? { ...c, es_el_actual: true, fase: "parada" as const, motivo: "FalloDeTransporte",
          desde: "2026-09-24 10:05:00", escenas: [{ id: "esc-3", estado: "generada" as const }] }
      : c),
};

export const generacionPublicada: GeneracionEnVivo = {
  ...generacionEnCurso,
  capitulos: generacionEnCurso.capitulos.map((c) => ({ ...c, es_el_actual: false,
    fase: "resumiendo" as const, escenas: c.escenas.map((e) => ({ ...e, estado: "consolidada" as const })) })),
  fase_de_la_obra: "publicada",
};

export const generacionSinPublicar: GeneracionEnVivo = {
  ...generacionPublicada, fase_de_la_obra: "esperando_revision",
};

export const generacionConSuelo: GeneracionEnVivo = {
  ...generacionEnCurso,
  coste: { generacion: "gen-inventada", usd: 1.5, delegaciones: 9, sin_coste: 1, es_suelo: true },
};

export const generacionSinMedir: GeneracionEnVivo = {
  ...generacionEnCurso,
  coste: { generacion: "gen-inventada", usd: null, delegaciones: 2, sin_coste: 2, es_suelo: true },
};

const REFERENCIA = {
  usd: 16.8905, delegaciones: 36,
  fuente: "R1, la novela de ejemplo: libro de gasto y Langfuse (harness/evals/medidas.md)",
};
const POR_QUE = "lo gastado antes de la migracion 18 no tiene coste guardado en la base";

export const confirmacionConUltima: ConfirmacionDeGasto = {
  gastado: { usd: 17.4, delegaciones: 40, sin_coste: 0, es_suelo: true, por_que_es_suelo: POR_QUE },
  techo_usd: 50, alcanzado: false,
  ultima: { generacion: "gen-inventada", usd: 16.95, delegaciones: 37, sin_coste: 1, es_suelo: true },
  referencia: REFERENCIA,
};

export const confirmacionVacia: ConfirmacionDeGasto = {
  gastado: { usd: null, delegaciones: 0, sin_coste: 0, es_suelo: true, por_que_es_suelo: POR_QUE },
  techo_usd: 50, alcanzado: false, ultima: null, referencia: REFERENCIA,
};

export const confirmacionEnElTecho: ConfirmacionDeGasto = {
  ...confirmacionConUltima,
  gastado: { ...confirmacionConUltima.gastado, usd: 51.2 },
  alcanzado: true,
};

export const estanteria: Estanteria = {
  obras: [
    { id: "obra-publicada", titulo: "El mapa de Nerea", dedicatoria: "Para Nerea, que siempre llega.",
      destinatario: "Nerea Salgado", fase: "publicada", entrevista: "ent-1", entrevista_cerrada: true },
    { id: "obra-escribiendose", titulo: "La casa del faro", dedicatoria: null,
      destinatario: "Tomás Ibarra", fase: "escribiendo", entrevista: "ent-2", entrevista_cerrada: true },
    { id: "obra-a-medias", titulo: null, dedicatoria: null, destinatario: null, fase: null,
      entrevista: "ent-3", entrevista_cerrada: false },
    { id: "obra-entregada", titulo: "Un verano en Cádiz", dedicatoria: "A mi hermana.",
      destinatario: null, fase: "publicada", entrevista: null, entrevista_cerrada: null },
  ],
};

/** SPEC-36 RF-03: la administracion. */
export const administracion: Administracion = {
  gastado: { usd: 14.7, delegaciones: 39, sin_coste: 1, es_suelo: true, por_que_es_suelo: POR_QUE },
  techo_usd: 50,
  obras: [
    { id: "obra-publicada", titulo: "El mapa de Nerea", fase: "publicada",
      coste: { generacion: null, usd: 12.3, delegaciones: 30, sin_coste: 0, es_suelo: false },
      hallazgos: { bloqueante: 0, mayor: 1, menor: 0 }, codigo_lean: 0 },
    { id: "obra-escribiendose", titulo: "La casa del faro", fase: "editando",
      coste: { generacion: null, usd: 2.4, delegaciones: 9, sin_coste: 1, es_suelo: true },
      hallazgos: { bloqueante: 0, mayor: 0, menor: 2 }, codigo_lean: null },
    { id: "obra-a-medias", titulo: null, fase: null, coste: null,
      hallazgos: { bloqueante: 0, mayor: 0, menor: 0 }, codigo_lean: null },
  ],
};

// SPEC-37: la historia de una novela. Un evento vacio con lo de cada tipo encima.
function evento(tipo: string, cambios: Partial<EventoDeLaHistoria>): EventoDeLaHistoria {
  return { tipo, cuando: null, version: null, capitulo: null, coste: null, notas: [], escenas: [],
    intentos: null, motivo: null, aprobado: null, origen: null, objeciones: [], ronda: null,
    codigo_lean: null, condiciones: [], peticion: null, capitulos_cambiados: [], ...cambios };
}
const costeDe = (usd: number | null, delegaciones: number, sin_coste = 0) => (
  { generacion: null, usd, delegaciones, sin_coste, es_suelo: sin_coste > 0 });
const seisNotas = (notas: number[]) => CRITERIOS.map((criterio, i) => ({
  criterio, nota: notas[i], justificacion: `sobre ${criterio}`,
  instruccion: notas[i] < 3 ? "acelera el final" : null, bajo_el_umbral: notas[i] < 3 }));

export const historiaDeObra: HistoriaDeObra = {
  obra: "obra-publicada", titulo: "El mapa de Nerea",
  totales: { coste: costeDe(16.89, 36, 1), nota_media: 4.4, paradas: 1, version_vigente: 2 },
  por_agente: [{ agente: "escritor", ...costeDe(9.4, 20) }, { agente: "editor", ...costeDe(4.9, 12, 1) }],
  abiertos: [{ invariante: "INV-26", severidad: "mayor", capitulo: 4, descripcion: "ritmo bajo" }],
  eventos: [
    evento("entrevista", { cuando: "2026-09-24 10:02:00", aprobado: true, coste: costeDe(0.3, 6) }),
    evento("ronda_del_plan", { ronda: 1, aprobado: false, origen: "revisor",
      objeciones: ["el recuerdo de Lisboa no aparece en ningún capítulo"] }),
    evento("ronda_del_plan", { ronda: 2, aprobado: true, origen: "revisor", coste: costeDe(2.1, 4) }),
    evento("capitulo", { cuando: "2026-09-24 10:14:00", version: 1, capitulo: 1, intentos: 1,
      coste: costeDe(1.32, 3), notas: seisNotas([4, 5, 3, 4, 3, 4]),
      escenas: [{ id: "esc-1", estado: "consolidada" }] }),
    evento("capitulo", { cuando: "2026-09-24 10:30:00", version: 1, capitulo: 3, intentos: 3,
      coste: costeDe(1.9, 5), notas: [], escenas: [{ id: "esc-3", estado: "generada" }] }),
    evento("parada", { cuando: "2026-09-24 10:41:00", version: 1, capitulo: 3, intentos: 3,
      motivo: "bloqueante", coste: costeDe(1.9, 5) }),
    evento("ronda_de_la_puerta", { cuando: "2026-09-24 12:40:00", version: 1, ronda: 1,
      aprobado: false, codigo_lean: 2, condiciones: ["INV-28 (obra): sin veredicto"], coste: costeDe(0.4, 1) }),
    evento("ronda_de_la_puerta", { cuando: "2026-09-24 12:52:00", version: 1, ronda: 2,
      aprobado: true, codigo_lean: 0 }),
    evento("version", { cuando: "2026-09-25 09:10:00", version: 2, peticion: "el perro se llama Nala",
      capitulos_cambiados: [4, 5, 6] }),
  ],
  atribucion: "El coste de cada capitulo es una atribucion por el progreso de la obra.",
};

export const FIXTURES_REGALO: Record<string, { esquema: string; datos: unknown }> = {
  turnoConAviso: { esquema: "TurnoDeEntrevistaSalida", datos: turnoConAviso },
  turnoSinNada: { esquema: "TurnoDeEntrevistaSalida", datos: turnoSinNada },
  turnoViejo: { esquema: "TurnoDeEntrevistaSalida", datos: turnoViejo },
  turnoDelNombre: { esquema: "TurnoDeEntrevistaSalida", datos: turnoDelNombre },
  historialAbierto: { esquema: "HistorialSalida", datos: historialAbierto },
  historialNuevo: { esquema: "HistorialSalida", datos: historialNuevo },
  historialConNombre: { esquema: "HistorialSalida", datos: historialConNombre },
  historialListo: { esquema: "HistorialSalida", datos: historialListo },
  historialCerrado: { esquema: "HistorialSalida", datos: historialCerrado },
  generacionEnCurso: { esquema: "GeneracionEnVivo", datos: generacionEnCurso },
  generacionParada: { esquema: "GeneracionEnVivo", datos: generacionParada },
  generacionPlanificando: { esquema: "GeneracionEnVivo", datos: generacionPlanificando },
  generacionFallida: { esquema: "GeneracionEnVivo", datos: generacionFallida },
  generacionPublicada: { esquema: "GeneracionEnVivo", datos: generacionPublicada },
  generacionSinPublicar: { esquema: "GeneracionEnVivo", datos: generacionSinPublicar },
  generacionConSuelo: { esquema: "GeneracionEnVivo", datos: generacionConSuelo },
  generacionSinMedir: { esquema: "GeneracionEnVivo", datos: generacionSinMedir },
  confirmacionConUltima: { esquema: "ConfirmacionDeGasto", datos: confirmacionConUltima },
  confirmacionVacia: { esquema: "ConfirmacionDeGasto", datos: confirmacionVacia },
  confirmacionEnElTecho: { esquema: "ConfirmacionDeGasto", datos: confirmacionEnElTecho },
  estanteria: { esquema: "Estanteria", datos: estanteria },
  administracion: { esquema: "Administracion", datos: administracion },
  historiaDeObra: { esquema: "HistoriaDeObra", datos: historiaDeObra },
};

type Respuesta = { estado?: number; cuerpo: unknown };

/**
 * Un fetch doble con metodo: `{"POST /api/x": [r1, r2]}` devuelve r1 y despues r2 (la
 * ultima se repite). Una ruta que no esta devuelve 404. Apunta lo pedido, con su cuerpo,
 * para poder comprobar que la pagina pidio lo que tenia que pedir.
 */
export function fetchConMetodo(rutas: Record<string, Respuesta[]>) {
  const pedidas: { clave: string; cuerpo: unknown }[] = [];
  const vistas: Record<string, number> = {};
  const fetch = async (url: string, init?: RequestInit) => {
    const clave = `${init?.method ?? "GET"} ${url}`;
    pedidas.push({ clave, cuerpo: init?.body ? JSON.parse(String(init.body)) : undefined });
    const lista = rutas[clave];
    if (!lista) return new Response(JSON.stringify({ detail: "no existe" }), { status: 404 });
    const n = vistas[clave] ?? 0;
    vistas[clave] = n + 1;
    const r = lista[Math.min(n, lista.length - 1)];
    return new Response(JSON.stringify(r.cuerpo), {
      status: r.estado ?? 200, headers: { "Content-Type": "application/json" },
    });
  };
  return { fetch, pedidas };
}
