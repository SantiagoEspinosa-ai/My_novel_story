import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  useLectura, type EventoDeLaHistoria, type HistoriaDeObra, type MatrizDeObra,
} from "@/shared/api";
import { ESTADO_DE_ESCENA, EtiquetaDeEstado, Esperando, SEVERIDAD, SinDato } from "@/shared/ui";
import { usd } from "./formato";
import { Matriz } from "./Matriz";
import "./historia-de-obra.css";

// La pagina de cada novela en la administracion. SPEC-38: se abre en la matriz por capitulo, y
// la linea de tiempo de SPEC-37 es la segunda pestana (`?vista=linea`). La version de la matriz
// va en `?version=N`, para poder enlazarla. La pagina no ordena, no suma ni atribuye: pinta.
export function PaginaHistoriaDeObra() {
  const { obra = "" } = useParams();
  const [params] = useSearchParams();
  const linea = params.get("vista") === "linea";
  const version = params.get("version");
  return (
    <main className="contenido historia">
      <p className="migas"><Link to="/admin">Administración</Link></p>
      <nav className="historia__pestanas" aria-label="vistas">
        <Link to="?" aria-current={linea ? undefined : "page"}
          className={linea ? "historia__pestana" : "historia__pestana historia__pestana--elegida"}>
          Por capítulo</Link>
        <Link to="?vista=linea" aria-current={linea ? "page" : undefined}
          className={linea ? "historia__pestana historia__pestana--elegida" : "historia__pestana"}>
          Línea de tiempo</Link>
      </nav>
      {linea ? <LineaDeTiempo obra={obra} />
        : <PorCapitulo obra={obra} version={version === null ? undefined : Number(version)} />}
    </main>
  );
}

function PorCapitulo({ obra, version }: { obra: string; version?: number }) {
  const lectura = useLectura((c) => c.matriz(obra, version), `matriz:${obra}:${version ?? "vigente"}`);
  return (
    <Esperando lectura={lectura}>
      {(m: MatrizDeObra) => <Matriz m={m} vista={(v) => `?version=${v}`} />}
    </Esperando>
  );
}

function LineaDeTiempo({ obra }: { obra: string }) {
  const lectura = useLectura((c) => c.historia(obra), `historia:${obra}`);
  return <Esperando lectura={lectura}>{(h: HistoriaDeObra) => <Historia h={h} />}</Esperando>;
}

