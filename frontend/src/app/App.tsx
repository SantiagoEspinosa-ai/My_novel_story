import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { PaginaAdministracion } from "@/pages/administracion";
import { PaginaCapitulo } from "@/pages/capitulo";
import { PaginaEntrevista } from "@/pages/entrevista";
import { PaginaEscena } from "@/pages/escena";
import { PaginaEstanteria } from "@/pages/estanteria";
import { PaginaFichas } from "@/pages/fichas";
import { PaginaHistoriaDeObra } from "@/pages/historia-de-obra";
import { PaginaGeneracion } from "@/pages/generacion";
import { PaginaIndice } from "@/pages/indice";
import { PaginaPortada } from "@/pages/portada";
import { ClienteProvider, type Cliente } from "@/shared/api";
import { Cabecera, Tema } from "@/shared/ui";

// Las rutas de la web: la novela regalo (SPEC-33) y su lectura (SPEC-22). Cada pagina lee su
// respuesta y la pinta tal cual llega.
export function App({ cliente }: { cliente: Cliente }) {
  return (
    <ClienteProvider cliente={cliente}>
      <Tema />
      <BrowserRouter>
        <Cabecera>
          <Link to="/">Estantería</Link>
          <Link to="/admin">Administración</Link>
        </Cabecera>
        <Routes>
          <Route path="/" element={<PaginaEstanteria />} />
          <Route path="/entrevistas/:entrevista" element={<PaginaEntrevista />} />
          <Route path="/admin" element={<PaginaAdministracion />} />
          <Route path="/admin/obras/:obra" element={<PaginaHistoriaDeObra />} />
          <Route path="/obras/:obra/generacion" element={<PaginaGeneracion />} />
          <Route path="/obras/:obra" element={<PaginaPortada />} />
          <Route path="/obras/:obra/indice" element={<PaginaIndice />} />
          <Route path="/obras/:obra/capitulos/:capitulo" element={<PaginaCapitulo />} />
          <Route path="/obras/:obra/versiones/:numero/indice" element={<PaginaIndice />} />
          <Route path="/obras/:obra/versiones/:numero/capitulos/:capitulo"
            element={<PaginaCapitulo />} />
          <Route path="/obras/:obra/escenas/:escena" element={<PaginaEscena />} />
          <Route path="/obras/:obra/fichas" element={<PaginaFichas />} />
          <Route path="*" element={<NoExiste />} />
        </Routes>
      </BrowserRouter>
    </ClienteProvider>
  );
}

function NoExiste() {
  return (
    <main className="contenido">
      <h1>No existe</h1>
      <p><Link to="/">Volver a la estantería</Link></p>
    </main>
  );
}
