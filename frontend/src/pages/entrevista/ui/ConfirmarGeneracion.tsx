import { useEffect, useState } from "react";
import { ErrorDeLaApi, useCliente, type ConfirmacionDeGasto } from "@/shared/api";
import "./confirmar.css";

// Lanzar gasta el precio de una novela (SPEC-33 RF-12). Antes, tres cifras con su
// procedencia: la ultima generacion medida en esta base, la referencia de la novela de
// ejemplo y lo gastado frente al techo. El boton que gasta no existe hasta que las cifras
// han cargado, ni cuando el techo esta alcanzado; el backend lo impone igual (RF-13).
export function ConfirmarGeneracion({ obra, alLanzar }: {
  obra: string;
  alLanzar: (generacion: string) => void;
}) {
  const cliente = useCliente();
  const [c, setC] = useState<ConfirmacionDeGasto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lanzando, setLanzando] = useState(false);

  useEffect(() => {
    let vivo = true;
    cliente.gasto().then((d) => { if (vivo) setC(d); },
      (e: unknown) => { if (vivo) setError(e instanceof Error ? e.message : String(e)); });
    return () => { vivo = false; };
  }, [cliente]);

  async function lanzar() {
    setError(null);
    setLanzando(true);
    try {
      const { generacion } = await cliente.lanzar(obra);
      alLanzar(generacion);
    } catch (e) {
      const d = e instanceof ErrorDeLaApi ? (e.detalle as { detail?: unknown } | null)?.detail : null;
      setError(typeof d === "string" ? d : e instanceof Error ? e.message : String(e));
      setLanzando(false);
    }
  }

  return (
    <section className="tarjeta confirmar" aria-label="Confirmar la generación">
      <h2>Escribir la novela</h2>
      <p className="confirmar__aviso">
        Escribir los diez capítulos llama a los modelos muchas veces y <strong>gasta dinero</strong>.
      </p>
      {!c && !error && <p aria-busy="true">cargando lo gastado…</p>}
      {c && (
        <dl className="confirmar__cifras">
          <div data-testid="ultima">
            <dt>La última generación en esta base</dt>
            <dd>{c.ultima === null || c.ultima.usd === null
              ? <span className="sin-dato">sin medir</span>
              : <>{usd(c.ultima.usd)}{c.ultima.es_suelo && <Suelo />}</>}</dd>
          </div>
          <div data-testid="referencia">
            <dt>Referencia: la novela de ejemplo</dt>
            <dd>{usd(c.referencia.usd)} en {c.referencia.delegaciones} delegaciones
              <span className="confirmar__fuente">fuente: {c.referencia.fuente}</span></dd>
          </div>
          <div data-testid="gastado">
            <dt>Gastado en esta base</dt>
            <dd>{c.gastado.usd === null
              ? <span className="sin-dato">sin medir</span> : usd(c.gastado.usd)}
              {" "}de {usd(c.techo_usd, 0)}{c.gastado.es_suelo && c.gastado.usd !== null && <Suelo />}
              <span className="confirmar__fuente">{c.gastado.por_que_es_suelo}</span></dd>
          </div>
        </dl>
      )}
      {c?.alcanzado && (
        <p role="alert" className="aviso">
          Lo gastado ya alcanza el techo de {usd(c.techo_usd, 0)}: no se puede lanzar otra.
        </p>
      )}
      {error && <p role="alert" className="aviso">{error}</p>}
      <button type="button" className="boton boton--principal"
        disabled={!c || c.alcanzado || lanzando} onClick={() => void lanzar()}>
        Sí, escribir la novela (gasta dinero)
      </button>
    </section>
  );
}

function Suelo() {
  return <span className="confirmar__suelo"> (como mínimo)</span>;
}

function usd(n: number, decimales = 2) {
  return `${n.toFixed(decimales).replace(".", ",")} USD`;
}