function Historia({ h }: { h: HistoriaDeObra }) {
  return (
    <div className="historia__cuerpo">
      <section>
        <h1><SinDato valor={h.titulo} ausente="sin título todavía">{(t) => t}</SinDato></h1>
        <p className="historia__sub">Lo que ha pasado con esta novela, en orden.</p>
        <ol className="historia__linea">
          {h.eventos.map((e, i) => <Evento key={i} e={e} n={i} />)}
        </ol>
        <p className="historia__atribucion" data-testid="atribucion">{h.atribucion}</p>
      </section>
      <aside className="historia__lado" data-testid="totales">
        <div className="tarjeta">
          <h2>Totales</h2>
          <dl>
            <dt>Coste</dt><dd>{usd(h.totales.coste) ?? <span className="sin-dato">sin gasto</span>}</dd>
            <dt>Delegaciones</dt><dd>{h.totales.coste?.delegaciones ?? 0}</dd>
            <dt>Nota media</dt><dd>{h.totales.nota_media === null ? <span className="sin-dato">sin notas</span>
              : h.totales.nota_media.toFixed(1).replace(".", ",")}</dd>
            <dt>Paradas</dt><dd>{h.totales.paradas}</dd>
            <dt>Versión vigente</dt><dd>{h.totales.version_vigente ?? "—"}</dd>
          </dl>
        </div>
        <div className="tarjeta">
          <h2>Por agente</h2>
          {h.por_agente.length === 0 ? <p className="sin-dato">sin gasto</p> : (
            <dl>{h.por_agente.map((a) => (
              <div key={a.agente} className="historia__par"><dt>{a.agente}</dt><dd>{usd(a)}</dd></div>
            ))}</dl>
          )}
        </div>
        <div className="tarjeta">
          <h2>Abiertos ahora</h2>
          {h.abiertos.length === 0 ? <p>Ninguno.</p> : (
            <ul className="historia__abiertos">{h.abiertos.map((a, i) => (
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
  );
}

const TONO: Record<string, string> = {
  entrevista: "bien", ronda_del_plan: "neutro", capitulo: "bien", parada: "mal",
  ronda_de_la_puerta: "neutro", version: "version",
};

function Evento({ e, n }: { e: EventoDeLaHistoria; n: number }) {
  const tono = e.tipo === "ronda_de_la_puerta" || e.tipo === "ronda_del_plan"
    ? (e.aprobado ? "bien" : "mal") : TONO[e.tipo] ?? "neutro";
  return (
    <li className={`historia__evento historia__evento--${tono}`} data-testid={`evento-${n}`}
      data-tipo={e.tipo}>
      <span className="historia__cuando">{e.cuando ?? "sin hora"}{e.coste && <> · {usd(e.coste)}</>}</span>
      <div className="tarjeta historia__tarjeta"><Contenido e={e} /></div>
    </li>
  );
}

function Contenido({ e }: { e: EventoDeLaHistoria }) {
  const intentos = e.intentos === null ? null : `${e.intentos} ${e.intentos === 1 ? "intento" : "intentos"}`;
  switch (e.tipo) {
    case "entrevista":
      return <h3>Entrevista {e.aprobado ? "cerrada" : "sin cerrar"}</h3>;
    case "ronda_del_plan":
      return (
        <>
          <h3>Plan · ronda {e.ronda} <Marca bien={!!e.aprobado} si="aprobado" no="devuelto" /></h3>
          {e.objeciones.length > 0 && <ul className="historia__lista">{e.objeciones.map((o) => <li key={o}>{o}</li>)}</ul>}
        </>
      );
    case "capitulo":
      return (
        <>
          <h3>Capítulo {e.capitulo}{e.version !== null && e.version > 1 && <> · versión {e.version}</>}
            {e.escenas.map((s) => <EtiquetaDeEstado key={s.id} distintivo={ESTADO_DE_ESCENA[s.estado]} />)}
            {intentos && <span className="historia__intentos">{intentos}</span>}
          </h3>
          {e.notas.length > 0 ? (
            <ul className="historia__notas">{e.notas.map((nota) => (
              <li key={nota.criterio} data-testid={`nota-${nota.criterio}`}
                className={nota.bajo_el_umbral ? "historia__nota historia__nota--baja" : "historia__nota"}
                title={nota.justificacion}>
                {nota.criterio.replace(/_/g, " ")} <strong>{nota.nota}</strong>
                {nota.bajo_el_umbral && " · bajo el umbral"}
              </li>
            ))}</ul>
          ) : <p className="sin-dato">sin notas del Editor todavía</p>}
        </>
      );
    case "parada":
      return (
        <h3>Parada en el capítulo {e.capitulo} <Marca bien={false} si="" no={e.motivo ?? "sin motivo"} />
          {intentos && <span className="historia__intentos">{intentos}</span>}</h3>
      );
    case "ronda_de_la_puerta":
      return (
        <>
          <h3>Puerta de publicación · ronda {e.ronda}{e.version !== null && <> · versión {e.version}</>}{" "}
            <Marca bien={!!e.aprobado} si="publica" no="no publica" /></h3>
          <p>Lean {e.codigo_lean ?? "sin ejecutar"}{e.codigo_lean === 0 ? " (pasa)" : ""}</p>
          {e.condiciones.length > 0 && <ul className="historia__lista">{e.condiciones.map((c) => <li key={c}>{c}</li>)}</ul>}
        </>
      );
    case "version":
      return (
        <>
          <h3>Versión {e.version}</h3>
          <p>{e.peticion ? <>Por la petición «{e.peticion}»</> : <span className="sin-dato">sin petición guardada</span>}</p>
          <p>Cambian los capítulos {e.capitulos_cambiados.join(", ")}</p>
        </>
      );
    default:
      return <h3>{e.tipo}</h3>;
  }
}

function Marca({ bien, si, no }: { bien: boolean; si: string; no: string }) {
  return <EtiquetaDeEstado distintivo={bien ? ESTADO_DE_ESCENA.aceptada : SEVERIDAD.bloqueante}
    texto={bien ? si : no} />;
}
