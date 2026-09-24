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
        <main className="contenido vista-escena">
          <nav className="migas">
            <Link to={`/obras/${encodeURIComponent(obra)}/indice`}>Índice</Link>
            {e.capitulo !== null && <>{" · "}
              <Link to={`/obras/${encodeURIComponent(obra)}/capitulos/${encodeURIComponent(e.capitulo)}`}>
                Su capítulo
              </Link></>}
          </nav>
          <h1>{e.id}</h1>
          <div className="tarjeta"><EscenaConEstado escena={e} /></div>
        </main>
      )}
    </Esperando>
  );
}
