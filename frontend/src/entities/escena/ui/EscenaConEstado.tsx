import type { EscenaLeida, Hallazgo } from "@/shared/api";

// Una escena se pinta **siempre** con su estado y sus hallazgos abiertos (SPEC-22 RF-39,
// VER-18): un texto suelto induce a darlo por bueno. Si la respuesta llega sin alguno de
// los dos, no se pinta el texto: se dice que falta. Nada se calcula aqui: la rendicion
// llega resuelta (RF-40) y cada hallazgo trae su estado.

const ETIQUETA_DE_ESTADO: Record<string, string> = {
  planificada: "planificada",
  generada: "generada",
  en_verificacion: "en verificación",
  rechazada: "rechazada",
  en_revision: "en revisión",
  aceptada: "aceptada",
  aceptada_por_rendicion: "aceptada por rendición",
  consolidada: "consolidada",
};

const ETIQUETA_DE_HALLAZGO: Record<string, string> = {
  abierto: "abierto",
  sin_veredicto: "sin veredicto",
  resuelto: "resuelto",
  descartado: "descartado",
};

type EscenaPintable = Omit<EscenaLeida, "borrador"> & { borrador?: EscenaLeida["borrador"] };

export function EscenaConEstado({ escena, conTexto = true }: {
  escena: EscenaPintable;
  conTexto?: boolean;
}) {
  if (!escena || !escena.estado || !Array.isArray(escena.hallazgos_abiertos)) {
    return (
      <p role="alert" className="escena-incompleta">
        La escena {escena?.id ?? "?"} llegó sin su estado o sus hallazgos: no se enseña su texto.
      </p>
    );
  }
  return (
    <article className="escena" data-escena={escena.id}>
      <header>
        <span data-testid="estado-de-escena" data-estado={escena.estado}
          data-rendida={String(escena.se_acepto_rindiendose)}
          className={escena.se_acepto_rindiendose ? "estado rendida" : "estado"}>
          {escena.se_acepto_rindiendose
            ? "aceptada por rendición"
            : ETIQUETA_DE_ESTADO[escena.estado] ?? escena.estado}
        </span>
        <Hallazgos hallazgos={escena.hallazgos_abiertos} />
      </header>
      {conTexto && (
        <div data-testid="texto-de-escena" className="texto">
          {escena.borrador
            ? <p style={{ whiteSpace: "pre-wrap" }}>{escena.borrador.texto}</p>
            : <p className="sin-texto">sin texto todavía ({ETIQUETA_DE_ESTADO[escena.estado]})</p>}
        </div>
      )}
    </article>
  );
}

function Hallazgos({ hallazgos }: { hallazgos: Hallazgo[] }) {
  if (hallazgos.length === 0) {
    return <span className="sin-hallazgos">sin hallazgos abiertos</span>;
  }
  return (
    <ul className="hallazgos">
      {hallazgos.map((h, i) => (
        <li key={i} data-testid="hallazgo" data-estado={h.estado} data-severidad={h.severidad}>
          {h.invariante} · {h.severidad} · {ETIQUETA_DE_HALLAZGO[h.estado] ?? h.estado}: {h.descripcion}
        </li>
      ))}
    </ul>
  );
}
