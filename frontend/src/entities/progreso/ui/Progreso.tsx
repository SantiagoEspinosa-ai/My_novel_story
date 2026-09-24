import { useEffect, useState } from "react";
import { useCliente, type ProgresoDeGeneracion } from "@/shared/api";
import { INTERVALO_DE_PROGRESO_MS, UMBRAL_SIN_ACTIVIDAD_SEGUNDOS } from "@/shared/config";
import { EtiquetaDeEstado, FASE_DE_GENERACION } from "@/shared/ui";

// En que punto va una generacion (SPEC-22 RF-60). Se vuelve a pedir sola cada intervalo.
// La fase, el capitulo y los segundos desde la ultima actividad llegan del servidor; aqui
// solo se decide si se avisa, comparando con un umbral de presentacion. Sin progreso
// (404) no se pinta nada: no se inventa una fase.
export function Progreso({ obra, intervaloMs = INTERVALO_DE_PROGRESO_MS }: {
  obra: string; intervaloMs?: number;
}) {
  const cliente = useCliente();
  const [p, setP] = useState<ProgresoDeGeneracion | null>(null);
  useEffect(() => {
    let vivo = true;
    const leer = () => cliente.progreso(obra).then(
      (d) => { if (vivo) setP(d); }, () => { if (vivo) setP(null); });
    leer();
    const id = setInterval(leer, intervaloMs);
    return () => { vivo = false; clearInterval(id); };
  }, [cliente, obra, intervaloMs]);
  if (!p) return null;
  const minutos = Math.floor(p.segundos_desde_la_ultima_actividad / 60);
  const quieta = p.segundos_desde_la_ultima_actividad >= UMBRAL_SIN_ACTIVIDAD_SEGUNDOS;
  const capitulo = p.capitulo;
  const total = p.total_de_capitulos;
  return (
    <section className="progreso tarjeta" data-testid="progreso" data-fase={p.fase}>
      <div className="progreso__cabecera">
        <EtiquetaDeEstado distintivo={FASE_DE_GENERACION[p.fase]} />
        {capitulo !== null && total !== null && <span>capítulo {capitulo} de {total}</span>}
        {p.motivo && <span className="progreso__motivo">motivo: {p.motivo}</span>}
        {quieta && (
          <span className="progreso__quieta" role="status">
            sin actividad desde hace {minutos} min
          </span>
        )}
      </div>
      {capitulo !== null && total !== null && (
        <div className="progreso__barra" role="progressbar" aria-valuemin={0}
          aria-valuenow={capitulo} aria-valuemax={total} aria-label="capítulos">
          <div className="progreso__relleno" style={{ width: `${(100 * capitulo) / total}%` }} />
        </div>
      )}
    </section>
  );
}
