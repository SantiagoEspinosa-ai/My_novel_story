// Configuracion de la interfaz: presentacion, no dominio. El frontend no lee los ficheros
// de configuracion del backend (SPEC-22 RF-56).

/** Pasado este tiempo sin actividad, la barra de progreso lo avisa (SPEC-22 RF-60). */
export const UMBRAL_SIN_ACTIVIDAD_SEGUNDOS = 5 * 60;

/** Cada cuanto se vuelve a pedir el progreso de una generacion. */
export const INTERVALO_DE_PROGRESO_MS = 5000;
