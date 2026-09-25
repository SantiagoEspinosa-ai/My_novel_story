import { useState } from "react";
import type { Cuaderno as CuadernoDelBackend, Nombres, NombresEntrada } from "@/shared/api";
import { ENTREVISTADORA } from "@/shared/config";
import "./cuaderno.css";

// SPEC-35 RF-05: el cuaderno, al lado de la conversacion. Lo que la ficha sabe, lo que falta y
// cuanto, tal como lo da el backend: aqui no se cuenta ni se traduce nada.
export function Cuaderno({ cuaderno, nombres, cerrada, alGuardarNombres, alConfirmarAviso }: {
  cuaderno: CuadernoDelBackend;
  nombres: Nombres;
  cerrada: boolean;
  alGuardarNombres: (n: NombresEntrada) => Promise<void>;
  alConfirmarAviso: (vetado: string) => Promise<void>;
}) {
  return (
    <aside className="cuaderno" data-testid="cuaderno" aria-label="El cuaderno">
      <h2 className="cuaderno__titulo">El cuaderno de {ENTREVISTADORA.nombre}</h2>
      <p className="cuaderno__cuenta">
        {cuaderno.faltan === 0
          ? "Ya está todo lo necesario"
          : `Faltan ${cuaderno.faltan} de ${cuaderno.total}`}
      </p>
      <Sabido cuaderno={cuaderno} />
      {cuaderno.falta.length > 0 && (
        <section className="cuaderno__seccion">
          <h3>Todavía falta</h3>
          <ul className="cuaderno__falta" data-testid="cuaderno-falta">
            {cuaderno.falta.map((f) => <li key={f}>{f}</li>)}
          </ul>
        </section>
      )}
      <NombresDelCuaderno nombres={nombres} cerrada={cerrada}
        alGuardar={alGuardarNombres} alConfirmarAviso={alConfirmarAviso} />
    </aside>
  );
}

export function Sabido({ cuaderno }: { cuaderno: CuadernoDelBackend }) {
  if (cuaderno.sabido.length === 0) {
    return <p className="cuaderno__vacio">Todavía no hay nada apuntado.</p>;
  }
  return (
    <dl className="cuaderno__sabido">
      {cuaderno.sabido.map((s) => (
        <div key={s.campo} className="cuaderno__campo">
          <dt>{s.etiqueta}</dt>
          {s.valores.map((v) => <dd key={v}>{v}</dd>)}
        </div>
      ))}
    </dl>
  );
}

