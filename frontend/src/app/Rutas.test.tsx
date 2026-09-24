// PLAN-33 E14 (SPEC-33 RF-01, RF-04): la novela regalo entra en la web. La raiz es la
// estanteria, y la entrevista y la generacion tienen sus rutas. Compone paginas, asi que vive
// en app/ (FSD: una pagina no importa otra).
import { render, screen } from "@testing-library/react";
import { crearCliente } from "@/shared/api";
import {
  estanteria, fetchConMetodo, generacionEnCurso, historialAbierto,
} from "@/shared/testing";
import { App } from "./App";

function abrir(ruta: string) {
  window.history.pushState({}, "", ruta);
  const { fetch } = fetchConMetodo({
    "GET /api/obras": [{ cuerpo: estanteria }],
    "GET /api/entrevistas/ent-inventada/turnos": [{ cuerpo: historialAbierto }],
    "GET /api/obras/obra-regalo-inventada/generacion": [{ cuerpo: generacionEnCurso }],
  });
  render(<App cliente={crearCliente(fetch)} />);
}

describe("App · la novela regalo", () => {
  it("la raíz es la estantería", async () => {
    abrir("/");
    expect(await screen.findByRole("heading", { name: "La estantería" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Generar novela" })).toBeInTheDocument();
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

  it("la cabecera lleva a la estantería desde cualquier página", async () => {
    abrir("/obras/obra-regalo-inventada/generacion");
    expect(await screen.findByRole("link", { name: "Estantería" })).toHaveAttribute("href", "/");
  });
});
