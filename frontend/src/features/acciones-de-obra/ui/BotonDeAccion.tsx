import { Link } from "react-router-dom";
import { useLectura } from "@/shared/api";

// SPEC-44 RF-04: en cada fila de la administracion, la accion que toca -generar, reanudar o
// publicar-, tal como la decide el backend. Lleva a la pagina de la novela, donde esta la
// confirmacion con lo que va a costar: desde la tabla no se gasta nada.
export function BotonDeAccion({ obra }: { obra: string }) {
  const lectura = useLectura((c) => c.acciones(obra), `acciones:${obra}`);
  if (lectura.estado !== "listo") return null;
  const a = lectura.datos;
  const nombre = a.generar?.posible ? "Generar"
    : a.reanudar.posible ? "Reanudar"
    : a.publicar.posible ? "Publicar" : null;
  if (nombre === null) return null;
  return (
    <Link className="boton boton--secundario" to={`/admin/obras/${encodeURIComponent(obra)}`}>
      {nombre}
    </Link>
  );
}
