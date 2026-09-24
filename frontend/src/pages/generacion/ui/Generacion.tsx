import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Progreso } from "@/entities/progreso";
import { useCliente, type CapituloEnGeneracion, type GeneracionEnVivo } from "@/shared/api";
import { INTERVALO_DE_REGALO_MS } from "@/shared/config";
import { EtiquetaDeEstado, FASE_DE_GENERACION, SEVERIDAD } from "@/shared/ui";
import { CosteEnVivo } from "./CosteEnVivo";
import "./generacion.css";

// La generacion, visible (SPEC-33 RF-14..RF-17). Los capitulos en fila con su fase, que se
// refresca sola, y las seis notas del Editor al cerrarse cada uno. La fase de cada capitulo,
// si una nota baja del umbral y el coste llegan resueltos de la API: aqui solo se pintan.
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

  if (error && !g) return <main className="contenido"><p role="alert">{error}</p></main>;
  if (!g) return <main className="contenido"><p aria-busy="true">cargando…</p></main>;

  return (
    <main className="contenido generacion">
      <header className="generacion__cabecera">
        <h1>La novela se está escribiendo</h1>
        <CosteEnVivo coste={g.coste} />
      </header>
      <Progreso obra={g.obra} intervaloMs={intervaloMs} />
      <ol className="generacion__capitulos" data-testid="capitulos">
        {g.capitulos.map((c) => <Capitulo key={c.numero} capitulo={c} />)}
      </ol>
    </main>
  );
}

function Capitulo({ capitulo: c }: { capitulo: CapituloEnGeneracion }) {
  return (
    <li className="tarjeta generacion__capitulo" data-testid={`capitulo-${c.numero}`}
      data-fase={c.fase ?? "no_empezado"}>
      <div className="generacion__numero">Capítulo {c.numero}</div>
      {c.fase
        ? <EtiquetaDeEstado distintivo={FASE_DE_GENERACION[c.fase]} />
        : <span className="sin-dato">no empezado</span>}
      {c.motivo && <p className="generacion__motivo">motivo: {c.motivo}</p>}
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
