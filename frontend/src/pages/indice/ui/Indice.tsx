import { Link, useParams } from "react-router-dom";
import { EscenaConEstado } from "@/entities/escena";
import { useLectura, type Indice } from "@/shared/api";
import { ESTADO_DE_CAPITULO, Esperando, EtiquetaDeEstado } from "@/shared/ui";

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
    <main className="contenido indice">
      <p className="migas"><Link to={`/obras/${obra}`}>{indice.titulo}</Link></p>
      <h1>Índice</h1>
      <ol className="capitulos">
        {indice.capitulos.map((c) => (
          <li key={c.id} data-testid="capitulo-del-indice" data-capitulo={c.id}
            data-estado={c.estado} className="tarjeta capitulo-del-indice">
            <div className="capitulo-del-indice__cabecera">
              <h2><Link to={`/obras/${obra}/capitulos/${encodeURIComponent(c.id)}`}>
                {`Capítulo ${c.orden}`}
              </Link></h2>
              <EtiquetaDeEstado distintivo={ESTADO_DE_CAPITULO[c.estado]} />
            </div>
            <ol className="escenas">
              {c.escenas.map((e) => (
                <li key={e.id} data-testid="escena-del-indice" data-escena={e.id}
                  className="escena-del-indice">
                  <Link to={`/obras/${obra}/escenas/${encodeURIComponent(e.id)}`}>{e.id}</Link>
                  <EscenaConEstado escena={e} conTexto={false} />
                </li>
              ))}
            </ol>
          </li>
        ))}
      </ol>
      <p><Link className="boton boton--secundario" to={`/obras/${obra}/fichas`}>Fichas</Link></p>
    </main>
  );
}
