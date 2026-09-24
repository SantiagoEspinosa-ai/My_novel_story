import "./estilos.css";
import { variablesCss } from "./tokens";

// Inyecta las variables del tema una vez. Todo lo demas las lee con var(--...).
export function Tema() {
  return <style data-tema="lectura">{variablesCss()}</style>;
}