// SPEC-35 RF-06, SPEC-34 RF-01: los nombres se escriben aqui y no pasan por ningun agente.
// Siempre el nombre real. Guardar manda el estado completo, que es lo que pide el backend.
function NombresDelCuaderno({ nombres, cerrada, alGuardar, alConfirmarAviso }: {
  nombres: Nombres;
  cerrada: boolean;
  alGuardar: (n: NombresEntrada) => Promise<void>;
  alConfirmarAviso: (vetado: string) => Promise<void>;
}) {
  const [nombre, setNombre] = useState("");
  const [tipo, setTipo] = useState<"persona" | "mascota">("persona");
  const [relacion, setRelacion] = useState("");
  const [vetado, setVetado] = useState("");
  const [regala, setRegala] = useState("");
  const [error, setError] = useState<string | null>(null);

  // El estado completo, con todos los campos: es lo que manda cada guardado.
  const actual = (): Required<NombresEntrada> => ({
    destinatario: nombres.destinatario,
    regalado_por: nombres.regalado_por,
    otros: nombres.otros.map((o) => ({ nombre: o.nombre, tipo: o.tipo as "persona" | "mascota",
      relacion: o.relacion })),
    vetados: [...nombres.vetados],
  });

  async function guardar(n: NombresEntrada, limpiar: () => void) {
    setError(null);
    try {
      await alGuardar(n);
      limpiar();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <section className="cuaderno__seccion cuaderno__nombres" data-testid="cuaderno-nombres">
      <h3>Los nombres</h3>
      <p className="cuaderno__nota">
        Se escriben aquí y se guardan tal cual: no los lee ningún modelo.
      </p>
      <dl className="cuaderno__sabido">
        <div className="cuaderno__campo">
          <dt>Para</dt>
          <dd>{nombres.destinatario ?? <span className="sin-dato">todavía sin nombre</span>}</dd>
        </div>
        {nombres.regalado_por && (
          <div className="cuaderno__campo"><dt>De parte de</dt><dd>{nombres.regalado_por}</dd></div>
        )}
      </dl>
      {nombres.otros.length > 0 && (
        <ul className="cuaderno__lista">
          {nombres.otros.map((o) => (
            <li key={o.nombre}>
              <strong>{o.nombre}</strong> · {o.tipo === "mascota" ? "mascota" : "persona"}
              {o.relacion && <> · {o.relacion}</>}
              {!cerrada && o.declarado && (
                <button type="button" className="cuaderno__quitar"
                  aria-label={`Quitar a ${o.nombre}`}
                  onClick={() => void guardar({ ...actual(),
                    otros: actual().otros.filter((x) => x.nombre !== o.nombre) }, () => {})}>
                  quitar
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
      {nombres.vetados.length > 0 && (
        <p className="cuaderno__vetados">
          No aparecerán: {nombres.vetados.join(", ")}
        </p>
      )}
      {nombres.avisos.map((a) => (
        <div key={a.vetado} role="note" className="aviso cuaderno__aviso">
          <p>{a.texto}</p>
          {!cerrada && (
            <button type="button" className="boton boton--secundario"
              onClick={() => void alConfirmarAviso(a.vetado)}>Entendido</button>
          )}
        </div>
      ))}
      {!cerrada && nombres.destinatario && (
        <>
          <form className="cuaderno__formulario" onSubmit={(ev) => {
            ev.preventDefault();
            if (!nombre.trim()) return;
            void guardar({ ...actual(), otros: [...actual().otros,
              { nombre: nombre.trim(), tipo, relacion: relacion.trim() || null }] },
            () => { setNombre(""); setRelacion(""); });
          }}>
            <p className="cuaderno__subtitulo">Otra persona o mascota con nombre</p>
            <label>Nombre<input value={nombre} onChange={(e) => setNombre(e.target.value)} /></label>
            <label htmlFor="cuaderno-tipo">Es</label>
            <select id="cuaderno-tipo" value={tipo}
              onChange={(e) => setTipo(e.target.value as "persona" | "mascota")}>
              <option value="persona">persona</option>
              <option value="mascota">mascota</option>
            </select>
            <label>Relación
              <input value={relacion} placeholder="su hermana, su perro…"
                onChange={(e) => setRelacion(e.target.value)} />
            </label>
            <button type="submit" className="boton boton--secundario">Añadir</button>
          </form>
          {!nombres.regalado_por && (
            <form className="cuaderno__formulario" onSubmit={(ev) => {
              ev.preventDefault();
              if (!regala.trim()) return;
              void guardar({ ...actual(), regalado_por: regala.trim() }, () => setRegala(""));
            }}>
              <label>Quién la regala
                <input value={regala} onChange={(e) => setRegala(e.target.value)} />
              </label>
              <button type="submit" className="boton boton--secundario">Guardar</button>
            </form>
          )}
          <form className="cuaderno__formulario" onSubmit={(ev) => {
            ev.preventDefault();
            if (!vetado.trim()) return;
            void guardar({ ...actual(), vetados: [...actual().vetados, vetado.trim()] },
              () => setVetado(""));
          }}>
            <label>Nombre que no debe aparecer
              <input value={vetado} onChange={(e) => setVetado(e.target.value)} />
            </label>
            <button type="submit" className="boton boton--secundario">Vetar</button>
          </form>
        </>
      )}
      {error && <p role="alert" className="aviso">No se guardaron los nombres: {error}</p>}
    </section>
  );
}
