import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ConfirmarGeneracion } from "./ConfirmarGeneracion";
import { Cuaderno } from "./Cuaderno";
import { CuadernoCompleto } from "./CuadernoCompleto";
import { Entrevistadora } from "./Entrevistadora";
import { Turno } from "./Turno";
import { ErrorDeLaApi, useCliente, type Historial, type NombresEntrada } from "@/shared/api";
import { ENTREVISTADORA, INTERVALO_DE_REGALO_MS } from "@/shared/config";
import { EtiquetaDeEstado, SEVERIDAD } from "@/shared/ui";
import "./entrevista.css";

// La entrevista como conversacion (SPEC-33 RF-05..RF-10) con Xime y su cuaderno (SPEC-35
// RF-04..RF-07). Una pregunta cada vez y las anteriores encima. La conversacion es el historial
// del backend, asi que sobrevive a recargar; la pagina no calcula nada: si se puede cerrar lo
// dice `puede_cerrar`, y lo que sabe el cuaderno llega resuelto.
export function PaginaEntrevista({ intervaloMs = INTERVALO_DE_REGALO_MS }: {
  intervaloMs?: number;
}) {
  const { entrevista = "" } = useParams();
  const navegar = useNavigate();
  const cliente = useCliente();
  const [historial, setHistorial] = useState<Historial | null>(null);
  const [errorDeCarga, setErrorDeCarga] = useState<string | null>(null);
  const [respuesta, setRespuesta] = useState("");
  const [pensando, setPensando] = useState(false);
  const [fallo, setFallo] = useState<string | null>(null);
  const [rechazo, setRechazo] = useState<Rechazo | null>(null);
  const [quiereCambiar, setQuiereCambiar] = useState(false);

  const leer = useCallback(() => cliente.historial(entrevista).then(
    (h) => { setHistorial(h); setErrorDeCarga(null); },
    (e: unknown) => setErrorDeCarga(e instanceof Error ? e.message : String(e)),
  ), [cliente, entrevista]);

  useEffect(() => { void leer(); }, [leer]);

  async function enviar() {
    setFallo(null);
    setPensando(true);
    try {
      const { id_trabajo } = await cliente.responder(entrevista, respuesta);
      for (;;) {
        const t = await cliente.trabajo(id_trabajo);
        if (t.estado === "terminado") break;
        if (["fallido", "abandonado", "detenido_por_presupuesto"].includes(t.estado)) {
          throw new Error(t.motivo ?? `el turno termino en ${t.estado}`);
        }
        await new Promise((r) => setTimeout(r, intervaloMs));
      }
      setRespuesta("");
      setQuiereCambiar(false);
      await leer();
    } catch (e) {
      // RF-07: se ensena el motivo y la respuesta escrita no se pierde.
      setFallo(e instanceof Error ? e.message : String(e));
    } finally {
      setPensando(false);
    }
  }

  async function hecho(id: string, confirmar: boolean) {
    await (confirmar ? cliente.confirmarHecho : cliente.descartarHecho)(entrevista, id);
    await leer();
  }

  async function guardarNombres(n: NombresEntrada) {
    await cliente.declararNombres(entrevista, n);
    await leer();
  }

  async function confirmarAviso(vetado: string) {
    await cliente.confirmarAviso(entrevista, vetado);
    await leer();
  }

  async function cerrar() {
    setRechazo(null);
    try {
      await cliente.cerrarEntrevista(entrevista);
      await leer();
    } catch (e) {
      setRechazo(rechazoDe(e));
    }
  }

  if (errorDeCarga) return <main className="contenido"><p role="alert">{errorDeCarga}</p></main>;
  if (!historial) return <main className="contenido"><p aria-busy="true">cargando…</p></main>;

  // SPEC-34 RF-01: mientras no hay destinatario ni turnos, la primera respuesta es el nombre y
  // se escribe en su campo, fuera del modelo.
  const pideElNombre = !historial.cerrada && historial.nombres.destinatario === null
    && historial.turnos.length === 0;
  const completo = historial.puede_cerrar && !historial.cerrada && !quiereCambiar;

  return (
    <main className="contenido entrevista">
      <div className="entrevista__conversacion-y-cuaderno">
        <section className="entrevista__lado">
          <h1>La entrevista</h1>
          <ol className="entrevista__conversacion">
            <li className="turno">
              <div className="turno__burbuja turno__burbuja--entrevistador">
                <Entrevistadora />
                <p>{historial.primera_pregunta}</p>
              </div>
            </li>
            {historial.turnos.map((t) => <Turno key={t.orden} turno={t} />)}
          </ol>

          {historial.hechos_propuestos.length > 0 && (
            <section className="tarjeta entrevista__hechos">
              <h2>Lo que se sacó de tu texto</h2>
              <ul>
                {historial.hechos_propuestos.map((h) => (
                  <li key={h.id} data-testid={`hecho-${h.id}`}>
                    <span>{h.texto}</span> <span className="entrevista__estado">{h.estado}</span>
                    {h.estado === "propuesto" && !historial.cerrada && (
                      <>
                        <button type="button" className="boton boton--secundario"
                          onClick={() => void hecho(h.id, true)}>Confirmar</button>
                        <button type="button" className="boton boton--secundario"
                          onClick={() => void hecho(h.id, false)}>Descartar</button>
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {historial.cerrada ? (
            <section className="tarjeta entrevista__cerrada">
              <p>La ficha está cerrada.</p>
              {/* SPEC-33 RF-11: con la ficha cerrada se puede escribir la novela, tras confirmar
                  (RF-12). SPEC-35 RF-07: sin quitarle nada a la confirmacion. */}
              <ConfirmarGeneracion obra={historial.obra}
                alLanzar={() => navegar(`/obras/${encodeURIComponent(historial.obra)}/generacion`)} />
            </section>
          ) : pideElNombre ? (
            <CampoDelNombre alGuardar={(nombre) => guardarNombres({
              destinatario: nombre, regalado_por: null, otros: [], vetados: [] })} />
          ) : completo ? (
            <CuadernoCompleto cuaderno={historial.cuaderno} nombres={historial.nombres}
              alCambiar={() => setQuiereCambiar(true)} alCerrar={() => void cerrar()}
              alGuardarDedicatoria={(texto) => guardarNombres({
                destinatario: historial.nombres.destinatario,
                regalado_por: historial.nombres.regalado_por,
                otros: historial.nombres.otros.map((o) => ({ nombre: o.nombre,
                  tipo: o.tipo as "persona" | "mascota", relacion: o.relacion })),
                vetados: historial.nombres.vetados, dedicatoria: texto })}
              rechazo={rechazo && <Rechazado rechazo={rechazo} />} />
          ) : (
            <form className="entrevista__responder"
              onSubmit={(ev) => { ev.preventDefault(); void enviar(); }}>
              <label htmlFor="respuesta">Tu respuesta</label>
              <textarea id="respuesta" value={respuesta} rows={3}
                onChange={(ev) => setRespuesta(ev.target.value)} />
              <div className="entrevista__acciones">
                <button type="submit" className="boton boton--principal"
                  disabled={pensando || respuesta.trim() === ""}>Responder</button>
                {historial.puede_cerrar && (
                  <button type="button" className="boton boton--secundario"
                    disabled={pensando} onClick={() => setQuiereCambiar(false)}>
                    Volver al cuaderno completo
                  </button>
                )}
              </div>
              {pensando && <p role="status" className="entrevista__pensando">
                {ENTREVISTADORA.nombre} está pensando…</p>}
              {fallo && <p role="alert" className="aviso">El turno no salió: {fallo}</p>}
              {rechazo && <Rechazado rechazo={rechazo} />}
            </form>
          )}
        </section>

        <Cuaderno cuaderno={historial.cuaderno} nombres={historial.nombres}
          cerrada={historial.cerrada} alGuardarNombres={guardarNombres}
          alConfirmarAviso={confirmarAviso} />
      </div>
    </main>
  );
}

// SPEC-34 RF-01: el nombre del destinatario, en su campo. No llama a ningun agente.
function CampoDelNombre({ alGuardar }: { alGuardar: (nombre: string) => Promise<void> }) {
  const [nombre, setNombre] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  return (
    <form className="entrevista__responder" onSubmit={(ev) => {
      ev.preventDefault();
      setGuardando(true);
      setError(null);
      alGuardar(nombre.trim()).catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
        setGuardando(false);
      });
    }}>
      <label htmlFor="nombre-del-destinatario">
        Su nombre, tal como quieres que aparezca escrito
      </label>
      <input id="nombre-del-destinatario" value={nombre} autoComplete="off"
        onChange={(ev) => setNombre(ev.target.value)} />
      <p className="entrevista__nota">
        Los nombres se guardan tal cual y no los lee ningún modelo: el que escribe la novela
        trabaja con uno inventado y el libro sale con el de verdad.
      </p>
      <div className="entrevista__acciones">
        <button type="submit" className="boton boton--principal"
          disabled={guardando || nombre.trim() === ""}>Guardar el nombre</button>
      </div>
      {error && <p role="alert" className="aviso">No se guardó el nombre: {error}</p>}
    </form>
  );
}

type Rechazo = {
  motivo: string;
  faltan: string[];
  avisos: string[];
  contradicciones: { tipo: string; descripcion: string }[];
};

// El 409 de cerrar (SPEC-25) viaja en `detail`. Se ensena tal como viene; si no tiene esa
// forma, se dice el codigo en vez de inventar un motivo.
function rechazoDe(e: unknown): Rechazo {
  const d = e instanceof ErrorDeLaApi
    ? (e.detalle as { detail?: Partial<Rechazo> } | null)?.detail : undefined;
  if (d && typeof d === "object") {
    return { motivo: d.motivo ?? "no se pudo cerrar", faltan: d.faltan ?? [],
      avisos: d.avisos ?? [], contradicciones: d.contradicciones ?? [] };
  }
  return { motivo: e instanceof Error ? e.message : String(e), faltan: [], avisos: [],
    contradicciones: [] };
}

function Rechazado({ rechazo }: { rechazo: Rechazo }) {
  return (
    <div role="alert" className="aviso entrevista__rechazo">
      <p>{rechazo.motivo}</p>
      <ul>
        {rechazo.contradicciones.map((c) => (
          <li key={c.descripcion}>
            <EtiquetaDeEstado distintivo={SEVERIDAD.bloqueante} texto="contradicción" />
            {" "}{c.descripcion}
          </li>
        ))}
        {rechazo.avisos.map((a) => (
          <li key={a}><EtiquetaDeEstado distintivo={SEVERIDAD.mayor} texto="aviso" /> {a}</li>
        ))}
        {rechazo.faltan.map((f) => (
          <li key={f}><EtiquetaDeEstado distintivo={SEVERIDAD.menor} texto="falta" /> {f}</li>
        ))}
      </ul>
    </div>
  );
}
