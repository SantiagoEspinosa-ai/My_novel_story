import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCliente, useLectura, type Estanteria, type ObraEnLaEstanteria } from "@/shared/api";
import { EtiquetaDeEstado, Esperando, FASE_DE_GENERACION, SinDato } from "@/shared/ui";
import "./estanteria.css";

// La estanteria (SPEC-33 RF-01..RF-04): todas las novelas, cada una en una tarjeta
// tipografica con su portada -titulo y dedicatoria, como en el dominio-, el destinatario y
// el estado. Sin imagen, por decision del autor. El estado llega resuelto; lo ausente se dice.
export function PaginaEstanteria() {
  const lectura = useLectura((c) => c.estanteria(), "estanteria");
  return (
    <main className="contenido estanteria">
      <header className="estanteria__cabecera">
        <div>
          <p className="estanteria__antetitulo">Novelas para regalar</p>
          <h1>La estantería</h1>
        </div>
        <GenerarNovela />
      </header>
      <Esperando lectura={lectura}>{(e: Estanteria) => <Baldas obras={e.obras} />}</Esperando>
    </main>
  );
}

function Baldas({ obras }: { obras: ObraEnLaEstanteria[] }) {
  if (obras.length === 0) {
    return <p className="estanteria__vacia">Todavía no hay ninguna novela. Empieza por la entrevista.</p>;
  }
  return (
    <ul className="estanteria__baldas">
      {obras.map((o) => <TarjetaDeObra key={o.id} obra={o} />)}
    </ul>
  );
}

// RF-04: un solo boton, que abre una entrevista nueva. La obra nace con ella.
function GenerarNovela() {
  const cliente = useCliente();
  const navegar = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [creando, setCreando] = useState(false);
  async function generar() {
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
        disabled={creando} onClick={() => void generar()}>Generar novela</button>
      {error && <p role="alert" className="aviso">{error}</p>}
    </div>
  );
}

function TarjetaDeObra({ obra: o }: { obra: ObraEnLaEstanteria }) {
  const id = encodeURIComponent(o.id);
  return (
    <li className="libro" data-testid={`obra-${o.id}`} data-fase={o.fase ?? "sin_generacion"}>
      <div className="libro__lomo" aria-hidden="true" />
      <div className="libro__portada">
        <h2 className="libro__titulo">
          <SinDato valor={o.titulo} ausente="sin título todavía">{(t) => t}</SinDato>
        </h2>
        {o.dedicatoria && <p className="libro__dedicatoria">{o.dedicatoria}</p>}
        <p className="libro__para">
          para{" "}
          <SinDato valor={o.destinatario} ausente="destinatario sin dato">{(d) => <strong>{d}</strong>}</SinDato>
        </p>
      </div>
      <footer className="libro__pie">
        {o.fase
          ? <EtiquetaDeEstado distintivo={FASE_DE_GENERACION[o.fase]} />
          : <span className="sin-dato">sin generación</span>}
        {o.fase === "publicada" && <Link className="boton boton--secundario" to={`/obras/${id}`}>Leer</Link>}
        {o.fase && o.fase !== "publicada" && (
          <Link className="boton boton--secundario" to={`/obras/${id}/generacion`}>Ver cómo se escribe</Link>
        )}
        {!o.fase && o.entrevista && (
          <Link className="boton boton--secundario" to={`/entrevistas/${encodeURIComponent(o.entrevista)}`}>
            {o.entrevista_cerrada ? "Escribir la novela" : "Seguir la entrevista"}
          </Link>
        )}
      </footer>
    </li>
  );
}
