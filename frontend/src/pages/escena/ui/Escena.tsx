import { Link, useParams } from "react-router-dom";
import { EscenaConEstado } from "@/entities/escena";
import { useLectura, type EscenaLeida } from "@/shared/api";
import { Esperando } from "@/shared/ui";

// Una escena sola, con su estado y sus hallazgos, y el enlace a su capitulo tal como llega.
export function PaginaEscena() {
  const { obra = "", escena = "" } = useParams();
  const lectura = useLectura((c) => c.escena(escena), escena);
  return (
    <Esperando lectura={lectura}>
      {(e: EscenaLeida) => (
        <main className="vista-escena">
          <nav>
            <Link to={`/obras/${encodeURIComponent(obra)}/indice`}>Índice</Link>
            {e.capitulo !== null && <>{" · "}
              <Link to={`/obras/${encodeURIComponent(obra)}/capitulos/${encodeURIComponent(e.capitulo)}`}>
                Su capítulo
              </Link></>}
          </nav>
          <h1>{e.id}</h1>
          <EscenaConEstado escena={e} />
        </main>
      )}
    </Esperando>
  );
}
