import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { PaginaCapitulo } from "@/pages/capitulo";
import { PaginaEscena } from "@/pages/escena";
import { PaginaFichas } from "@/pages/fichas";
import { PaginaIndice } from "@/pages/indice";
import { PaginaPortada } from "@/pages/portada";
import { ClienteProvider, type Cliente } from "@/shared/api";

// Las rutas de la lectura web. Cada pagina lee su respuesta y la pinta tal cual llega.
export function App({ cliente }: { cliente: Cliente }) {
  return (
    <ClienteProvider cliente={cliente}>
      <BrowserRouter>
        <Routes>
          <Route path="/obras/:obra" element={<PaginaPortada />} />
          <Route path="/obras/:obra/indice" element={<PaginaIndice />} />
          <Route path="/obras/:obra/capitulos/:capitulo" element={<PaginaCapitulo />} />
          <Route path="/obras/:obra/escenas/:escena" element={<PaginaEscena />} />
          <Route path="/obras/:obra/fichas" element={<PaginaFichas />} />
          <Route path="*" element={<Inicio />} />
        </Routes>
      </BrowserRouter>
    </ClienteProvider>
  );
}

function Inicio() {
  return (
    <main>
      <h1>Lectura</h1>
      <p>Abre una obra por su identificador: <code>/obras/&lt;id&gt;</code>.</p>
      <p><Link to="/">Inicio</Link></p>
    </main>
  );
}
