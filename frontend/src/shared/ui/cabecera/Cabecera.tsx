import type { ReactNode } from "react";

// PLAN-35 F7: la web ya no es solo la lectura; encarga, sigue la escritura y lee.
export function Cabecera({ children }: { children?: ReactNode }) {
  return (
    <header className="cabecera">
      <span className="cabecera__marca">Novelas para regalar</span>
      <nav>{children}</nav>
    </header>
  );
}
