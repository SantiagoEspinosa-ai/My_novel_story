import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  motivoDelError, useCliente, useLectura, type AccionesDeObra as Acciones, type ConfirmacionDeGasto,
} from "@/shared/api";
import { INTERVALO_DE_REGALO_MS } from "@/shared/config";
import { EtiquetaDeEstado, FASE_DE_GENERACION } from "@/shared/ui";
import "./acciones-de-obra.css";

// Publicar y reanudar una novela (SPEC-39). Si se puede, por que no, desde donde y cuanto lo
// resuelve el backend; aqui se ensena, y nada que gaste se lanza sin decirlo antes.
export function AccionesDeObra({ obra, intervaloMs = INTERVALO_DE_REGALO_MS }: {
  obra: string; intervaloMs?: number;
}) {
  const lectura = useLectura((c) => c.acciones(obra), `acciones:${obra}`);
  if (lectura.estado !== "listo") return null;
  const a = lectura.datos;
  // Publicar se ensena si se puede, o si lo unico que falta es Lean (RF-03): hay que decirlo.
  const publicar = a.publicar.posible || (!a.publicar.lean_disponible && a.publicar.motivo === a.publicar.lean_motivo);
  const reanudar = a.reanudar.posible || (a.reanudar.motivo ?? "").startsWith("lo gastado");
  if (!publicar && !reanudar) return null;
  return (
    <div className="acciones-de-obra">
      {publicar && <Publicar obra={obra} a={a} intervaloMs={intervaloMs} />}
      {reanudar && <Reanudar obra={obra} a={a} />}
    </div>
  );
}

function usd(n: number) {
  return `${n.toFixed(2).replace(".", ",")} USD`;
}

type Resultado = {
  publicada: boolean; ronda: number; version: number;
  condiciones: { invariante: string; capitulo: string | null; detalle: string }[];
  lean: { codigo: number | null; detalle: string | null };
};

function Publicar({ obra, a, intervaloMs }: { obra: string; a: Acciones; intervaloMs: number }) {
  const cliente = useCliente();
  const [enCurso, setEnCurso] = useState(false);
  const [resultado, setResultado] = useState<Resultado | null>(null);
  const [error, setError] = useState<string | null>(null);
  const p = a.publicar;

  async function publicar() {
    setError(null);
    setEnCurso(true);
    try {
      const { id_trabajo } = await cliente.publicar(obra);
      for (;;) {
        const t = await cliente.trabajo(id_trabajo);
        if (t.estado === "terminado") { setResultado(t.resultado as Resultado); break; }
        if (["fallido", "abandonado"].includes(t.estado)) throw new Error(t.motivo ?? t.estado);
        await new Promise((r) => setTimeout(r, intervaloMs));
      }
    } catch (e) {
      setError(motivoDelError(e));
    } finally {
      setEnCurso(false);
    }
  }

  return (
    <section className="tarjeta acciones-de-obra__bloque" data-testid="publicar">
      <h2>Publicar la novela</h2>
      <p>
        Todos los capítulos de la versión {p.version} están escritos. Publicar la pasa por la puerta
        de publicación: Lean comprueba la cronología y <strong>el Editor juzga la obra entera, que es
        una delegación y gasta dinero</strong>
        {p.coste_medio_del_editor === null
          ? " (el Editor todavía no tiene coste medido en esta base)."
          : ` (en esta base, ${usd(p.coste_medio_del_editor)} de media en ${p.delegaciones_medidas_del_editor} delegaciones).`}
        {" "}No reescribe nada: si no pasa, dice qué falló.
      </p>
      {!p.lean_disponible ? (
        <p role="alert" className="aviso">{p.lean_motivo}</p>
      ) : !resultado && (
        <button type="button" className="boton boton--principal" disabled={enCurso}
          onClick={() => void publicar()}>
          {enCurso ? "Pasando por la puerta…" : "Publicar (gasta una delegación del Editor)"}
        </button>
      )}
      {error && <p role="alert" className="aviso">No se pudo publicar: {error}</p>}
      {resultado && (
        <div data-testid="resultado-publicar" className="acciones-de-obra__resultado">
          {resultado.publicada ? (
            <>
              <p><EtiquetaDeEstado distintivo={FASE_DE_GENERACION.publicada} />
                {" "}La versión {resultado.version} está publicada (Lean {resultado.lean.codigo}).</p>
              <Link className="boton boton--principal" to={`/obras/${encodeURIComponent(obra)}`}>Leer la novela</Link>
            </>
          ) : (
            <>
              <p><strong>No se publicó</strong> (ronda {resultado.ronda}). Lo que falló:</p>
              <ul>
                {resultado.condiciones.map((c, i) => (
                  <li key={i}><strong>{c.invariante}</strong>{c.capitulo ? ` (${c.capitulo})` : " (obra)"}: {c.detalle}</li>
                ))}
              </ul>
              <p>Lean {resultado.lean.codigo ?? "no se pudo ejecutar"}{resultado.lean.detalle ? `: ${resultado.lean.detalle}` : ""}</p>
            </>
          )}
        </div>
      )}
    </section>
  );
}

function Reanudar({ obra, a }: { obra: string; a: Acciones }) {
  const cliente = useCliente();
  const navegar = useNavigate();
  const [g, setG] = useState<ConfirmacionDeGasto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lanzando, setLanzando] = useState(false);
  const r = a.reanudar;

  useEffect(() => {
    let vivo = true;
    cliente.gasto().then((d) => { if (vivo) setG(d); },
      (e: unknown) => { if (vivo) setError(motivoDelError(e)); });
    return () => { vivo = false; };
  }, [cliente]);

  async function reanudar() {
    setError(null);
    setLanzando(true);
    try {
      await cliente.lanzar(obra);
      navegar(`/obras/${encodeURIComponent(obra)}/generacion`);
    } catch (e) {
      setError(motivoDelError(e));
      setLanzando(false);
    }
  }

  return (
    <section className="tarjeta acciones-de-obra__bloque" data-testid="reanudar">
      <h2>Reanudar la novela</h2>
      {r.posible ? (
        <>
          <p>Se paró a medias. Seguirá <strong>desde el capítulo {r.desde_capitulo}</strong>: faltan {r.faltan} capítulos.
            Lo ya consolidado no se vuelve a escribir.</p>
          {r.estimacion_usd !== null && r.coste_por_capitulo !== null && (
            <p>Estimación: {r.faltan} × {usd(r.coste_por_capitulo)} ≈ <strong>{usd(r.estimacion_usd)}</strong>, con {r.fuente}.
              Es una estimación, no un precio, y la puerta del final se paga aparte.</p>
          )}
          <p className="acciones-de-obra__nota">Si la causa de la parada sigue, puede volver a pararse en el mismo capítulo, después de gastar sus intentos.</p>
          {g && <p>Gastado en esta base: {g.gastado.usd === null ? "sin medir" : usd(g.gastado.usd)} de {usd(g.techo_usd).replace(",00", "")} (como mínimo).</p>}
          <button type="button" className="boton boton--principal" disabled={!g || g.alcanzado || lanzando}
            onClick={() => void reanudar()}>Sí, reanudar (gasta dinero)</button>
        </>
      ) : <p role="alert" className="aviso">{r.motivo}</p>}
      {error && <p role="alert" className="aviso">{error}</p>}
    </section>
  );
}
