import type { ReactNode } from "react";
import { Link } from "react-router-dom";

export function BotonEnlace({ a, variante = "principal", children }: {
  a: string; variante?: "principal" | "secundario"; children: ReactNode;
}) {
  return <Link className={`boton boton--${variante}`} to={a}>{children}</Link>;
}
