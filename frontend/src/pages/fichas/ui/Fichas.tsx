import { Link, useParams } from "react-router-dom";
import { useLectura, type Esquemas, type Fichas } from "@/shared/api";
import { Esperando, SinDato } from "@/shared/ui";

// Las fichas de personajes y lugares (SPEC-22 RF-43, RF-44). Los capitulos donde aparece
// cada entidad los calcula el backend; aqui se enlazan **los que llegan, ni uno mas**. Lo que
// no consta se dice: un nombre nulo pinta el id y lo avisa, un dato nulo es «sin dato» y
// unos presentes sin declarar son «no declarado», que no es «ninguno».
type Enlazado = Esquemas["CapituloEnlazado"];

export function PaginaFichas() {
  const { obra = "" } = useParams();
  const lectura = useLectura((c) => c.fichas(obra), obra);
  return <Esperando lectura={lectura}>{(f: Fichas) => <VistaFichas obra={obra} fichas={f} />}</Esperando>;
}

function Capitulos({ obra, capitulos, ausente }: {
  obra: string; capitulos: Enlazado[] | null; ausente: string;
}) {
  return (
    <span data-testid="capitulos">
      <SinDato valor={capitulos} ausente={ausente}>
        {(lista: Enlazado[]) => lista.map((c, i) => (
          <span key={c.id}>
            {i > 0 && ", "}
            <Link to={`/obras/${encodeURIComponent(obra)}/capitulos/${encodeURIComponent(c.id)}`}>
              {`Capítulo ${c.orden}`}
            </Link>
          </span>
        ))}
      </SinDato>
    </span>
  );
}

function Nombre({ id, nombre }: { id: string; nombre: string | null }) {
  return (
    <h3 data-testid="nombre">
      {nombre ?? <>{id} <small className="sin-dato">(sin nombre guardado)</small></>}
    </h3>
  );
}

function VistaFichas({ obra, fichas }: { obra: string; fichas: Fichas }) {
  return (
    <main className="contenido fichas">
      <nav className="migas"><Link to={`/obras/${encodeURIComponent(obra)}/indice`}>Índice</Link></nav>
      <h1>Fichas</h1>
      <h2>Personajes</h2>
      <div className="fichas__rejilla">
      {fichas.personajes.map((p) => (
        <article key={p.id} data-testid="ficha" data-ficha={p.id} className="tarjeta ficha">
          <Nombre id={p.id} nombre={p.nombre_canonico} />
          <dl>
            <dt>Alias</dt>
            <dd data-testid="alias"><SinDato valor={p.alias}>{(a: string[]) => a.join(", ")}</SinDato></dd>
            <dt>Rol</dt>
            <dd data-testid="rol_dramatico"><SinDato valor={p.rol_dramatico}>{(r: string) => r}</SinDato></dd>
            <dt>Estado vital</dt>
            <dd data-testid="estado_vital"><SinDato valor={p.estado_vital}>{(e: string) => e}</SinDato></dd>
            <dt>Aparece en</dt>
            <dd><Capitulos obra={obra} capitulos={p.capitulos_donde_aparece} ausente="no declarado" /></dd>
          </dl>
        </article>
      ))}
      </div>
      <h2>Lugares</h2>
      <div className="fichas__rejilla">
      {fichas.lugares.map((l) => (
        <article key={l.id} data-testid="ficha" data-ficha={l.id} className="tarjeta ficha">
          <Nombre id={l.id} nombre={l.nombre} />
          <dl>
            <dt>Atmósfera</dt>
            <dd data-testid="atmosfera"><SinDato valor={l.atmosfera}>{(a: string) => a}</SinDato></dd>
            <dt>Aparece en</dt>
            <dd><Capitulos obra={obra} capitulos={l.capitulos_donde_aparece} ausente="sin dato" /></dd>
          </dl>
        </article>
      ))}
      </div>
    </main>
  );
}
