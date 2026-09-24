import { Link, useParams } from "react-router-dom";
import { EscenaConEstado } from "@/entities/escena";
import { useLectura, type Indice } from "@/shared/api";
import { Esperando } from "@/shared/ui";

// El indice pinta **en el orden en que llega** (SPEC-22 RF-38): no ordena, no agrupa y no
// deduce a que capitulo va cada escena. «Capitulo N» es el `orden` que trae la respuesta.
// No hay partes: la API no las trae porque la base no las tiene.
export function PaginaIndice() {
  const { obra = "" } = useParams();
  const lectura = useLectura((c) => c.indice(obra), obra);
  return <Esperando lectura={lectura}>{(i: Indice) => <VistaIndice indice={i} />}</Esperando>;
}

function VistaIndice({ indice }: { indice: Indice }) {
  const obra = encodeURIComponent(indice.id);
  return (
    <main className="indice">
      <p><Link to={`/obras/${obra}`}>{indice.titulo}</Link></p>
      <h1>Índice</h1>
      <ol className="capitulos">
        {indice.capitulos.map((c) => (
          <li key={c.id} data-testid="capitulo-del-indice" data-capitulo={c.id}
            data-estado={c.estado}>
            <h2><Link to={`/obras/${obra}/capitulos/${encodeURIComponent(c.id)}`}>
              {`Capítulo ${c.orden}`}
            </Link></h2>
            <span className="estado-de-capitulo">{c.estado}</span>
            <ol className="escenas">
              {c.escenas.map((e) => (
                <li key={e.id} data-testid="escena-del-indice" data-escena={e.id}>
                  <Link to={`/obras/${obra}/escenas/${encodeURIComponent(e.id)}`}>{e.id}</Link>
                  <EscenaConEstado escena={e} conTexto={false} />
                </li>
              ))}
            </ol>
          </li>
        ))}
      </ol>
      <p><Link to={`/obras/${obra}/fichas`}>Fichas</Link></p>
    </main>
  );
}
