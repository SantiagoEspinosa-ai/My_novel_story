import type { TurnoDeEntrevista } from "@/shared/api";
import { EtiquetaDeEstado, SEVERIDAD } from "@/shared/ui";
import { Entrevistadora } from "./Entrevistadora";
import "./turno.css";

// Un turno de la conversacion (SPEC-33 RF-05, RF-06): la respuesta del comprador, la pregunta
// que vino despues y, dentro del mismo turno, lo que el codigo dijo en el. Se pinta lo que
// llega; nada se calcula aqui. Un turno sin nada que decir no pinta un panel vacio, y uno
// anterior a guardar sus avisos lo dice (un hueco no es una lista vacia).
// SPEC-35 RF-04: cada pregunta la firma la entrevistadora. SPEC-34 RF-01: una respuesta escrita
// en el campo de nombres no paso por ningun agente, y se ve como tal.
export function Turno({ turno }: { turno: TurnoDeEntrevista }) {
  return (
    <li className="turno" data-testid={`turno-${turno.orden}`}>
      <div className="turno__burbuja turno__burbuja--comprador">
        <p>{turno.respuesta}</p>
        {turno.fuera_del_modelo && (
          <p className="turno__cuaderno">escrito en el cuaderno</p>
        )}
      </div>
      <div className="turno__burbuja turno__burbuja--entrevistador">
        <Entrevistadora />
        <p>{turno.pregunta}</p>
        <Observaciones turno={turno} />
      </div>
    </li>
  );
}

function Observaciones({ turno }: { turno: TurnoDeEntrevista }) {
  const { falta, avisos, contradicciones_abiertas: contradicciones } = turno;
  if (falta === null && avisos === null && contradicciones === null) {
    return <p className="sin-dato turno__no-guardado">avisos de este turno no guardados</p>;
  }
  const hay = (falta?.length ?? 0) + (avisos?.length ?? 0) + (contradicciones?.length ?? 0);
  if (hay === 0) return null;
  return (
    <ul className="turno__observaciones" data-testid="observaciones">
      {(contradicciones ?? []).map((c) => (
        <li key={`c-${c.descripcion}`}>
          <EtiquetaDeEstado distintivo={SEVERIDAD.bloqueante} texto="contradicción" />
          <span>{c.descripcion}</span>
        </li>
      ))}
      {(avisos ?? []).map((a) => (
        <li key={`a-${a}`}>
          <EtiquetaDeEstado distintivo={SEVERIDAD.mayor} texto="aviso" />
          <span>{a}</span>
        </li>
      ))}
      {(falta ?? []).map((f) => (
        <li key={`f-${f}`}>
          <EtiquetaDeEstado distintivo={SEVERIDAD.menor} texto="pendiente" />
          <span>falta: {f}</span>
        </li>
      ))}
    </ul>
  );
}
