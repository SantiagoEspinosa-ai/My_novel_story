import { Link } from "react-router-dom";
import { AccionesDeObra } from "@/features/acciones-de-obra";
import type { FilaDeLaMatriz, MatrizDeObra } from "@/shared/api";
import { ESTADO_DE_ESCENA, EtiquetaDeEstado, NOTA_DEL_EDITOR, SEVERIDAD, SinDato } from "@/shared/ui";
import { euros, usd } from "./formato";

// La matriz por capitulo (SPEC-38): una fila por capitulo de la version elegida, con las seis
// notas en color y escritas, el coste, los intentos, los hallazgos y si cambio. Medias y
// totales llegan resueltos del backend: aqui no se suma nada.
const CORTO: Record<string, string> = {
  continuidad: "cont.", tono: "tono", arco: "arco", coherencia_de_personajes: "pers.",
  ritmo: "ritmo", personalizacion: "perso.",
};

function hallazgos(h: FilaDeLaMatriz["hallazgos"]) {
  const t = (["bloqueante", "mayor", "menor"] as const).filter((s) => h[s] > 0)
    .map((s) => `${h[s]} ${s}`).join(" · ");
  return t || "—";
}

export function Matriz({ m, vista }: { m: MatrizDeObra; vista: (v: number) => string }) {
  const g = m.cifras.gastado;
  return (
    <>
      <h1><SinDato valor={m.titulo} ausente="sin título todavía">{(t) => t}</SinDato></h1>
      <div className="matriz__cifras" data-testid="cifras">
        <div className="tarjeta"><span>Coste</span>
          <strong>{usd(m.cifras.coste) ?? <span className="sin-dato">sin gasto</span>}</strong></div>
        <div className="tarjeta"><span>Delegaciones</span>
          <strong>{m.cifras.coste?.delegaciones ?? 0}</strong></div>
        <div className="tarjeta"><span>Gastado en la base</span>
          <strong>{g.usd === null ? "sin medir" : euros(g.usd)} de {euros(m.cifras.techo_usd).replace(",00", "")}</strong>
          <small>como mínimo</small></div>
        <div className="tarjeta"><span>Hallazgos abiertos</span><strong>{m.cifras.abiertos}</strong></div>
      </div>

      {/* SPEC-39: publicar o reanudar, debajo de las cifras. */}
      <AccionesDeObra obra={m.obra} />

      <nav className="matriz__versiones" aria-label="versiones">
        <span>Versión:</span>
        {m.versiones.map((v) => (
          <Link key={v.numero} to={vista(v.numero)} aria-current={v.numero === m.version ? "page" : undefined}
            className={v.numero === m.version ? "matriz__version matriz__version--elegida" : "matriz__version"}>
            Versión {v.numero}{v.peticion && <> · «{v.peticion}»</>}
          </Link>
        ))}
      </nav>

      <div className="matriz__cuerpo">
        <section>
          <div className="matriz__tabla-caja">
            <table className="matriz__tabla">
              <thead>
                <tr className="matriz__grupo">
                  <th />
                  <th colSpan={6}>Notas del Editor</th>
                  <th colSpan={4}>El capítulo</th>
                </tr>
                <tr>
                  <th>Capítulo</th>
                  {/* Sin filas (nada escrito todavia) los criterios siguen siendo los seis de INV-26. */}
                  {(m.filas[0]?.notas.map((n) => n.criterio) ?? Object.keys(CORTO)).map((c) =>
                    <th key={c} title={c}>{CORTO[c] ?? c}</th>)}
                  <th>Coste</th><th>Intentos</th><th>Hallazgos</th><th>En v{m.version}</th>
                </tr>
              </thead>
              <tbody>
                {m.filas.map((f) => (
                  <tr key={f.capitulo} data-testid={`fila-${f.capitulo}`}
                    className={f.parada ? "matriz__fila matriz__fila--parada" : "matriz__fila"}>
                    <td className="matriz__capitulo">
                      {f.capitulo}
                      {f.parada && <EtiquetaDeEstado distintivo={SEVERIDAD.bloqueante} texto="parada" />}
                      {f.escenas.map((e) => <EtiquetaDeEstado key={e.id} distintivo={ESTADO_DE_ESCENA[e.estado]} />)}
                    </td>
                    {f.notas.map((n) => {
                      const d = n.nota === null ? null : NOTA_DEL_EDITOR[String(n.nota) as keyof typeof NOTA_DEL_EDITOR];
                      return (
                        <td key={n.criterio} data-testid={`celda-${n.criterio}`}
                          data-nota={n.nota ?? "sin_nota"} className="matriz__nota"
                          title={n.justificacion ?? "sin nota todavía"}
                          style={d ? { background: d.fondo, color: d.texto } : undefined}>
                          {n.nota ?? "—"}
                        </td>
                      );
                    })}
                    <td>{usd(f.coste) ?? "—"}</td>
                    <td>{f.intentos}</td>
                    <td>{hallazgos(f.hallazgos)}</td>
                    <td>{f.cambio === null ? "—" : f.cambio ? <strong>cambió</strong> : "igual"}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr data-testid="fila-totales" className="matriz__totales">
                  <td>Media / total</td>
                  {m.totales.medias.map((x, i) => <td key={i}>{x === null ? "—" : x.toFixed(1).replace(".", ",")}</td>)}
                  <td>{usd(m.totales.coste) ?? "—"}</td>
                  <td>{m.totales.intentos}</td>
                  <td>{hallazgos(m.totales.hallazgos)}</td>
                  <td>{m.totales.cambiados === null ? "—" : `${m.totales.cambiados} de ${m.filas.length}`}</td>
                </tr>
              </tfoot>
            </table>
          </div>

          <div className="matriz__leyenda" data-testid="leyenda">
            <span>Notas del Editor:</span>
            {Object.entries(NOTA_DEL_EDITOR).map(([k, d]) => (
              <span key={k} className="matriz__muestra">
                <i style={{ background: d.fondo, color: d.texto }}>{k}</i>{d.etiqueta}
              </span>
            ))}
            <span className="matriz__muestra"><i>—</i>sin nota todavía</span>
          </div>
          <p className="historia__atribucion" data-testid="atribucion">{m.atribucion}</p>

          <div className="matriz__debajo">
            <div className="tarjeta" data-testid="paradas">
              <h2>Paradas</h2>
              {m.paradas.length === 0 ? <p>Ninguna en esta versión.</p> : (
                <table className="matriz__mini">
                  <thead><tr><th>Capítulo</th><th>Por qué</th><th>Intentos</th><th>Coste</th></tr></thead>
                  <tbody>{m.paradas.map((p, i) => (
                    <tr key={i}><td>{p.capitulo}</td><td>{p.motivo ?? "sin motivo"}</td>
                      <td>{p.intentos ?? "—"}</td><td>{usd(p.coste) ?? "—"}</td></tr>
                  ))}</tbody>
                </table>
              )}
            </div>
            <div className="tarjeta" data-testid="puerta">
              <h2>Puerta de publicación · versión {m.version}</h2>
              {m.puerta.length === 0 ? <p>Todavía no ha pasado por la puerta.</p> : (
                <table className="matriz__mini">
                  <thead><tr><th>Ronda</th><th>Lean</th><th>Resultado</th><th>Condiciones</th></tr></thead>
                  <tbody>{m.puerta.map((r, i) => (
                    <tr key={i}><td>{r.ronda}</td>
                      <td>Lean {r.codigo_lean ?? "sin ejecutar"}</td>
                      <td><EtiquetaDeEstado distintivo={r.aprobado ? ESTADO_DE_ESCENA.aceptada : SEVERIDAD.bloqueante}
                        texto={r.aprobado ? "publica" : "no publica"} /></td>
                      <td>{r.condiciones.length ? r.condiciones.join("; ") : "todas"}</td></tr>
                  ))}</tbody>
                </table>
              )}
            </div>
          </div>
        </section>

        <aside className="matriz__lado" data-testid="panel-lateral">
          <div className="tarjeta">
            <h2>Por agente</h2>
            {m.por_agente.length === 0 ? <p className="sin-dato">sin gasto</p> : (
              <dl>{m.por_agente.map((a) => (
                <div key={a.agente} className="historia__par"><dt>{a.agente}</dt><dd>{usd(a)}</dd></div>
              ))}</dl>
            )}
          </div>
          <div className="tarjeta">
            <h2>Abiertos ahora</h2>
            {m.abiertos.length === 0 ? <p>Ninguno.</p> : (
              <ul className="historia__abiertos">{m.abiertos.map((a, i) => (
                <li key={i}>
                  <EtiquetaDeEstado distintivo={SEVERIDAD[a.severidad]} /> <strong>{a.invariante}</strong>
                  {a.capitulo !== null && <> · cap. {a.capitulo}</>}
                  <span className="historia__desc">{a.descripcion}</span>
                </li>
              ))}</ul>
            )}
          </div>
        </aside>
      </div>
    </>
  );
}
