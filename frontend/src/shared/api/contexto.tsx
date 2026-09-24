import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { ErrorDeLaApi, type Cliente } from "./cliente";

// El cliente llega por contexto: la app le da el fetch real y las pruebas uno de fixtures.
const ContextoDelCliente = createContext<Cliente | null>(null);

export function ClienteProvider({ cliente, children }: { cliente: Cliente; children: ReactNode }) {
  return <ContextoDelCliente.Provider value={cliente}>{children}</ContextoDelCliente.Provider>;
}

export function useCliente(): Cliente {
  const c = useContext(ContextoDelCliente);
  if (!c) throw new Error("falta ClienteProvider: nadie ha dado un cliente de la API");
  return c;
}

export type Lectura<T> =
  | { estado: "cargando" }
  | { estado: "error"; mensaje: string; codigo: number | null }
  | { estado: "listo"; datos: T };

/** Lee una respuesta de la API. No transforma nada: devuelve lo que llega. */
export function useLectura<T>(leer: (c: Cliente) => Promise<T>, clave: string): Lectura<T> {
  const cliente = useCliente();
  const [lectura, setLectura] = useState<Lectura<T>>({ estado: "cargando" });
  useEffect(() => {
    let vivo = true;
    setLectura({ estado: "cargando" });
    leer(cliente).then(
      (datos) => vivo && setLectura({ estado: "listo", datos }),
      (e: unknown) => vivo && setLectura({
        estado: "error",
        mensaje: e instanceof Error ? e.message : String(e),
        codigo: e instanceof ErrorDeLaApi ? e.estado : null,
      }),
    );
    return () => { vivo = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cliente, clave]);
  return lectura;
}
