import { Link, useParams } from "react-router-dom";
import { TextoDeEscena, tituloDeCapitulo } from "@/entities/escena";
import { ConPeticion } from "@/features/pedir-cambio";
import { useLectura, type CapituloLeido, type EscenaLeida } from "@/shared/api";
import { Esperando } from "@/shared/ui";

// Una escena sola y el enlace a su capitulo tal como llega. SPEC-43: es lectura, asi que se
// titula con su capitulo -«Capitulo N · titulo»-, nunca con su id, y no ensena estado ni
// hallazgos (estan en la administracion). Sin capitulo, o mientras llega, sin titulo.
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
          {e.capitulo !== null && <TituloDelCapitulo capitulo={e.capitulo} />}
          <div className="tarjeta">
            <ConPeticion obra={obra} escena={e}><TextoDeEscena escena={e} /></ConPeticion>
          </div>
        </main>
      )}
    </Esperando>
  );
}

function TituloDelCapitulo({ capitulo }: { capitulo: string }) {
  const lectura = useLectura((c) => c.capitulo(capitulo), `capitulo:${capitulo}`);
  if (lectura.estado !== "listo") return null;
  return <h1>{tituloDeCapitulo(lectura.datos as CapituloLeido)}</h1>;
}
