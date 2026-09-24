import type { ReactNode } from "react";

export function Cabecera({ children }: { children?: ReactNode }) {
  return (
    <header className="cabecera">
      <span className="cabecera__marca">Novela regalo <small>lectura</small></span>
      <nav>{children}</nav>
    </header>
  );
}
