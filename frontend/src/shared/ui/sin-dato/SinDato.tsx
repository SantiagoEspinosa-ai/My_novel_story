import type { ReactNode } from "react";

// Lo que no consta viaja nulo (SPEC-22 RF-35) y se dice: «sin dato», o el nombre que la
// ausencia tenga en su sitio («no declarado»). Una lista vacia es otra cosa —«se miro y no
// habia»— y se pinta distinto. Un cero es un dato y se pinta como tal.
type Props<T> = {
  valor: T | null | undefined;
  ausente?: string;
  vacio?: string;
  children: (valor: T) => ReactNode;
};

export function SinDato<T>({ valor, ausente = "sin dato", vacio = "ninguno", children }: Props<T>) {
  if (valor === null || valor === undefined) {
    return <span className="sin-dato" data-sin-dato="true">{ausente}</span>;
  }
  if (Array.isArray(valor) && valor.length === 0) {
    return <span className="vacio">{vacio}</span>;
  }
  return <>{children(valor)}</>;
}
