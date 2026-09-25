// Configuracion de la interfaz: presentacion, no dominio. El frontend no lee los ficheros
// de configuracion del backend (SPEC-22 RF-56).

/** Pasado este tiempo sin actividad, la barra de progreso lo avisa (SPEC-22 RF-60). */
export const UMBRAL_SIN_ACTIVIDAD_SEGUNDOS = 5 * 60;

/** Cada cuanto se vuelve a pedir el progreso de una generacion. */
export const INTERVALO_DE_PROGRESO_MS = 5000;

/** Cada cuanto se vuelve a pedir el estado de un trabajo encolado (SPEC-22 RF-48). */
export const INTERVALO_DE_TRABAJO_MS = 3000;

/**
 * SPEC-33 cuestion 5: cada cuanto se vuelve a pedir un trabajo de la entrevista y el estado
 * de una generacion en las paginas de la novela regalo. La barra de PLAN-22 sigue con el suyo.
 */
export const INTERVALO_DE_REGALO_MS = 2000;

/**
 * SPEC-35 RF-04 (cuestion 1, v3): la entrevistadora tiene nombre y cara. Es presentacion: el
 * Entrevistador (el agente) no cambia, y el modelo no finge ser nadie. Se cambia aqui.
 */
export const ENTREVISTADORA = { nombre: "Xime" };
