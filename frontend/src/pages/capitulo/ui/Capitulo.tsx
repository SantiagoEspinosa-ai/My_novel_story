import { Link, useParams } from "react-router-dom";
import { TextoDeEscena, tituloDeCapitulo } from "@/entities/escena";
import { ConPeticion } from "@/features/pedir-cambio";
import {
  useLectura, type CapituloLeido, type CapituloLeidoDeVersion, type Indice, type Versiones,
} from "@/shared/api";
import { Esperando, EtiquetaDeEstado, MARCA_DE_CAMBIO } from "@/shared/ui";
import "./capitulo.css";

// La lectura continua de un capitulo (SPEC-22 RF-41). Que escenas entran y en que orden lo
// decide el backend; aqui se pinta **una escena por bloque**. No se juntan textos: juntarlos
// borraria de que escena es cada frase.
//
// SPEC-43: la lectura es para el lector. Ni el estado de la escena ni sus hallazgos ni su
// estado de verificacion: todo eso vive en la administracion (la pestana «Escenas» de cada
// novela). Se queda la marca de cambio de una version (RF-52, SPEC-35 RF-10), que es del
// lector. Una version que no es la vigente se lee entera (RF-53) pero no ofrece pedir
// cambios: se pide sobre la vigente, que es de la que parte la peticion.
export function PaginaCapitulo() {
  const { obra = "", capitulo = "", numero } = useParams();
  if (numero !== undefined) {
    return <CapituloDeVersion obra={obra} capitulo={capitulo} numero={Number(numero)} />;
  }
  return <CapituloVigente obra={obra} capitulo={capitulo} />;
}

function CapituloVigente({ obra, capitulo }: { obra: string; capitulo: string }) {
  const lectura = useLectura((c) => c.capitulo(capitulo), capitulo);
  return (
    <Esperando lectura={lectura}>
      {(cap: CapituloLeido) => <VistaCapitulo obra={obra} capitulo={cap} pedir />}
    </Esperando>
  );
}

function CapituloDeVersion({ obra, capitulo, numero }: {
  obra: string; capitulo: string; numero: number;
}) {
  const versiones = useLectura((c) => c.versiones(obra), `versiones:${obra}`);
  const lectura = useLectura((c) => c.capituloDeVersion(obra, numero, capitulo),
    `${obra}:${numero}:${capitulo}`);
  return (
    <Esperando lectura={versiones}>
      {(v: Versiones) => {
        const vigente = v.vigente; // la dice el backend (F-150): la ultima creada no es la vigente
        return (
          <Esperando lectura={lectura}>
            {(cap: CapituloLeidoDeVersion) => (
              <VistaCapitulo obra={obra} capitulo={cap} numero={numero} vigente={vigente}
                pedir={numero === vigente}
                anterior={v.versiones.find((x) => x.numero === numero)?.anterior ?? null} />
            )}
          </Esperando>
        );
      }}
    </Esperando>
  );
}

