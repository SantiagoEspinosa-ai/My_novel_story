// PLAN-39 P4 (SPEC-39): publicar y reanudar desde la web. Si se puede, por que no, desde donde
// y cuanto lo dice el backend; aqui se ensena, y nada que gaste se lanza sin avisar.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  accionesGenerar, accionesNinguna, accionesPublicar, accionesReanudar, accionesSinLean,
  confirmacionConUltima, fetchConMetodo,
} from "@/shared/testing";
import { AccionesDeObra } from "./AccionesDeObra";
import { BotonDeAccion } from "./BotonDeAccion";

const O = "/api/obras/obra-x";

function montar(acciones: unknown, otras: Parameters<typeof fetchConMetodo>[0] = {}) {
  const doble = fetchConMetodo({
    [`GET ${O}/acciones`]: [{ cuerpo: acciones }],
    "GET /api/generaciones/gasto": [{ cuerpo: confirmacionConUltima }], ...otras });
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter initialEntries={["/aqui"]}>
        <Routes>
          <Route path="/aqui" element={<AccionesDeObra obra="obra-x" intervaloMs={5} />} />
          <Route path="/obras/:obra/generacion" element={<p>pagina de la generacion</p>} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
  return doble;
}

describe("AccionesDeObra", () => {
  it("publicar avisa del Editor y enseña la condición que falló", async () => {
    const { pedidas } = montar(accionesPublicar, {
      [`POST ${O}/publicaciones`]: [{ estado: 202, cuerpo: { id_trabajo: "t-1" } }],
      "GET /api/trabajos/t-1": [{ cuerpo: { estado: "terminado", motivo: null, resultado: {
        publicada: false, ronda: 1, version: 1,
        condiciones: [{ invariante: "INV-28", capitulo: null, detalle: "sin veredicto" }],
        lean: { codigo: 2, detalle: "no habia dato bastante" } } } }],
    });
    const bloque = await screen.findByTestId("publicar");
    expect(bloque).toHaveTextContent("Editor");
    expect(bloque).toHaveTextContent("0,31 USD");
    fireEvent.click(screen.getByRole("button", { name: /Publicar/ }));
    const r = await screen.findByTestId("resultado-publicar");
    expect(r).toHaveTextContent("No se publicó");
    expect(r).toHaveTextContent("INV-28");
    expect(r).toHaveTextContent("sin veredicto");
    expect(r).toHaveTextContent("Lean 2");
    expect(pedidas.map((p) => p.clave)).toContain(`POST ${O}/publicaciones`);
  });

  it("publicada lo dice y lleva a leerla", async () => {
    montar(accionesPublicar, {
      [`POST ${O}/publicaciones`]: [{ estado: 202, cuerpo: { id_trabajo: "t-1" } }],
      "GET /api/trabajos/t-1": [{ cuerpo: { estado: "terminado", motivo: null, resultado: {
        publicada: true, ronda: 1, version: 1, condiciones: [], lean: { codigo: 0, detalle: null } } } }],
    });
    fireEvent.click(await screen.findByRole("button", { name: /Publicar/ }));
    expect(await screen.findByRole("link", { name: "Leer la novela" })).toHaveAttribute("href", "/obras/obra-x");
  });

  it("sin Lean lo dice y no hay botón", async () => {
    montar(accionesSinLean);
    expect(await screen.findByRole("alert")).toHaveTextContent("Falta Lean");
    expect(screen.queryByRole("button", { name: /Publicar/ })).toBeNull();
  });

  it("reanudar dice desde qué capítulo y cuánto, y no se lanza sin confirmar", async () => {
    const { pedidas } = montar(accionesReanudar, {
      [`POST ${O}/generaciones`]: [{ estado: 202, cuerpo: { id_trabajo: "t-2", generacion: "g" } }],
    });
    const b = await screen.findByTestId("reanudar");
    expect(b).toHaveTextContent("desde el capítulo 4");
    expect(b).toHaveTextContent("faltan 7");
    expect(b).toHaveTextContent("10,50 USD");
    expect(b).toHaveTextContent("la media de los 3 capítulos medidos");
    expect(pedidas.map((p) => p.clave)).not.toContain(`POST ${O}/generaciones`);
    const boton = screen.getByRole("button", { name: /Sí, reanudar/ });
    await waitFor(() => expect(boton).toBeEnabled());
    expect(b).toHaveTextContent("17,40 USD de 50 USD");
    fireEvent.click(boton);
    expect(await screen.findByText("pagina de la generacion")).toBeInTheDocument();
  });

  it("si no hay nada que hacer, no pinta nada", async () => {
    const { pedidas } = montar({ publicar: accionesReanudar.publicar, reanudar: accionesPublicar.reanudar,
      generar: accionesPublicar.generar });
    await waitFor(() => expect(pedidas.map((p) => p.clave)).toContain(`GET ${O}/acciones`));
    expect(screen.queryByTestId("publicar")).toBeNull();
    expect(screen.queryByTestId("reanudar")).toBeNull();
  });
});

// PLAN-44 G2 (SPEC-44): generar, y el boton de cada fila de la administracion.
describe("AccionesDeObra › generar", () => {
  it("una novela sin generar ofrece generarla con su estimación", async () => {
    const { pedidas } = montar(accionesGenerar, {
      [`POST ${O}/generaciones`]: [{ estado: 202, cuerpo: { id_trabajo: "t-9", generacion: "gen-9" } }],
    });
    const bloque = await screen.findByTestId("generar");
    expect(bloque).toHaveTextContent("5,81 USD");
    expect(bloque).toHaveTextContent("la media de las 2 novelas publicadas en esta base");
    fireEvent.click(await screen.findByRole("button", { name: /Sí, generar/ }));
    expect(await screen.findByText("pagina de la generacion")).toBeInTheDocument();
    expect(pedidas.map((p) => p.clave)).toContain(`POST ${O}/generaciones`);
  });
});

function montarBoton(acciones: unknown) {
  const doble = fetchConMetodo({ [`GET ${O}/acciones`]: [{ cuerpo: acciones }] });
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter><BotonDeAccion obra="obra-x" /></MemoryRouter>
    </ClienteProvider>,
  );
}

describe("BotonDeAccion", () => {
  it.each([
    [accionesGenerar, "Generar"], [accionesReanudar, "Reanudar"], [accionesPublicar, "Publicar"],
  ])("ofrece la acción que toca y lleva a la página de la novela", async (acciones, nombre) => {
    montarBoton(acciones);
    expect(await screen.findByRole("link", { name: nombre })).toHaveAttribute(
      "href", "/admin/obras/obra-x");
  });

  it("sin ninguna posible no ofrece nada", async () => {
    montarBoton(accionesNinguna);
    await waitFor(() => expect(screen.queryByRole("link")).toBeNull());
  });
});
