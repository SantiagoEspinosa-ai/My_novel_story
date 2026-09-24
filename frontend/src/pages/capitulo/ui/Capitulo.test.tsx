// PLAN-22 E9: la lectura continua de un capitulo, una escena por bloque y cada una con su
// estado y sus hallazgos (SPEC-22 RF-39, RF-41).
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  capituloA, capituloB, escenaConsolidada, fetchDeFixtures, hechosDeB1,
} from "@/shared/testing";
import { PaginaCapitulo } from "./Capitulo";

function montar(id: string) {
  const cliente = crearCliente(fetchDeFixtures({
    "/api/capitulos/cap-b": capituloB, "/api/capitulos/cap-a": capituloA,
    "/api/escenas/esc-b1/hechos": hechosDeB1,
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
  it("cada escena de la lectura continua lleva su estado y sus hallazgos", async () => {
    montar("cap-a");
    const bloques = await screen.findAllByTestId("bloque-de-escena");
    expect(bloques).toHaveLength(2);
    for (const b of bloques) {
      expect(within(b).getByTestId("estado-de-escena")).toBeInTheDocument();
      expect(b.querySelector(".hallazgos, .sin-hallazgos")).not.toBeNull();
    }
    expect(within(bloques[0]).getByTestId("hallazgo")).toHaveAttribute("data-estado", "sin_veredicto");
  });

  it("no junta textos: una escena, un bloque", async () => {
    montar("cap-b");
    const bloques = await screen.findAllByTestId("bloque-de-escena");
    expect(bloques.map((b) => b.getAttribute("data-escena"))).toEqual(["esc-b1", "esc-b2"]);
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

  it("dice su numero con el orden que trae y enlaza con el indice", async () => {
    montar("cap-a");
    expect(await screen.findByRole("heading", { name: "Capítulo 2" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Índice" })).toHaveAttribute(
      "href", "/obras/obra-inventada/indice");
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