function VistaCapitulo({ obra, capitulo, numero, vigente, anterior = null, pedir = false }: {
  obra: string;
  capitulo: CapituloLeido | CapituloLeidoDeVersion;
  numero?: number;
  vigente?: number;
  anterior?: number | null;
  pedir?: boolean;
}) {
  const o = encodeURIComponent(obra);
  const deVersion = "numero" in capitulo ? capitulo : null;
  const indice = numero === undefined
    ? `/obras/${o}/indice` : `/obras/${o}/versiones/${numero}/indice`;
  return (
    <main className="contenido capitulo" data-capitulo={capitulo.id}>
      <nav className="migas">
        <Link to={indice}>Índice{numero !== undefined ? ` · versión ${numero}` : ""}</Link>
      </nav>
      {numero !== undefined && vigente !== undefined && numero !== vigente && (
        <p className="aviso aviso-de-version" role="status">
          Estás leyendo la versión {numero}, que se conserva entera. Los cambios se piden sobre
          la <Link to={`/obras/${o}/versiones/${vigente}/indice`}>versión {vigente}</Link>.
        </p>
      )}
      {deVersion?.compartido === false && numero !== undefined && (
        <PorTuCambio obra={obra} numero={numero} anterior={anterior} />
      )}
      <h1>{tituloDeCapitulo(capitulo)}</h1>
      <div className="capitulo__etiquetas">
        {deVersion?.compartido === false &&
          <EtiquetaDeEstado distintivo={MARCA_DE_CAMBIO.cambio} />}
        {deVersion?.compartido === true &&
          <EtiquetaDeEstado distintivo={MARCA_DE_CAMBIO.compartido} />}
      </div>
      {capitulo.escenas.map((e) => {
        const escena = <TextoDeEscena escena={e} />;
        return (
          <section key={e.id} data-testid="bloque-de-escena" data-escena={e.id}
            className="tarjeta bloque-de-escena">
            {pedir ? <ConPeticion obra={obra} escena={e}>{escena}</ConPeticion> : escena}
          </section>
        );
      })}
      <NavegacionEntreCapitulos obra={obra} capitulo={capitulo.id} numero={numero} />
    </main>
  );
}

// SPEC-43 RF-03: al final, anterior, siguiente y el indice, en el orden de lectura de la
// version que se lee. El orden lo da el indice del backend; aqui no se ordena. Mientras el
// indice no llega no se pinta (arriba queda el enlace al indice); si no llega, solo la vuelta.
function NavegacionEntreCapitulos({ obra, capitulo, numero }: {
  obra: string; capitulo: string; numero?: number;
}) {
  const lectura = useLectura(
    (c) => (numero === undefined ? c.indice(obra) : c.indiceDeVersion(obra, numero)),
    numero === undefined ? `indice:${obra}` : `indice:${obra}:${numero}`);
  const o = encodeURIComponent(obra);
  const base = numero === undefined ? `/obras/${o}` : `/obras/${o}/versiones/${numero}`;
  if (lectura.estado === "cargando") return null;
  const capitulos = lectura.estado === "listo" ? (lectura.datos as Indice).capitulos : [];
  const i = capitulos.findIndex((c) => c.id === capitulo);
  const anterior = i > 0 ? capitulos[i - 1] : null;
  const siguiente = i >= 0 && i < capitulos.length - 1 ? capitulos[i + 1] : null;
  const a = (id: string) => `${base}/capitulos/${encodeURIComponent(id)}`;
  return (
    <nav className="entre-capitulos" aria-label="entre capítulos">
      {anterior ? <Link className="entre-capitulos__anterior" to={a(anterior.id)}>
        ← Anterior: {tituloDeCapitulo(anterior)}</Link> : <span />}
      <Link className="entre-capitulos__indice" to={`${base}/indice`}>Volver al índice</Link>
      {siguiente ? <Link className="entre-capitulos__siguiente" to={a(siguiente.id)}>
        Siguiente: {tituloDeCapitulo(siguiente)} →</Link> : <span />}
    </nav>
  );
}

// SPEC-35 RF-10: un capitulo que cambio en una version dice que peticion lo cambio, con las
// palabras del lector, y enlaza a la version anterior. Sin peticion (una version que no nacio
// de un cambio), o mientras no llega, no hay aviso: no se inventa un porque.
function PorTuCambio({ obra, numero, anterior }: {
  obra: string; numero: number; anterior: number | null;
}) {
  const lectura = useLectura((c) => c.peticionDeLaVersion(obra, numero), `peticion:${obra}:${numero}`);
  if (lectura.estado !== "listo" || lectura.datos.texto === null) return null;
  const o = encodeURIComponent(obra);
  return (
    <p className="por-tu-cambio" data-testid="por-tu-cambio" role="note">
      <span>Este capítulo se reescribió por tu cambio: «{lectura.datos.texto}»</span>
      {anterior !== null && (
        <Link to={`/obras/${o}/versiones/${anterior}/indice`}>Leer cómo era antes</Link>
      )}
    </p>
  );
}
