import type { HTMLAttributes } from "react";
import type { Distintivo } from "../tema/tokens";

// Un estado con su color **y** su texto: nunca solo color (SPEC-22 RF-59).
export function EtiquetaDeEstado({ distintivo, texto, ...resto }: {
  distintivo: Distintivo | undefined;
  texto?: string;
} & HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className="etiqueta" {...resto}
      style={distintivo ? { background: distintivo.fondo, color: distintivo.texto } : undefined}>
      {texto ?? distintivo?.etiqueta ?? "estado desconocido"}
    </span>
  );
}
