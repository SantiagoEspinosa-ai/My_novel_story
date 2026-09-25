// PLAN-22 E9: la lectura continua de un capitulo, una escena por bloque (SPEC-22 RF-41).
// PLAN-43 L2 (SPEC-43): es para el lector: sin estado, sin hallazgos y sin identificadores;
// titulo «Capitulo N · titulo» y, al final, anterior, siguiente e indice.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  capituloA, capituloB, escenaConsolidada, fetchDeFixtures, hechosDeB1, indice,
} from "@/shared/testing";
import { PaginaCapitulo } from "./Capitulo";

function montar(id: string) {
  const cliente = crearCliente(fetchDeFixtures({
    "/api/capitulos/cap-b": capituloB, "/api/capitulos/cap-a": capituloA,
    "/api/escenas/esc-b1/hechos": hechosDeB1, "/api/obras/obra-inventada/indice": indice,
  }));
  return render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={[`/obras/obra-inventada/capitulos/${id}`]}>
        <Routes>
          <Route path="/obras/:obra/capitulos/:capitulo" element={<PaginaCapitulo />} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Capitulo", () => {
  it("no enseña al lector ni el estado ni los hallazgos (SPEC-43 RF-01)", async () => {
    const { container } = montar("cap-a");
    await screen.findAllByTestId("bloque-de-escena");
    expect(screen.queryByTestId("estado-de-escena")).toBeNull();
    expect(screen.queryByTestId("hallazgo")).toBeNull();
    expect(container.textContent).not.toMatch(/INV-\d+|consolidada|sin_veredicto|capítulo abierto|esc-a1/);
  });

  it("el título es Capítulo N y el del capítulo si lo tiene (RF-02)", async () => {
    montar("cap-b");
    expect(await screen.findByRole("heading", { level: 1, name: "Capítulo 1 · El faro inventado" }))
      .toBeInTheDocument();
  });

  it("sin título en el plan, solo Capítulo N", async () => {
    montar("cap-a");
    expect(await screen.findByRole("heading", { level: 1, name: "Capítulo 2" })).toBeInTheDocument();
  });

  it("al final navega al siguiente y al índice; el primero no tiene anterior (RF-03)", async () => {
    montar("cap-b");
    const nav = await screen.findByRole("navigation", { name: "entre capítulos" });
    expect(within(nav).getByRole("link", { name: /Siguiente/ })).toHaveAttribute(
      "href", "/obras/obra-inventada/capitulos/cap-a");
    expect(within(nav).getByRole("link", { name: /volver al índice/i })).toHaveAttribute(
      "href", "/obras/obra-inventada/indice");
    expect(within(nav).queryByRole("link", { name: /Anterior/ })).toBeNull();
  });

  it("el último navega al anterior y no tiene siguiente", async () => {
    montar("cap-a");
    const nav = await screen.findByRole("navigation", { name: "entre capítulos" });
    expect(within(nav).getByRole("link", { name: /Anterior/ })).toHaveAttribute(
      "href", "/obras/obra-inventada/capitulos/cap-b");
    expect(within(nav).queryByRole("link", { name: /Siguiente/ })).toBeNull();
  });

  it("no junta textos: una escena, un bloque", async () => {
    montar("cap-b");
    const bloques = await screen.findAllByTestId("bloque-de-escena");
    expect(bloques).toHaveLength(2);
    const textos = screen.getAllByTestId("texto-de-escena");
    expect(textos).toHaveLength(2);
    expect(textos[0].textContent).not.toContain("Texto rendido");
  });

  it("el texto se pinta tal como llega", async () => {
    montar("cap-b");
    const [primero] = await screen.findAllByTestId("texto-de-escena");
    expect(primero.textContent).toBe(escenaConsolidada.borrador!.texto);
    expect(primero.querySelector("p")!.style.whiteSpace).toBe("pre-wrap");
  });

  it("cada escena con texto ofrece pedir un cambio, y la seleccion llega como fragmento", async () => {
    // PLAN-22 E16: se pide desde la pagina del capitulo, escena a escena.
    montar("cap-b");
    const [b1] = await screen.findAllByTestId("bloque-de-escena");
    const texto = within(b1).getByTestId("texto-de-escena");
    const nodo = texto.querySelector("p")!.firstChild!;
    const rango = document.createRange();
    rango.setStart(nodo, 0);
    rango.setEnd(nodo, 13);
    const seleccion = window.getSelection()!;
    seleccion.removeAllRanges();
    seleccion.addRange(rango);
    fireEvent.mouseUp(texto);
    fireEvent.click(within(b1).getByRole("button", { name: /Pedir un cambio/ }));
    const panel = await within(b1).findByTestId("pedir-cambio");
    expect(panel).toHaveTextContent("Primer texto");
    expect(await within(panel).findByLabelText(/El faro existe/)).toBeInTheDocument();
  });
});
