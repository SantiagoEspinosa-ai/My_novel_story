import type { ReactNode } from "react";
import type { Cuaderno as CuadernoDelBackend, Nombres } from "@/shared/api";
import { Sabido } from "./Cuaderno";

// SPEC-35 RF-07: cuando el backend dice `puede_cerrar`, el repaso de la ficha y lo que se
// propone -titulo, premisa y dedicatoria-, con la opcion de seguir hablando. Cerrar es un
// acto aparte y sin vuelta atras (SPEC-25), y la pantalla lo dice. Lo ausente se dice.
export function CuadernoCompleto({ cuaderno, nombres, alCambiar, alCerrar, rechazo }: {
  cuaderno: CuadernoDelBackend;
  nombres: Nombres;
  alCambiar: () => void;
  alCerrar: () => void;
  rechazo: ReactNode;
}) {
  const p = cuaderno.propuesta;
  return (
    <section className="tarjeta cuaderno-completo" data-testid="cuaderno-completo"
      aria-label="El cuaderno completo">
      <h2>El cuaderno completo</h2>
      <p>Ya está todo lo necesario para escribir la novela. Repásalo antes de cerrar.</p>
      <div className="cuaderno-completo__propuesta">
        <p className="cuaderno-completo__etiqueta">Título</p>
        <p className="cuaderno-completo__titulo">{p.titulo ?? <Falta />}</p>
        <p className="cuaderno-completo__etiqueta">De qué va</p>
        <p>{p.premisa ?? <Falta />}</p>
        <p className="cuaderno-completo__etiqueta">Dedicatoria</p>
        <p className="dedicatoria">{p.dedicatoria ?? <span className="sin-dato">sin dedicatoria</span>}</p>
      </div>
      <Sabido cuaderno={cuaderno} />
      {nombres.vetados.length > 0 && (
        <p>No aparecerán: {nombres.vetados.join(", ")}</p>
      )}
      <p className="cuaderno-completo__aviso">
        Cerrar la ficha <strong>no tiene vuelta atrás</strong>: después ya no se puede cambiar
        nada de la entrevista. Si algo no está bien, sigue la conversación.
      </p>
      <div className="entrevista__acciones">
        <button type="button" className="boton boton--secundario" onClick={alCambiar}>
          Quiero cambiar algo
        </button>
        <button type="button" className="boton boton--principal" onClick={alCerrar}>
          Cerrar la ficha
        </button>
      </div>
      {rechazo}
    </section>
  );
}

function Falta() {
  return <span className="sin-dato">sin decidir</span>;
}
