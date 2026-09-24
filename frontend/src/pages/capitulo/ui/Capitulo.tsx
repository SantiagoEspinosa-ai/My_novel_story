import { Link, useParams } from "react-router-dom";
import { EscenaConEstado } from "@/entities/escena";
import { useLectura, type CapituloLeido } from "@/shared/api";
import { Esperando } from "@/shared/ui";

// La lectura continua de un capitulo (SPEC-22 RF-41). Que escenas entran y en que orden lo
// decide el backend; aqui se pinta **una escena por bloque**, cada una con su estado y sus
// hallazgos (RF-39). No se juntan textos: juntarlos borraria de que escena es cada frase.
export function PaginaCapitulo() {
  const { obra = "", capitulo = "" } = useParams();
  const lectura = useLectura((c) => c.capitulo(capitulo), capitulo);
  return (
    <Esperando lectura={lectura}>
      {(cap: CapituloLeido) => <VistaCapitulo obra={obra} capitulo={cap} />}
    </Esperando>
  );
}

function VistaCapitulo({ obra, capitulo }: { obra: string; capitulo: CapituloLeido }) {
  const o = encodeURIComponent(obra);
  return (
    <main className="capitulo" data-capitulo={capitulo.id} data-estado={capitulo.estado}>
      <nav><Link to={`/obras/${o}/indice`}>Índice</Link></nav>
      <h1>{`Capítulo ${capitulo.orden}`}</h1>
      <span className="estado-de-capitulo">{capitulo.estado}</span>
      {capitulo.escenas.map((e) => (
        <section key={e.id} data-testid="bloque-de-escena" data-escena={e.id}>
          <EscenaConEstado escena={e} />
        </section>
      ))}
    </main>
  );
}
