import { ENTREVISTADORA } from "@/shared/config";

// SPEC-35 RF-04: la entrevistadora, con nombre y cara. La cara es una inicial dibujada con CSS,
// sin imagen; el nombre sale de la configuracion. El agente no cambia: lo presenta la web.
export function Entrevistadora() {
  return (
    <span className="entrevistadora">
      <span className="entrevistadora__cara" aria-hidden="true">
        {ENTREVISTADORA.nombre.charAt(0)}
      </span>
      <span className="entrevistadora__nombre">{ENTREVISTADORA.nombre}</span>
    </span>
  );
}
