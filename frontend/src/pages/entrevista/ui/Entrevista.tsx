import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Turno } from "./Turno";
import { ErrorDeLaApi, useCliente, type Historial } from "@/shared/api";
import { INTERVALO_DE_REGALO_MS } from "@/shared/config";
import { EtiquetaDeEstado, SEVERIDAD } from "@/shared/ui";
import "./entrevista.css";

// La entrevista como conversacion (SPEC-33 RF-05..RF-10). Una pregunta cada vez y las
// anteriores encima. La conversacion es el historial del backend, asi que sobrevive a
// recargar; la pagina no calcula nada: si se puede cerrar lo dice `puede_cerrar`.
export function PaginaEntrevista({ intervaloMs = INTERVALO_DE_REGALO_MS, alCerrar }: {
  intervaloMs?: number;
  /** Lo que se ensena al cerrar la ficha: aqui entra lanzar la generacion (RF-11). */
  alCerrar?: (h: Historial) => React.ReactNode;
}) {
  const { entrevista = "" } = useParams();
  const cliente = useCliente();
  const [historial, setHistorial] = useState<Historial | null>(null);
  const [errorDeCarga, setErrorDeCarga] = useState<string | null>(null);
  const [respuesta, setRespuesta] = useState("");
  const [pensando, setPensando] = useState(false);
  const [fallo, setFallo] = useState<string | null>(null);
  const [rechazo, setRechazo] = useState<Rechazo | null>(null);

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

  return (
    <main className="contenido entrevista">
      <h1>La entrevista</h1>
      <ol className="entrevista__conversacion">
        <li className="turno">
          <p className="turno__burbuja turno__burbuja--entrevistador">
            {historial.primera_pregunta}
          </p>
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
          {alCerrar?.(historial)}
        </section>
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
                disabled={pensando} onClick={() => void cerrar()}>Cerrar la ficha</button>
            )}
          </div>
          {pensando && <p role="status" className="entrevista__pensando">
            El entrevistador está pensando…</p>}
          {fallo && <p role="alert" className="aviso">El turno no salió: {fallo}</p>}
          {rechazo && <Rechazado rechazo={rechazo} />}
        </form>
      )}
    </main>
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
