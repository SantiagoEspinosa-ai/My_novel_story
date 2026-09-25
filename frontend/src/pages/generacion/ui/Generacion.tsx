import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Progreso } from "@/entities/progreso";
import {
  useCliente, useLectura, type CapituloEnGeneracion, type GeneracionEnVivo,
} from "@/shared/api";
import { INTERVALO_DE_REGALO_MS } from "@/shared/config";
import { ESTADO_DE_ESCENA, EtiquetaDeEstado, FASE_DE_GENERACION, SEVERIDAD } from "@/shared/ui";
import { CosteEnVivo } from "./CosteEnVivo";
import "./generacion.css";

// La generacion, visible (SPEC-33 RF-14..RF-17), de noche (SPEC-35 RF-13). Los capitulos en
// fila con su fase, que se refresca sola, y las seis notas del Editor al cerrarse cada uno. La
// fase de cada capitulo, la de la obra, el motivo de un lanzamiento fallido y el coste llegan
// resueltos de la API: aqui solo se pintan.
export function PaginaGeneracion({ intervaloMs = INTERVALO_DE_REGALO_MS }: {
  intervaloMs?: number;
}) {
  const { obra = "" } = useParams();
  const cliente = useCliente();
  const [g, setG] = useState<GeneracionEnVivo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vivo = true;
    const leer = () => cliente.generacion(obra).then(
      (d) => { if (vivo) { setG(d); setError(null); } },
      (e: unknown) => { if (vivo) setError(e instanceof Error ? e.message : String(e)); });
    void leer();
    const id = setInterval(leer, intervaloMs);
    return () => { vivo = false; clearInterval(id); };
  }, [cliente, obra, intervaloMs]);

  if (error && !g) {
    return <main className="generacion-noche"><div className="contenido">
      <p role="alert">{error}</p></div></main>;
  }
  if (!g) {
    return <main className="generacion-noche"><div className="contenido">
      <p aria-busy="true">cargando…</p></div></main>;
  }

  return (
    <main className="generacion-noche">
      <div className="contenido generacion">
        <header className="generacion__cabecera">
          <h1>La novela se está escribiendo</h1>
          <CosteEnVivo coste={g.coste} />
        </header>
        {g.motivo_del_fallo && (
          <p role="alert" className="aviso generacion__fallo">
            La novela no se pudo empezar a escribir: {g.motivo_del_fallo}
          </p>
        )}
        <AlTerminar g={g} />
        <Progreso obra={g.obra} intervaloMs={intervaloMs} />
        {g.capitulos.length === 0 ? (
          !g.motivo_del_fallo && (
            <p className="generacion__sin-capitulos" data-testid="sin-capitulos">
              Todavía se está preparando el plan de la novela: los capítulos aparecen cuando
              esté aprobado.
            </p>
          )
        ) : (
          <ol className="generacion__capitulos" data-testid="capitulos">
            {g.capitulos.map((c) => <Capitulo key={c.numero} capitulo={c} />)}
          </ol>
        )}
      </div>
    </main>
  );
}

// SPEC-35 RF-13: al terminar, a leer. Publicada, la novela; sin publicar o parada, lo escrito,
// con el motivo de que no se publicara tal como lo da el backend.
function AlTerminar({ g }: { g: GeneracionEnVivo }) {
  const a = `/obras/${encodeURIComponent(g.obra)}`;
  if (g.fase_de_la_obra === "publicada") {
    return (
      <div className="generacion__terminada">
        <p>La novela está terminada y publicada.</p>
        <Link className="boton boton--principal" to={a}>Leer la novela</Link>
      </div>
    );
  }
  if (g.fase_de_la_obra === "esperando_revision" || g.fase_de_la_obra === "parada") {
    return <SinPublicar obra={g.obra} a={a} />;
  }
  return null;
}

function SinPublicar({ obra, a }: { obra: string; a: string }) {
  const pdf = useLectura((c) => c.pdfDisponible(obra), `pdf:${obra}`);
  return (
    <div className="generacion__terminada">
      <p data-testid="sin-publicar">
        La novela no está publicada
        {pdf.estado === "listo" && pdf.datos.motivo ? <>: {pdf.datos.motivo}</> : "."}
      </p>
      <Link className="boton boton--secundario" to={a}>Leer lo escrito</Link>
    </div>
  );
}

// La fase solo dice algo del capitulo en curso. Uno que ya paso conserva su ultima fase
// -casi siempre «resumiendo», porque el pipeline no cierra capitulos- y lo que dice que
// termino es el estado de su escena (F-200; CLAUDE.md: una escena, siempre con su estado).
function Capitulo({ capitulo: c }: { capitulo: CapituloEnGeneracion }) {
  const estado = c.es_el_actual ? c.fase : c.fase ? "pasado" : "no_empezado";
  return (
    <li className="tarjeta generacion__capitulo" data-testid={`capitulo-${c.numero}`}
      data-fase={estado}>
      <div className="generacion__numero">Capítulo {c.numero}</div>
      {c.es_el_actual && c.fase && <EtiquetaDeEstado distintivo={FASE_DE_GENERACION[c.fase]} />}
      {!c.es_el_actual && c.fase && c.escenas.map((e) => (
        <EtiquetaDeEstado key={e.id} distintivo={ESTADO_DE_ESCENA[e.estado]} />
      ))}
      {!c.fase && <span className="sin-dato">no empezado</span>}
      {c.es_el_actual && c.motivo && <p className="generacion__motivo">motivo: {c.motivo}</p>}
      {c.notas.length > 0 && (
        <ul className="generacion__notas" data-testid={`notas-${c.numero}`}>
          {c.notas.map((n) => (
            <li key={n.criterio} data-testid={`nota-${n.criterio}`}
              className={n.bajo_el_umbral ? "generacion__nota generacion__nota--baja"
                : "generacion__nota"}>
              <span className="generacion__criterio">{n.criterio.replace(/_/g, " ")}</span>
              <strong>{n.nota}/5</strong>
              {n.bajo_el_umbral && (
                <EtiquetaDeEstado distintivo={SEVERIDAD.mayor} texto="bajo el umbral" />
              )}
              <p className="generacion__justificacion">{n.justificacion}</p>
              {n.instruccion && <p className="generacion__instruccion">→ {n.instruccion}</p>}
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}
