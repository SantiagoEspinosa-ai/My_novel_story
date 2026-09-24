import { Link, useParams } from "react-router-dom";
import { EscenaConEstado } from "@/entities/escena";
import { ConPeticion } from "@/features/pedir-cambio";
import {
  useLectura, type CapituloLeido, type CapituloLeidoDeVersion, type Versiones,
} from "@/shared/api";
import { ESTADO_DE_CAPITULO, Esperando, EtiquetaDeEstado, MARCA_DE_CAMBIO } from "@/shared/ui";

// La lectura continua de un capitulo (SPEC-22 RF-41). Que escenas entran y en que orden lo
// decide el backend; aqui se pinta **una escena por bloque**, cada una con su estado y sus
// hallazgos (RF-39). No se juntan textos: juntarlos borraria de que escena es cada frase.
//
// Dentro de una version (PLAN-22 E17) cada escena lleva ademas su estado de verificacion
// en esa version (RF-54) y el capitulo su marca de cambio (RF-52), tal como llegan. Una
// version que no es la vigente se lee entera (RF-53) pero no ofrece pedir cambios: se pide
// sobre la vigente, que es de la que parte la peticion.
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
        const vigente = v.versiones[v.versiones.length - 1].numero;
        return (
          <Esperando lectura={lectura}>
            {(cap: CapituloLeidoDeVersion) => (
              <VistaCapitulo obra={obra} capitulo={cap} numero={numero} vigente={vigente}
                pedir={numero === vigente} />
            )}
          </Esperando>
        );
      }}
    </Esperando>
  );
}

function VistaCapitulo({ obra, capitulo, numero, vigente, pedir = false }: {
  obra: string;
  capitulo: CapituloLeido | CapituloLeidoDeVersion;
  numero?: number;
  vigente?: number;
  pedir?: boolean;
}) {
  const o = encodeURIComponent(obra);
  const deVersion = "numero" in capitulo ? capitulo : null;
  const indice = numero === undefined
    ? `/obras/${o}/indice` : `/obras/${o}/versiones/${numero}/indice`;
  return (
    <main className="contenido capitulo" data-capitulo={capitulo.id} data-estado={capitulo.estado}>
      <nav className="migas">
        <Link to={indice}>Índice{numero !== undefined ? ` · versión ${numero}` : ""}</Link>
      </nav>
      {numero !== undefined && vigente !== undefined && numero !== vigente && (
        <p className="aviso aviso-de-version" role="status">
          Estás leyendo la versión {numero}, que se conserva entera. Los cambios se piden sobre
          la <Link to={`/obras/${o}/versiones/${vigente}/indice`}>versión {vigente}</Link>.
        </p>
      )}
      <h1>{`Capítulo ${capitulo.orden}`}</h1>
      <div className="capitulo__etiquetas">
        {deVersion?.compartido === false &&
          <EtiquetaDeEstado distintivo={MARCA_DE_CAMBIO.cambio} />}
        {deVersion?.compartido === true &&
          <EtiquetaDeEstado distintivo={MARCA_DE_CAMBIO.compartido} />}
        <EtiquetaDeEstado distintivo={ESTADO_DE_CAPITULO[capitulo.estado]} />
      </div>
      {capitulo.escenas.map((e) => {
        const verificacion = "estado_de_verificacion" in e ? e.estado_de_verificacion : undefined;
        const escena = <EscenaConEstado escena={e} verificacion={verificacion} />;
        return (
          <section key={e.id} data-testid="bloque-de-escena" data-escena={e.id}
            className="tarjeta bloque-de-escena">
            {pedir ? <ConPeticion obra={obra} escena={e}>{escena}</ConPeticion> : escena}
          </section>
        );
      })}
    </main>
  );
}
