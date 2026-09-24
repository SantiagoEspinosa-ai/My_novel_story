import type { EscenaLeida, Hallazgo } from "@/shared/api";
import { ESTADO_DE_ESCENA, ESTADO_DE_HALLAZGO, EtiquetaDeEstado, SEVERIDAD } from "@/shared/ui";

// Una escena se pinta **siempre** con su estado y sus hallazgos abiertos (SPEC-22 RF-39,
// VER-18): un texto suelto induce a darlo por bueno. Si la respuesta llega sin alguno de
// los dos, no se pinta el texto: se dice que falta. Nada se calcula aqui: la rendicion
// llega resuelta (RF-40) y cada hallazgo trae su estado. Cada estado va con color y texto.

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
  const distintivo = escena.se_acepto_rindiendose
    ? ESTADO_DE_ESCENA.aceptada_por_rendicion
    : ESTADO_DE_ESCENA[escena.estado];
  return (
    <div className="escena" data-escena={escena.id}>
      <header>
        <EtiquetaDeEstado distintivo={distintivo} data-testid="estado-de-escena"
          data-estado={escena.estado} data-rendida={String(escena.se_acepto_rindiendose)}
          texto={escena.se_acepto_rindiendose ? "aceptada por rendición" : undefined} />
        <Hallazgos hallazgos={escena.hallazgos_abiertos} />
      </header>
      {conTexto && (
        <div data-testid="texto-de-escena" className="texto">
          {escena.borrador
            ? <p style={{ whiteSpace: "pre-wrap" }}>{escena.borrador.texto}</p>
            : <p className="sin-texto">
                sin texto todavía ({ESTADO_DE_ESCENA[escena.estado]?.etiqueta ?? escena.estado})
              </p>}
        </div>
      )}
    </div>
  );
}

function Hallazgos({ hallazgos }: { hallazgos: Hallazgo[] }) {
  if (hallazgos.length === 0) {
    return <span className="sin-hallazgos">sin hallazgos abiertos</span>;
  }
  return (
    <ul className="hallazgos">
      {hallazgos.map((h, i) => (
        <li key={i} className="hallazgo" data-testid="hallazgo" data-estado={h.estado}
          data-severidad={h.severidad}>
          <span className="hallazgo__invariante">{h.invariante}</span>
          <EtiquetaDeEstado distintivo={SEVERIDAD[h.severidad]} />
          <EtiquetaDeEstado distintivo={ESTADO_DE_HALLAZGO[h.estado]} />
          <span>{h.descripcion}</span>
        </li>
      ))}
    </ul>
  );
}
