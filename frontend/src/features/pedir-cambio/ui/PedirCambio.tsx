import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Progreso } from "@/entities/progreso";
import {
  motivoDelError, useCliente, useLectura, type EscenaLeida, type Fichas, type HechosDeEscena,
  type Indice, type PeticionEntrada, type Propuesta, type Trabajo,
} from "@/shared/api";
import { INTERVALO_DE_TRABAJO_MS } from "@/shared/config";
import { ESTADO_DE_TRABAJO, EtiquetaDeEstado } from "@/shared/ui";
import "./pedir-cambio.css";

// Pedir un cambio desde la pagina (SPEC-22 RF-47..RF-51, RF-55; SPEC-23 D-3).
//
// La seleccion vive aqui y **no viaja**: lo que se manda es el hecho o el personaje que el
// lector elige y sus palabras (PLAN-22, reparto con PLAN-23). Que capitulos se tocan lo
// decide el backend (RF-50): la interfaz los enseña **antes** de ofrecer confirmar (RF-51)
// y al confirmar devuelve exactamente la lista que recibio. La promesa y su punto ciego se
// pintan tal como llegan, juntos. Un 409 se enseña con el motivo que da el backend.

type Clase = "hecho" | "nombre";
type EscenaParaPedir = Pick<EscenaLeida, "id" | "borrador" | "personajes_presentes">;

const TERMINALES = new Set(["terminado", "fallido", "abandonado", "detenido_por_presupuesto"]);

export function PedirCambio({ obra, escena, fragmento, onCerrar,
  intervaloMs = INTERVALO_DE_TRABAJO_MS }: {
  obra: string;
  escena: EscenaParaPedir;
  fragmento: string | null;
  onCerrar?: () => void;
  intervaloMs?: number;
}) {
  const cliente = useCliente();
  const hechos = useLectura((c) => c.hechosDeEscena(escena.id), escena.id);
  const fichas = useLectura((c) => c.fichas(obra), `fichas:${obra}`);
  const indice = useLectura((c) => c.indice(obra), `indice:${obra}`);

  const [clase, setClase] = useState<Clase>("hecho");
  const [hecho, setHecho] = useState<string | null>(null);
  const [enunciado, setEnunciado] = useState("");
  const [personaje, setPersonaje] = useState<string | null>(null);
  const [nombre, setNombre] = useState("");
  const [texto, setTexto] = useState("");
  const [propuesta, setPropuesta] = useState<Propuesta | null>(null);
  const [negativa, setNegativa] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [idTrabajo, setIdTrabajo] = useState<string | null>(null);

  const peticion = (): PeticionEntrada | null => {
    if (!texto.trim()) return null;
    if (clase === "hecho" && hecho && enunciado.trim()) {
      return { clase, hecho, enunciado_nuevo: enunciado.trim(), texto: texto.trim() };
    }
    if (clase === "nombre" && personaje && nombre.trim()) {
      return { clase, personaje, nombre_nuevo: nombre.trim(), texto: texto.trim() };
    }
    return null;
  };

  // Cambiar lo pedido invalida lo propuesto: no se confirma una propuesta de otra peticion.
  const cambiar = <T,>(f: (v: T) => void) => (v: T) => {
    f(v); setPropuesta(null); setNegativa(null);
  };

  async function proponer() {
    const p = peticion();
    if (!p) return;
    setEnviando(true); setNegativa(null); setPropuesta(null);
    try {
      setPropuesta(await cliente.proponerCambio(obra, p));
    } catch (e) {
      setNegativa(motivoDelError(e));
    } finally {
      setEnviando(false);
    }
  }

  async function confirmar() {
    const p = peticion();
    if (!p || !propuesta?.capitulos_propuestos) return;
    setEnviando(true); setNegativa(null);
    try {
      const r = await cliente.pedirCambio(obra, {
        ...p, version_de_partida: propuesta.version_de_partida,
        capitulos_propuestos: propuesta.capitulos_propuestos,
      });
      setIdTrabajo(r.id_trabajo);
    } catch (e) {
      setNegativa(motivoDelError(e));
    } finally {
      setEnviando(false);
    }
  }

  const nombreDe = (i: Indice | null) => (id: string) => {
    const c = i?.capitulos.find((x) => x.id === id);
    return c ? `Capítulo ${c.orden}` : id;
  };
  const capitulo = nombreDe(indice.estado === "listo" ? indice.datos : null);

  return (
    <section className="pedir-cambio tarjeta" aria-label="Pedir un cambio" data-testid="pedir-cambio">
      <header className="pedir-cambio__cabecera">
        <h2>Pedir un cambio</h2>
        {onCerrar && <button type="button" className="boton boton--secundario"
          onClick={onCerrar}>Cerrar</button>}
      </header>

      {fragmento
        ? <blockquote className="pedir-cambio__fragmento">
            <span className="pedir-cambio__rotulo">Fragmento seleccionado
              {escena.borrador ? ` (borrador v${escena.borrador.version})` : ""}</span>
            <p>{fragmento}</p>
          </blockquote>
        : <p className="pedir-cambio__nota">Sin fragmento seleccionado: el cambio se pide
            sobre esta escena.</p>}

      {idTrabajo === null && <>
        <p className="pedir-cambio__nota">
          Elige qué cambia: un hecho que usa esta escena o el nombre de alguien que aparece.
        </p>
        <div role="tablist" className="pedir-cambio__pestanas">
          {(["hecho", "nombre"] as Clase[]).map((c) => (
            <button key={c} type="button" role="tab" aria-selected={clase === c}
              className={`pestana ${clase === c ? "pestana--activa" : ""}`}
              onClick={() => cambiar(setClase)(c)}>
              {c === "hecho" ? "Un hecho" : "Un nombre"}
            </button>
          ))}
        </div>

        {clase === "hecho"
          ? <ElegirHecho lectura={hechos} elegido={hecho} onElegir={cambiar(setHecho)}
              enunciado={enunciado} onEnunciado={cambiar(setEnunciado)} />
          : <ElegirPersonaje presentes={escena.personajes_presentes}
              fichas={fichas.estado === "listo" ? fichas.datos : null}
              elegido={personaje} onElegir={cambiar(setPersonaje)}
              nombre={nombre} onNombre={cambiar(setNombre)} />}

        <label className="campo">
          <span>Con tus palabras, qué quieres cambiar</span>
          <textarea rows={3} value={texto}
            onChange={(e) => cambiar(setTexto)(e.target.value)} />
        </label>

        <div className="pedir-cambio__acciones">
          <button type="button" className="boton boton--secundario"
            disabled={!peticion() || enviando} onClick={proponer}>
            Ver qué capítulos se tocarían
          </button>
        </div>
      </>}

      {negativa && <p role="alert" className="aviso">No se puede: {negativa}</p>}

      {propuesta && idTrabajo === null &&
        <VistaPropuesta propuesta={propuesta} capitulo={capitulo}
          indice={indice.estado === "listo" ? indice.datos : null}
          enviando={enviando} onConfirmar={confirmar} />}

      {idTrabajo !== null &&
        <Seguimiento obra={obra} idTrabajo={idTrabajo} intervaloMs={intervaloMs} />}
    </section>
  );
}

