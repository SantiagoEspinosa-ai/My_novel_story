import type { ObraEnLaAdministracion } from "@/shared/api";

export type Coste = ObraEnLaAdministracion["coste"];

export function euros(n: number) {
  return `${n.toFixed(2).replace(".", ",")} USD`;
}

/** Un coste tal como llega: sin medir si no se midio, y «como minimo» si es un suelo. */
export function usd(c: Coste) {
  if (!c) return null;
  const cifra = c.usd === null ? "sin medir" : euros(c.usd);
  return <>{cifra}{c.es_suelo && c.usd !== null ? " (como mínimo)" : ""}</>;
}
