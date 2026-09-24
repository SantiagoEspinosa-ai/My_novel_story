import { Link, useParams } from "react-router-dom";
import { useLectura, type Indice } from "@/shared/api";
import { Esperando } from "@/shared/ui";

// La portada: el titulo y la dedicatoria de la Obra (SPEC-22 RF-46). Sin dedicatoria, solo
// el titulo: no se rellena con nada, porque un relleno se leeria como la dedicatoria.
export function PaginaPortada() {
  const { obra = "" } = useParams();
  const lectura = useLectura((c) => c.indice(obra), obra);
  return <Esperando lectura={lectura}>{(i: Indice) => <Portada indice={i} />}</Esperando>;
}

function Portada({ indice }: { indice: Indice }) {
  return (
    <main className="portada">
      <h1>{indice.titulo}</h1>
      {indice.dedicatoria !== null && (
        <p data-testid="dedicatoria" className="dedicatoria" style={{ whiteSpace: "pre-wrap" }}>
          {indice.dedicatoria}
        </p>
      )}
      <nav>
        <Link to={`/obras/${encodeURIComponent(indice.id)}/indice`}>Índice</Link>
        {" · "}
        <Link to={`/obras/${encodeURIComponent(indice.id)}/fichas`}>Fichas</Link>
      </nav>
    </main>
  );
}
