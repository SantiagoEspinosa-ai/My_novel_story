// PLAN-33 E14 (SPEC-33 RF-01, RF-04): la novela regalo entra en la web. La raiz es la
// estanteria, y la entrevista y la generacion tienen sus rutas. Compone paginas, asi que vive
// en app/ (FSD: una pagina no importa otra).
import { render, screen } from "@testing-library/react";
import { crearCliente } from "@/shared/api";
import {
  administracion, estanteria, fetchConMetodo, generacionEnCurso, historialAbierto,
} from "@/shared/testing";
import { App } from "./App";

function abrir(ruta: string) {
  window.history.pushState({}, "", ruta);
  const { fetch } = fetchConMetodo({
    "GET /api/obras": [{ cuerpo: estanteria }],
    "GET /api/admin/obras": [{ cuerpo: administracion }],
    "GET /api/entrevistas/ent-inventada/turnos": [{ cuerpo: historialAbierto }],
    "GET /api/obras/obra-regalo-inventada/generacion": [{ cuerpo: generacionEnCurso }],
  });
  render(<App cliente={crearCliente(fetch)} />);
}

describe("App · la novela regalo", () => {
  it("la raíz es la estantería", async () => {
    abrir("/");
    expect(await screen.findByRole("heading", { name: "La estantería" })).toBeInTheDocument();
    // SPEC-36 RF-01: el boton unico se llama como en la propuesta.
    expect(screen.getByRole("button", { name: "Encargar una novela" })).toBeInTheDocument();
  });

  it("la entrevista tiene su ruta", async () => {
    abrir("/entrevistas/ent-inventada");
    expect(await screen.findByRole("heading", { name: "La entrevista" })).toBeInTheDocument();
  });

  it("la generación tiene su ruta", async () => {
    abrir("/obras/obra-regalo-inventada/generacion");
    expect(await screen.findByRole("heading", { name: "La novela se está escribiendo" }))
      .toBeInTheDocument();
  });

  it("la cabecera dice qué es la web: novelas para regalar, no solo su lectura", async () => {
    abrir("/obras/obra-regalo-inventada/generacion");
    const cabecera = (await screen.findAllByRole("banner"))[0];
    expect(cabecera).toHaveTextContent("Novelas para regalar");
    expect(cabecera).not.toHaveTextContent("lectura");
  });

  it("la administración tiene su ruta y su enlace en la cabecera (SPEC-36 RF-03)", async () => {
    abrir("/admin");
    expect(await screen.findByRole("heading", { name: "Administración" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Administración" })).toHaveAttribute("href", "/admin");
  });

  it("la cabecera lleva a la estantería desde cualquier página", async () => {
    abrir("/obras/obra-regalo-inventada/generacion");
    expect(await screen.findByRole("link", { name: "Estantería" })).toHaveAttribute("href", "/");
  });
});
