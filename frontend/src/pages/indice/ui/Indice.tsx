import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import { EscenaConEstado } from "@/entities/escena";
import { Progreso } from "@/entities/progreso";
import { useLectura, type Indice, type IndiceDeVersion, type Versiones } from "@/shared/api";
import { ESTADO_DE_CAPITULO, Esperando, EtiquetaDeEstado, MARCA_DE_CAMBIO } from "@/shared/ui";

// El indice pinta **en el orden en que llega** (SPEC-22 RF-38): no ordena, no agrupa y no
// deduce a que capitulo va cada escena. «Capitulo N» es el `orden` que trae la respuesta.
// No hay partes: la API no las trae porque la base no las tiene.
//
// Con versiones (SPEC-23 D-2, PLAN-22 E17) se lee la de la ruta o, sin ella, la ultima de
// la lista que da el backend. Cada capitulo lleva la marca de «cambio» **tal como llega**
// (`compartido`, RF-52): aqui no se compara ningun texto. Una obra sin versiones se lee
// como siempre.
export function PaginaIndice() {
  const { obra = "", numero } = useParams();
  const versiones = useLectura((c) => c.versiones(obra), `versiones:${obra}`);
  if (versiones.estado === "error" && versiones.codigo === 404) {
    return <IndiceSinVersiones obra={obra} />;
  }
  return (
    <Esperando lectura={versiones}>
      {(v: Versiones) => {
        const vigente = v.versiones[v.versiones.length - 1].numero;
        return <IndiceConVersiones obra={obra} versiones={v} vigente={vigente}
          numero={numero === undefined ? vigente : Number(numero)} />;
      }}
    </Esperando>
  );
}

function IndiceSinVersiones({ obra }: { obra: string }) {
  const lectura = useLectura((c) => c.indice(obra), obra);
  return <Esperando lectura={lectura}>{(i: Indice) => <VistaIndice indice={i} />}</Esperando>;
}

function IndiceConVersiones({ obra, versiones, vigente, numero }: {
  obra: string; versiones: Versiones; vigente: number; numero: number;
}) {
  const lectura = useLectura((c) => c.indiceDeVersion(obra, numero), `${obra}:${numero}`);
  return (
    <Esperando lectura={lectura}>
      {(i: IndiceDeVersion) => (
        <VistaIndice indice={i} numero={numero} cabecera={
          <SelectorDeVersion obra={i.id} versiones={versiones} vigente={vigente} numero={numero} />
        } />
      )}
    </Esperando>
  );
}

function SelectorDeVersion({ obra, versiones, vigente, numero }: {
  obra: string; versiones: Versiones; vigente: number; numero: number;
}) {
  const o = encodeURIComponent(obra);
  return (
    <>
      <nav className="versiones" aria-label="Versiones de la obra">
        <span className="versiones__rotulo">Versiones</span>
        {[...versiones.versiones].reverse().map((v) => {
          const texto = `Versión ${v.numero}${v.numero === vigente ? " (vigente)" : ""}`;
          return v.numero === numero
            ? <span key={v.numero} className="version version--actual"
                data-testid="version-actual" aria-current="page">{texto}</span>
            : <Link key={v.numero} className="version"
                to={`/obras/${o}/versiones/${v.numero}/indice`}>{texto}</Link>;
        })}
      </nav>
      {numero !== vigente && (
        <p className="aviso aviso-de-version" role="status">
          Estás leyendo la versión {numero}, que se conserva entera. La vigente es la{" "}
          <Link to={`/obras/${o}/versiones/${vigente}/indice`}>versión {vigente}</Link>.
        </p>
      )}
    </>
  );
}

type Verificacion = "verificada" | "sin_reverificar" | "fallida";
type EscenaPintable = Indice["capitulos"][number]["escenas"][number] & {
  estado_de_verificacion?: Verificacion;
};
type CapituloPintable = Omit<Indice["capitulos"][number], "escenas"> & {
  compartido?: boolean | null;
  escenas: EscenaPintable[];
};

// `data-cambio`: "true" si el backend dice que cambio, "false" si es el mismo, y
// "sin-anterior" si la version no tiene con que compararse. Fuera de una version, nada.
function marcaDe(c: CapituloPintable): "true" | "false" | "sin-anterior" | undefined {
  if (!("compartido" in c)) return undefined;
  if (c.compartido === null || c.compartido === undefined) return "sin-anterior";
  return c.compartido ? "false" : "true";
}

function VistaIndice({ indice, numero, cabecera }: {
  indice: Indice | IndiceDeVersion; numero?: number; cabecera?: ReactNode;
}) {
  const obra = encodeURIComponent(indice.id);
  const base = numero === undefined ? `/obras/${obra}` : `/obras/${obra}/versiones/${numero}`;
  const capitulos = indice.capitulos as CapituloPintable[];
  return (
    <main className="contenido indice">
      <p className="migas"><Link to={`/obras/${obra}`}>{indice.titulo}</Link></p>
      <h1>Índice</h1>
      {cabecera}
      <Progreso obra={indice.id} />
      <ol className="capitulos">
        {capitulos.map((c) => {
          const cambio = marcaDe(c);
          const clase = cambio === "true" ? " capitulo-del-indice--cambiado" : "";
          return (
            <li key={c.id} data-testid="capitulo-del-indice" data-capitulo={c.id}
              data-estado={c.estado} data-cambio={cambio}
              className={`tarjeta capitulo-del-indice${clase}`}>
              <div className="capitulo-del-indice__cabecera">
                <h2><Link to={`${base}/capitulos/${encodeURIComponent(c.id)}`}>
                  {`Capítulo ${c.orden}`}
                </Link></h2>
                <span className="capitulo-del-indice__etiquetas">
                  {cambio === "true" && <EtiquetaDeEstado distintivo={MARCA_DE_CAMBIO.cambio} />}
                  {cambio === "false" && <EtiquetaDeEstado distintivo={MARCA_DE_CAMBIO.compartido} />}
                  <EtiquetaDeEstado distintivo={ESTADO_DE_CAPITULO[c.estado]} />
                </span>
              </div>
              <ol className="escenas">
                {c.escenas.map((e) => (
                  <li key={e.id} data-testid="escena-del-indice" data-escena={e.id}
                    className="escena-del-indice">
                    <Link to={`/obras/${obra}/escenas/${encodeURIComponent(e.id)}`}>{e.id}</Link>
                    <EscenaConEstado escena={e} conTexto={false}
                      verificacion={e.estado_de_verificacion} />
                  </li>
                ))}
              </ol>
            </li>
          );
        })}
      </ol>
      <p><Link className="boton boton--secundario" to={`/obras/${obra}/fichas`}>Fichas</Link></p>
    </main>
  );
}