function ElegirHecho({ lectura, elegido, onElegir, enunciado, onEnunciado }: {
  lectura: ReturnType<typeof useLectura<HechosDeEscena>>;
  elegido: string | null;
  onElegir: (id: string) => void;
  enunciado: string;
  onEnunciado: (v: string) => void;
}) {
  if (lectura.estado === "cargando") return <p className="cargando">cargando los hechos…</p>;
  if (lectura.estado === "error") {
    return <p role="alert" className="aviso">No llegaron los hechos de la escena ({lectura.mensaje}).</p>;
  }
  const lista = lectura.datos.hechos_que_usa;
  if (lista.length === 0) {
    return <p className="vacio">Esta escena no usa ningún hecho declarado.</p>;
  }
  return (
    <fieldset className="pedir-cambio__opciones">
      <legend>Los hechos que usa esta escena</legend>
      {lista.map((h) => (
        <label key={h.id} className={`opcion ${elegido === h.id ? "opcion--elegida" : ""}`}>
          <input type="radio" name="hecho" value={h.id} checked={elegido === h.id}
            onChange={() => onElegir(h.id)} />
          <span>{h.enunciado}</span>
        </label>
      ))}
      <label className="campo">
        <span>Cómo debería ser</span>
        <input type="text" value={enunciado} onChange={(e) => onEnunciado(e.target.value)} />
      </label>
    </fieldset>
  );
}

function ElegirPersonaje({ presentes, fichas, elegido, onElegir, nombre, onNombre }: {
  presentes: string[] | null;
  fichas: Fichas | null;
  elegido: string | null;
  onElegir: (id: string) => void;
  nombre: string;
  onNombre: (v: string) => void;
}) {
  if (presentes === null) {
    return <p className="vacio">La escena no declara quién está presente: no hay a quién
      ofrecer para renombrar.</p>;
  }
  if (presentes.length === 0) return <p className="vacio">No hay nadie presente en esta escena.</p>;
  const nombreDe = (id: string) =>
    fichas?.personajes.find((p) => p.id === id)?.nombre_canonico ?? null;
  return (
    <fieldset className="pedir-cambio__opciones">
      <legend>Quién aparece en esta escena</legend>
      {presentes.map((id) => {
        const n = nombreDe(id);
        return (
          <label key={id} className={`opcion ${elegido === id ? "opcion--elegida" : ""}`}>
            <input type="radio" name="personaje" value={id} checked={elegido === id}
              onChange={() => onElegir(id)} />
            <span>{n ?? id}{n === null && <em className="sin-dato"> (sin nombre guardado)</em>}</span>
          </label>
        );
      })}
      <label className="campo">
        <span>Nombre nuevo</span>
        <input type="text" value={nombre} onChange={(e) => onNombre(e.target.value)} />
      </label>
    </fieldset>
  );
}

