import type { EscenaLeida } from "@/shared/api";

// SPEC-43 RF-01: lo que ve el lector de una escena es su texto y nada mas. El estado y los
// hallazgos siguen en la API y se pintan en la administracion con `EscenaConEstado`.
export function TextoDeEscena({ escena }: { escena: Pick<EscenaLeida, "borrador"> }) {
  return (
    <div data-testid="texto-de-escena" className="texto">
      {escena.borrador
        ? <p style={{ whiteSpace: "pre-wrap" }}>{escena.borrador.texto}</p>
        : <p className="sin-texto">Todavía no está escrito.</p>}
    </div>
  );
}

// SPEC-43 RF-02: «Capitulo N» y, si el plan le dio titulo, «Capitulo N · su titulo».
export function tituloDeCapitulo(c: { orden: number; titulo?: string | null }) {
  return c.titulo ? `Capítulo ${c.orden} · ${c.titulo}` : `Capítulo ${c.orden}`;
}
