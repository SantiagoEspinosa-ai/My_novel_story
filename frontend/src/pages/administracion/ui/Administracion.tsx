import { Link } from "react-router-dom";
import { useLectura, type Administracion, type ObraEnLaAdministracion } from "@/shared/api";
import { EtiquetaDeEstado, Esperando, FASE_DE_GENERACION, SinDato } from "@/shared/ui";
import "./administracion.css";

// La administracion (SPEC-36 RF-03): todas las novelas con su fase, su coste, sus hallazgos
// abiertos y el ultimo codigo de Lean. Todo llega resuelto del backend. **Sin login**, por
// decision del autor: la pagina lo dice, para que nadie lo lea como un descuido.
export function PaginaAdministracion() {
  const lectura = useLectura((c) => c.administracion(), "administracion");
  return (
    <main className="contenido administracion">
      <h1>Administración</h1>
      <p role="note" className="aviso">
        Esta vista va sin login: cualquiera con la URL la ve. Es una decisión del autor
        mientras no haya usuarios (SPEC-36).
      </p>
      <Esperando lectura={lectura}>{(a: Administracion) => <Tabla a={a} />}</Esperando>
    </main>
  );
}

function usd(n: number) {
  return `${n.toFixed(2).replace(".", ",")} USD`;
}

function Tabla({ a }: { a: Administracion }) {
  const publicadas = a.obras.filter((o) => o.fase === "publicada").length;
  const abiertos = a.obras.reduce((s, o) => s + o.hallazgos.bloqueante + o.hallazgos.mayor
    + o.hallazgos.menor, 0);
  return (
    <>
      <div className="administracion__cifras">
        <div className="tarjeta" data-testid="admin-gastado">
          <span>Gastado en esta base</span>
          <strong>{a.gastado.usd === null ? "sin medir" : usd(a.gastado.usd)} de {usd(a.techo_usd).replace(",00", "")}</strong>
          <small>como mínimo: {a.gastado.por_que_es_suelo}</small>
        </div>
        <div className="tarjeta"><span>Novelas</span><strong>{a.obras.length}</strong>
          <small>{publicadas} publicadas</small></div>
        <div className="tarjeta"><span>Hallazgos abiertos</span><strong>{abiertos}</strong></div>
      </div>
      <table className="administracion__tabla">
        <thead>
          <tr><th>Novela</th><th>Fase</th><th>Coste</th><th>Delegaciones</th><th>Hallazgos abiertos</th><th>Lean</th></tr>
        </thead>
        <tbody>{a.obras.map((o) => <Fila key={o.id} o={o} />)}</tbody>
      </table>
    </>
  );
}

function Fila({ o }: { o: ObraEnLaAdministracion }) {
  const h = o.hallazgos;
  const partes = [["bloqueante", h.bloqueante], ["mayor", h.mayor], ["menor", h.menor]] as const;
  const texto = partes.filter(([, n]) => n > 0).map(([s, n]) => `${n} ${s}`).join(" · ");
  return (
    <tr data-testid={`admin-${o.id}`}>
      <td><Link to={`/obras/${encodeURIComponent(o.id)}`}>
        <SinDato valor={o.titulo} ausente="sin título todavía">{(t) => t}</SinDato></Link></td>
      <td>{o.fase ? <EtiquetaDeEstado distintivo={FASE_DE_GENERACION[o.fase]} />
        : <span className="sin-dato">sin generación</span>}</td>
      <td>{o.coste === null || o.coste.usd === null ? "—"
        : <>{usd(o.coste.usd)}{o.coste.es_suelo && <small> (como mínimo)</small>}</>}</td>
      <td>{o.coste === null ? "—" : o.coste.delegaciones}</td>
      <td>{texto || "0"}</td>
      <td>{o.codigo_lean === null ? "—" : o.codigo_lean}</td>
    </tr>
  );
}