// SPEC-35 RF-09: la propuesta como una balda. Los capitulos de la obra en su orden, y resaltados
// **exactamente** los que el backend propone. Uno propuesto que no este en el indice tambien sale:
// esconderlo haria confirmar algo que no se ha visto.
function Balda({ indice, propuestos, capitulo }: {
  indice: Indice; propuestos: string[]; capitulo: (id: string) => string;
}) {
  const enElIndice = new Set(indice.capitulos.map((c) => c.id));
  const ids = [...indice.capitulos.map((c) => c.id), ...propuestos.filter((id) => !enElIndice.has(id))];
  const tocados = new Set(propuestos);
  return (
    <ol className="balda" data-testid="balda">
      {ids.map((id) => {
        const toca = tocados.has(id);
        return (
          <li key={id} data-capitulo={id}
            data-testid={toca ? "capitulo-que-se-toca" : "capitulo-que-no-se-toca"}
            className={`balda__lomo${toca ? " balda__lomo--se-toca" : ""}`}>
            <span className="balda__titulo">{capitulo(id)}</span>
            {toca && <span className="balda__marca">se reescribe</span>}
          </li>
        );
      })}
    </ol>
  );
}

function ListaDeCapitulos({ ids, capitulo }: { ids: string[]; capitulo: (id: string) => string }) {
  return (
    <ol className="pedir-cambio__capitulos">
      {ids.map((id) => (
        <li key={id} data-testid="capitulo-que-se-toca" data-capitulo={id}>{capitulo(id)}</li>
      ))}
    </ol>
  );
}

function VistaPropuesta({ propuesta, capitulo, indice, enviando, onConfirmar }: {
  propuesta: Propuesta;
  capitulo: (id: string) => string;
  indice: Indice | null;
  enviando: boolean;
  onConfirmar: () => void;
}) {
  const lista = propuesta.capitulos_propuestos;
  return (
    <div className="propuesta" data-testid="propuesta">
      {lista
        ? <>
            <h3>{lista.length === 1 ? "Para que la historia siga encajando, se reescribiría 1 capítulo"
              : `Para que la historia siga encajando, se reescribirían ${lista.length} capítulos`}</h3>
            {indice
              ? <Balda indice={indice} propuestos={lista} capitulo={capitulo} />
              : <ListaDeCapitulos ids={lista} capitulo={capitulo} />}
          </>
        : <>
            <h3>Todavía no se sabe qué capítulos se reescribirían</h3>
            <p className="aviso">{propuesta.motivo}</p>
            <p className="pedir-cambio__nota">Según cómo se regenere:</p>
            <h4>En cascada, desde el primero afectado</h4>
            <ListaDeCapitulos ids={propuesta.capitulos.cascada} capitulo={capitulo} />
            <h4>Solo los que usan lo que cambia</h4>
            <ListaDeCapitulos ids={propuesta.capitulos.selectiva} capitulo={capitulo} />
          </>}
      <div className="promesa">
        <p data-testid="promesa"><strong>Lo que prometemos:</strong> {propuesta.promesa}</p>
        <p data-testid="punto-ciego"><strong>Lo que no cubre:</strong> {propuesta.punto_ciego}</p>
      </div>
      {lista && (
        <div className="pedir-cambio__acciones">
          <button type="button" className="boton boton--principal" disabled={enviando}
            onClick={onConfirmar}>Confirmar el cambio</button>
          <span className="pedir-cambio__nota">Se creará una versión nueva; la actual se
            podrá seguir leyendo entera.</span>
        </div>
      )}
    </div>
  );
}

function Seguimiento({ obra, idTrabajo, intervaloMs }: {
  obra: string; idTrabajo: string; intervaloMs: number;
}) {
  const cliente = useCliente();
  const [trabajo, setTrabajo] = useState<Trabajo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const terminado = trabajo !== null && TERMINALES.has(trabajo.estado);
  useEffect(() => {
    if (terminado) return;
    let vivo = true;
    const leer = () => cliente.trabajo(idTrabajo).then(
      (t) => { if (vivo) { setTrabajo(t); setError(null); } },
      (e: unknown) => { if (vivo) setError(motivoDelError(e)); });
    leer();
    const id = setInterval(leer, intervaloMs);
    return () => { vivo = false; clearInterval(id); };
  }, [cliente, idTrabajo, intervaloMs, terminado]);
  const o = encodeURIComponent(obra);
  return (
    <div className="seguimiento" data-testid="seguimiento" aria-live="polite">
      <h3>Tu petición está en marcha</h3>
      {trabajo
        ? <p className="seguimiento__estado">
            <EtiquetaDeEstado distintivo={ESTADO_DE_TRABAJO[trabajo.estado]} />
          </p>
        : <p className="cargando">consultando el trabajo…</p>}
      {trabajo?.motivo && <p className="aviso">Motivo: {trabajo.motivo}</p>}
      {error && <p role="alert" className="aviso">No se pudo consultar el trabajo: {error}</p>}
      {trabajo?.estado === "terminado" && (
        <p><Link className="boton boton--principal" to={`/obras/${o}/indice`}>
          Leer la versión nueva</Link></p>
      )}
      <Progreso obra={obra} />
    </div>
  );
}
