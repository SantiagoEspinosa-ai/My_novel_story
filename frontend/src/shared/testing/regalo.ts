// Datos de prueba **inventados** de la novela regalo en la web (SPEC-33), con la forma del
// congelado: el tipo sale de contrato.ts y tests/regalo.test.ts los valida contra el mismo
// esquema. Viven aparte de fixtures.ts, que es de PLAN-22.
import type { Historial, TurnoDeEntrevista } from "@/shared/api";

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
};

export const turnoSinNada: TurnoDeEntrevista = {
  orden: 2, respuesta: "Es su cumpleaños", pregunta: "¿Algo más?", tema: null,
  falta: [], avisos: [], contradicciones_abiertas: [], cuando: "2026-09-24 10:01:00",
};

export const turnoViejo: TurnoDeEntrevista = {
  orden: 1, respuesta: "Hola", pregunta: "¿Y después?", tema: null,
  falta: null, avisos: null, contradicciones_abiertas: null, cuando: null,
};

export const historialAbierto: Historial = {
  obra: "obra-regalo-inventada",
  cerrada: false,
  puede_cerrar: false,
  hechos_propuestos: [{ id: "hp-1", texto: "aprendió a nadar a los 30", estado: "propuesto" }],
  primera_pregunta: "Vamos a preparar una novela de 10 capitulos. ¿Cómo se llama?",
  turnos: [turnoConAviso, turnoSinNada],
};

export const historialListo: Historial = {
  ...historialAbierto,
  puede_cerrar: true,
  hechos_propuestos: [],
  turnos: [...historialAbierto.turnos, {
    orden: 3, respuesta: "Nada más", pregunta: "Perfecto, ¿cerramos la ficha?", tema: null,
    falta: [], avisos: [], contradicciones_abiertas: [], cuando: "2026-09-24 10:02:00",
  }],
};

export const historialCerrado: Historial = { ...historialListo, cerrada: true, puede_cerrar: false };

export const FIXTURES_REGALO: Record<string, { esquema: string; datos: unknown }> = {
  turnoConAviso: { esquema: "TurnoDeEntrevistaSalida", datos: turnoConAviso },
  turnoSinNada: { esquema: "TurnoDeEntrevistaSalida", datos: turnoSinNada },
  turnoViejo: { esquema: "TurnoDeEntrevistaSalida", datos: turnoViejo },
  historialAbierto: { esquema: "HistorialSalida", datos: historialAbierto },
  historialListo: { esquema: "HistorialSalida", datos: historialListo },
  historialCerrado: { esquema: "HistorialSalida", datos: historialCerrado },
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
