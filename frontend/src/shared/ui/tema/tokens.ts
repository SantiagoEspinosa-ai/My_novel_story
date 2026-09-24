// La identidad visual de la lectura web (SPEC-22 RF-59), en UN solo sitio.
//
// ============================================================================================
//  PALETA PROVISIONAL. No es la de Qaracter: el autor todavia no la ha pasado.
//  Cuando llegue, se cambian los valores de PALETA (y, si hace falta, TIPOGRAFIA) en este
//  fichero y en ningun otro. tema.test.ts comprueba que ningun fichero de src fuera de
//  shared/ui/tema escribe un color, y que texto y fondo mantienen contraste AA (4.5:1).
// ============================================================================================

export const PALETA_ES_PROVISIONAL = true;

const PALETA = {
  tinta: "#1b2238", // azul noche: texto principal y cabecera
  tintaSuave: "#4a5270",
  papel: "#f7f3ec", // fondo calido, de libro
  superficie: "#ffffff",
  linea: "#e3dccf",
  acento: "#a8321f", // coral oscuro: llamadas a la accion
  acentoSuave: "#f6e2dc",
  dorado: "#8a6414", // detalles de portada
  sobreOscuro: "#ffffff",
};

export const COLORES = {
  fondo: PALETA.papel,
  superficie: PALETA.superficie,
  texto: PALETA.tinta,
  textoSuave: PALETA.tintaSuave,
  linea: PALETA.linea,
  acento: PALETA.acento,
  acentoSuave: PALETA.acentoSuave,
  sobreAcento: PALETA.sobreOscuro,
  enlace: PALETA.acento,
  cabecera: PALETA.tinta,
  sobreCabecera: PALETA.sobreOscuro,
  detalle: PALETA.dorado,
};

export const TIPOGRAFIA = {
  // Provisional tambien: una serif con caracter para leer y una sans para la interfaz.
  lectura: '"Literata", "Iowan Old Style", Georgia, serif',
  titulos: '"Fraunces", "Literata", Georgia, serif',
  interfaz: '"Inter", "Segoe UI", system-ui, sans-serif',
  tamanoBase: "18px",
  alturaDeLinea: "1.65",
};

export const ESPACIADO = { xs: "4px", s: "8px", m: "16px", l: "24px", xl: "40px", xxl: "72px" };
export const RADIOS = { s: "6px", m: "12px", l: "20px", pildora: "999px" };
export const SOMBRAS = {
  suave: "0 1px 2px rgba(27, 34, 56, 0.06), 0 2px 8px rgba(27, 34, 56, 0.06)",
  media: "0 4px 18px rgba(27, 34, 56, 0.10)",
  portada: "0 24px 60px rgba(27, 34, 56, 0.18)",
};

export type Distintivo = { etiqueta: string; fondo: string; texto: string };

// Cada estado lleva color **y** texto: el color solo no lo lee quien no distingue colores.
export const ESTADO_DE_ESCENA: Record<string, Distintivo> = {
  planificada: { etiqueta: "planificada", fondo: "#eceae4", texto: "#45474f" },
  generada: { etiqueta: "generada", fondo: "#e1ebf7", texto: "#1d4f8a" },
  en_verificacion: { etiqueta: "en verificación", fondo: "#ebe4f6", texto: "#553089" },
  rechazada: { etiqueta: "rechazada", fondo: "#f8e0de", texto: "#9a1f15" },
  en_revision: { etiqueta: "en revisión", fondo: "#fbefd6", texto: "#7a4d00" },
  aceptada: { etiqueta: "aceptada", fondo: "#dff1e4", texto: "#1d6b37" },
  aceptada_por_rendicion: { etiqueta: "aceptada por rendición", fondo: "#fde4cc", texto: "#8a3b00" },
  consolidada: { etiqueta: "consolidada", fondo: "#d6efec", texto: "#0f5f58" },
};

export const ESTADO_DE_HALLAZGO: Record<string, Distintivo> = {
  abierto: { etiqueta: "abierto", fondo: "#f8e0de", texto: "#9a1f15" },
  sin_veredicto: { etiqueta: "sin veredicto", fondo: "#ebe4f6", texto: "#553089" },
  resuelto: { etiqueta: "resuelto", fondo: "#dff1e4", texto: "#1d6b37" },
  descartado: { etiqueta: "descartado", fondo: "#eceae4", texto: "#45474f" },
};

export const SEVERIDAD: Record<string, Distintivo> = {
  bloqueante: { etiqueta: "bloqueante", fondo: "#9a1f15", texto: "#ffffff" },
  mayor: { etiqueta: "mayor", fondo: "#fde4cc", texto: "#8a3b00" },
  menor: { etiqueta: "menor", fondo: "#f4efd9", texto: "#5e5207" },
};

