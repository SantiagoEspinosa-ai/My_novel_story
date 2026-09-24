import type { CosteDeLaGeneracion } from "@/shared/api";

// El coste en vivo, discreto (SPEC-33 RF-19, RF-20). Sube con cada delegacion porque la
// pagina vuelve a pedir la generacion. Lo que no se midio dice «sin medir», nunca 0,00; y
// si alguna delegacion no trajo coste, la marca de suelo va junto a la cifra, no en una nota.
export function CosteEnVivo({ coste }: { coste: CosteDeLaGeneracion | null }) {
  if (!coste) {
    return <p className="coste" data-testid="coste"><span className="sin-dato">coste sin medir</span></p>;
  }
  const cifra = coste.usd === null ? null : coste.usd.toFixed(2).replace(".", ",");
  return (
    <p className="coste" data-testid="coste" aria-live="polite">
      {cifra === null
        ? <span className="sin-dato">sin medir</span>
        : <strong className="coste__cifra">{cifra} USD</strong>}
      {coste.es_suelo && cifra !== null && (
        <span className="coste__suelo">
          como mínimo: {coste.sin_coste} sin coste medido
        </span>
      )}
      <span className="coste__delegaciones">{coste.delegaciones} delegaciones</span>
    </p>
  );
}
