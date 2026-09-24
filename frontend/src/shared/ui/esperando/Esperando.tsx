import type { ReactNode } from "react";

type LecturaMinima<T> =
  | { estado: "cargando" }
  | { estado: "error"; mensaje: string; codigo: number | null }
  | { estado: "listo"; datos: T };

// Cargando y error se dicen; lo que se pinta solo aparece cuando la respuesta llego.
export function Esperando<T>({ lectura, children }: {
  lectura: LecturaMinima<T>;
  children: (datos: T) => ReactNode;
}) {
  if (lectura.estado === "cargando") return <p aria-busy="true">cargando…</p>;
  if (lectura.estado === "error") {
    return (
      <p role="alert">
        {lectura.codigo === 404 ? "No existe." : "La API no contestó bien."} ({lectura.mensaje})
      </p>
    );
  }
  return <>{children(lectura.datos)}</>;
}
