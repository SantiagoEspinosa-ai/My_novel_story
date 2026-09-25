import { useParams } from "react-router-dom";
import { Progreso } from "@/entities/progreso";
import { urlDelPdf, useLectura, type Indice, type Lectura, type PdfDisponible } from "@/shared/api";
import { BotonEnlace, Esperando } from "@/shared/ui";
import "./portada.css";

// La portada: la cubierta del libro, con el titulo y la dedicatoria de la Obra (SPEC-22 RF-46,
// SPEC-35 RF-11). Sin dedicatoria, solo el titulo: no se rellena con nada, porque un relleno se
// leeria como la dedicatoria. Los adornos de la cubierta son CSS, no texto, por lo mismo.
// El PDF se ofrece solo si el backend dice que lo hay (SPEC-35 RF-12, cuestion 2); si no, se
// dice por que, y no hay boton que falle.
export function PaginaPortada() {
  const { obra = "" } = useParams();
  const lectura = useLectura((c) => c.indice(obra), obra);
  return <Esperando lectura={lectura}>{(i: Indice) => <Portada indice={i} />}</Esperando>;
}

function Portada({ indice }: { indice: Indice }) {
  const pdf = useLectura((c) => c.pdfDisponible(indice.id), `pdf:${indice.id}`);
  const o = encodeURIComponent(indice.id);
  const primero = indice.capitulos[0];
  return (
    <main className="portada portada--cubierta">
      <div className="portada__libro">
        <h1>{indice.titulo}</h1>
        {indice.dedicatoria !== null && (
          <p data-testid="dedicatoria" className="dedicatoria" style={{ whiteSpace: "pre-wrap" }}>
            {indice.dedicatoria}
          </p>
        )}
      </div>
      <nav className="portada__acciones">
        {primero && (
          <BotonEnlace a={`/obras/${o}/capitulos/${encodeURIComponent(primero.id)}`}>
            Empezar a leer
          </BotonEnlace>
        )}
        <BotonEnlace a={`/obras/${o}/indice`} variante="secundario">Índice</BotonEnlace>
        <BotonEnlace a={`/obras/${o}/fichas`} variante="secundario">Fichas</BotonEnlace>
        <Pdf obra={indice.id} lectura={pdf} />
      </nav>
      <Progreso obra={indice.id} />
    </main>
  );
}

function Pdf({ obra, lectura }: { obra: string; lectura: Lectura<PdfDisponible> }) {
  if (lectura.estado !== "listo") return null;
  if (!lectura.datos.disponible) {
    return <p className="portada__sin-pdf">Sin PDF todavía: {lectura.datos.motivo}</p>;
  }
  return (
    <a className="boton boton--secundario" href={urlDelPdf(obra)} download>Descargar en PDF</a>
  );
}