export const ESTADO_DE_CAPITULO: Record<string, Distintivo> = {
  abierto: { etiqueta: "capítulo abierto", fondo: "#e1ebf7", texto: "#1d4f8a" },
  cerrado: { etiqueta: "capítulo cerrado", fondo: "#d6efec", texto: "#0f5f58" },
};

// SPEC-22 RF-60: en que punto va una generacion. `parada` y `esperando_revision` avisan.
export const FASE_DE_GENERACION: Record<string, Distintivo> = {
  planificando: { etiqueta: "planificando", fondo: "#ebe4f6", texto: "#553089" },
  revisando_plan: { etiqueta: "revisando el plan", fondo: "#ebe4f6", texto: "#553089" },
  escribiendo: { etiqueta: "escribiendo", fondo: "#e1ebf7", texto: "#1d4f8a" },
  editando: { etiqueta: "editando", fondo: "#e1ebf7", texto: "#1d4f8a" },
  resumiendo: { etiqueta: "resumiendo", fondo: "#e1ebf7", texto: "#1d4f8a" },
  en_la_puerta: { etiqueta: "en la puerta de publicación", fondo: "#fbefd6", texto: "#7a4d00" },
  publicada: { etiqueta: "publicada", fondo: "#dff1e4", texto: "#1d6b37" },
  parada: { etiqueta: "parada", fondo: "#f8e0de", texto: "#9a1f15" },
  esperando_revision: { etiqueta: "esperando revisión", fondo: "#fbefd6", texto: "#7a4d00" },
};

// La peticion de cambio (SPEC-22 RF-48): el estado del trabajo que la atiende. `fallido`
// y `abandonado` no son lo mismo (se sabe que paso / no se sabe si llego a pasar).
export const ESTADO_DE_TRABAJO: Record<string, Distintivo> = {
  en_cola: { etiqueta: "en cola", fondo: "#eceae4", texto: "#45474f" },
  esperando_presupuesto: { etiqueta: "esperando presupuesto", fondo: "#fbefd6", texto: "#7a4d00" },
  en_curso: { etiqueta: "en curso", fondo: "#e1ebf7", texto: "#1d4f8a" },
  terminado: { etiqueta: "terminado", fondo: "#dff1e4", texto: "#1d6b37" },
  fallido: { etiqueta: "fallido", fondo: "#f8e0de", texto: "#9a1f15" },
  abandonado: { etiqueta: "abandonado: no se sabe si llegó a pasar", fondo: "#fde4cc", texto: "#8a3b00" },
  detenido_por_presupuesto: { etiqueta: "detenido por presupuesto", fondo: "#fbefd6", texto: "#7a4d00" },
};

// SPEC-22 RF-54: una escena en una version. `sin_reverificar` es un verde heredado y
// **no se pinta verde**: se pinta como aviso, con su texto.
export const ESTADO_DE_VERIFICACION: Record<string, Distintivo> = {
  verificada: { etiqueta: "verificada en esta versión", fondo: "#dff1e4", texto: "#1d6b37" },
  sin_reverificar: { etiqueta: "sin reverificar: su verde es de otra versión", fondo: "#fbefd6", texto: "#7a4d00" },
  fallida: { etiqueta: "falló al reverificar", fondo: "#f8e0de", texto: "#9a1f15" },
};

// SPEC-22 RF-52: la marca de «cambió», tal como la da el backend capitulo a capitulo.
export const MARCA_DE_CAMBIO: Record<"cambio" | "compartido", Distintivo> = {
  cambio: { etiqueta: "cambió en esta versión", fondo: PALETA.acentoSuave, texto: PALETA.acento },
  compartido: { etiqueta: "igual que en la versión anterior", fondo: "#eceae4", texto: "#45474f" },
};

/** Las variables CSS que usa `estilos.css`. Se inyectan una vez, en `Tema`. */
export function variablesCss(): string {
  const v: Record<string, string> = {};
  for (const [k, x] of Object.entries(COLORES)) v[`--color-${k}`] = x;
  for (const [k, x] of Object.entries(ESPACIADO)) v[`--espacio-${k}`] = x;
  for (const [k, x] of Object.entries(RADIOS)) v[`--radio-${k}`] = x;
  for (const [k, x] of Object.entries(SOMBRAS)) v[`--sombra-${k}`] = x;
  v["--fuente-lectura"] = TIPOGRAFIA.lectura;
  v["--fuente-titulos"] = TIPOGRAFIA.titulos;
  v["--fuente-interfaz"] = TIPOGRAFIA.interfaz;
  v["--tamano-base"] = TIPOGRAFIA.tamanoBase;
  v["--altura-de-linea"] = TIPOGRAFIA.alturaDeLinea;
  return `:root{${Object.entries(v).map(([k, x]) => `${k}:${x}`).join(";")}}`;
}
