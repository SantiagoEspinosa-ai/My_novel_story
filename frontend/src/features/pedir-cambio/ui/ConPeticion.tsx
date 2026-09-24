import { useRef, useState, type ReactNode } from "react";
import type { EscenaLeida } from "@/shared/api";
import { PedirCambio } from "./PedirCambio";

// Envuelve una escena para pedir un cambio sobre ella (SPEC-22 RF-47). Si el lector
// selecciona un fragmento del texto, se recoge **aqui** para enseñarlo en el panel; no viaja
// al backend (PLAN-22, reparto con PLAN-23: lo que viaja es el hecho o el personaje).
// Una escena sin texto no ofrece pedir nada: no hay nada escrito que cambiar.
export function ConPeticion({ obra, escena, children }: {
  obra: string;
  escena: Pick<EscenaLeida, "id" | "borrador" | "personajes_presentes">;
  children: ReactNode;
}) {
  const caja = useRef<HTMLDivElement>(null);
  const [fragmento, setFragmento] = useState<string | null>(null);
  const [abierto, setAbierto] = useState(false);

  function recoger() {
    const s = window.getSelection();
    if (!s || s.rangeCount === 0 || !caja.current) return;
    const texto = s.toString().trim();
    if (texto && caja.current.contains(s.getRangeAt(0).commonAncestorContainer)) {
      setFragmento(texto);
    }
  }

  return (
    <div className="con-peticion">
      <div ref={caja} onMouseUp={recoger} onKeyUp={recoger}>{children}</div>
      {escena.borrador && !abierto && (
        <div className="con-peticion__barra">
          <button type="button" className="boton boton--secundario"
            onClick={() => setAbierto(true)}>
            {fragmento ? "Pedir un cambio sobre el fragmento seleccionado" : "Pedir un cambio"}
          </button>
          {fragmento && <span className="con-peticion__fragmento">«{fragmento}»</span>}
        </div>
      )}
      {abierto && (
        <PedirCambio obra={obra} escena={escena} fragmento={fragmento}
          onCerrar={() => setAbierto(false)} />
      )}
    </div>
  );
}
