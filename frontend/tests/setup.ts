// SPEC-22 NF-01: las pruebas del frontend no arrancan un backend. El fetch global se
// sustituye por uno que falla si alguien lo llama: una prueba que necesite datos se los
// inyecta al cliente, derivados del congelado (NF-04).
import "@testing-library/jest-dom/vitest";

export const MENSAJE_FETCH =
  "una prueba del frontend ha llamado a fetch sin inyectarlo: NF-01 prohibe hablar con un backend";

globalThis.fetch = (() => {
  throw new Error(MENSAJE_FETCH);
}) as typeof fetch;
