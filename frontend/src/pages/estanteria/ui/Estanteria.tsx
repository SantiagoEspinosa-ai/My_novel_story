import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCliente, useLectura, type Estanteria, type ObraEnLaEstanteria } from "@/shared/api";
import {
  COLORES_DE_LOMO, EtiquetaDeEstado, Esperando, FASE_DE_GENERACION, SinDato,
} from "@/shared/ui";
import "./estanteria.css";

// La estanteria de madera (SPEC-36 RF-01, sobre SPEC-33 RF-01..RF-04): cada obra es un lomo en
// una balda, con su titulo y su estado; al pulsarlo, su ficha al lado. El estado llega resuelto;
// lo ausente se dice. El color del lomo es presentacion: sale del id, para que no cambie.
const LOMOS_POR_BALDA = 7;

export function PaginaEstanteria() {
  const lectura = useLectura((c) => c.estanteria(), "estanteria");
  return (
    <main className="estanteria-pared">
      <div className="contenido estanteria">
        <header className="estanteria__cabecera">
          <div>
            <p className="estanteria__antetitulo">Novelas para regalar</p>
            <h1>La estantería</h1>
          </div>
          <EncargarNovela />
        </header>
        <Esperando lectura={lectura}>{(e: Estanteria) => <Baldas obras={e.obras} />}</Esperando>
      </div>
    </main>
  );
}

function Baldas({ obras }: { obras: ObraEnLaEstanteria[] }) {
  const [elegida, setElegida] = useState<string | null>(null);
  if (obras.length === 0) {
    return <p className="estanteria__vacia">Todavía no hay ninguna novela. Empieza por encargar una.</p>;
  }
  const baldas: ObraEnLaEstanteria[][] = [];
  for (let i = 0; i < obras.length; i += LOMOS_POR_BALDA) baldas.push(obras.slice(i, i + LOMOS_POR_BALDA));
  const abierta = obras.find((o) => o.id === elegida) ?? null;
  return (
    <div className="estanteria__mueble">
      <div className="estanteria__baldas">
        {baldas.map((b, n) => (
          <div key={n} className="balda" data-testid="balda">
            {b.map((o) => (
              <Lomo key={o.id} obra={o} pulsado={o.id === elegida}
                alPulsar={() => setElegida(o.id === elegida ? null : o.id)} />
            ))}
          </div>
        ))}
      </div>
      {abierta
        ? <FichaDelLibro obra={abierta} />
        : <p className="estanteria__pista">Pulsa un libro para ver su ficha.</p>}
    </div>
  );
}

function colorDe(id: string) {
  let h = 0;
  for (const c of id) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return COLORES_DE_LOMO[h % COLORES_DE_LOMO.length];
}

function Lomo({ obra: o, pulsado, alPulsar }: {
  obra: ObraEnLaEstanteria; pulsado: boolean; alPulsar: () => void;
}) {
  const alto = 200 + (o.id.length * 7) % 40;
  return (
    <button type="button" className="lomo" data-testid={`obra-${o.id}`} aria-pressed={pulsado}
      data-fase={o.fase ?? "sin_generacion"}
      style={{ background: colorDe(o.id), height: `${alto}px` }} onClick={alPulsar}>
      <span className="lomo__titulo">{o.titulo ?? "(sin título)"}</span>
      <span className="lomo__estado">
        {o.fase ? FASE_DE_GENERACION[o.fase].etiqueta : "sin generación"}
      </span>
    </button>
  );
}

function FichaDelLibro({ obra: o }: { obra: ObraEnLaEstanteria }) {
  const id = encodeURIComponent(o.id);
  return (
    <aside className="ficha-del-libro" data-testid="ficha-del-libro" aria-live="polite">
      <h2 className="ficha-del-libro__titulo">
        <SinDato valor={o.titulo} ausente="sin título todavía">{(t) => t}</SinDato>
      </h2>
      {o.dedicatoria && <p className="ficha-del-libro__dedicatoria">«{o.dedicatoria}»</p>}
      <p className="ficha-del-libro__para">
        para{" "}
        <SinDato valor={o.destinatario} ausente="destinatario sin dato">{(d) => <strong>{d}</strong>}</SinDato>
      </p>
      <div className="ficha-del-libro__estado">
        {o.fase
          ? <EtiquetaDeEstado distintivo={FASE_DE_GENERACION[o.fase]} />
          : <span className="sin-dato">sin generación</span>}
      </div>
      <div className="ficha-del-libro__acciones">
        {o.fase === "publicada" && <Link className="boton boton--principal" to={`/obras/${id}`}>Leer</Link>}
        {o.fase && o.fase !== "publicada" && (
          <>
            <Link className="boton boton--principal" to={`/obras/${id}/generacion`}>Ver cómo se escribe</Link>
            <Link className="boton boton--secundario" to={`/obras/${id}`}>Leer lo escrito</Link>
          </>
        )}
        {!o.fase && o.entrevista && (
          <Link className="boton boton--principal" to={`/entrevistas/${encodeURIComponent(o.entrevista)}`}>
            {o.entrevista_cerrada ? "Escribir la novela" : "Seguir la entrevista"}
          </Link>
        )}
      </div>
    </aside>
  );
}

// SPEC-33 RF-04, SPEC-36 RF-01: un solo boton, que abre una entrevista nueva. La obra nace con ella.
function EncargarNovela() {
  const cliente = useCliente();
  const navegar = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [creando, setCreando] = useState(false);
  async function encargar() {
    setCreando(true);
    try {
      const e = await cliente.crearEntrevista();
      navegar(`/entrevistas/${encodeURIComponent(e.id)}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setCreando(false);
    }
  }
  return (
    <div className="estanteria__generar">
      <button type="button" className="boton boton--principal boton--grande"
        disabled={creando} onClick={() => void encargar()}>Encargar una novela</button>
      {error && <p role="alert" className="aviso">{error}</p>}
    </div>
  );
}
