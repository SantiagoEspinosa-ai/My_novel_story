import type { HTMLAttributes } from "react";

export function Tarjeta({ className = "", ...resto }: HTMLAttributes<HTMLElement>) {
  return <article className={`tarjeta ${className}`.trim()} {...resto} />;
}
