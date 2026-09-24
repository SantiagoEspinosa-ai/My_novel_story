// PLAN-22 E8 (VER-107): el indice pinta en el orden y con los enlaces que recibe. No
// reordena nada ni deduce a que capitulo va cada escena (SPEC-22 RF-38, NF-06).
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { fetchDeFixtures, indice } from "@/shared/testing";
import { PaginaIndice } from "./Indice";

function montar(datos = indice) {
  const cliente = crearCliente(fetchDeFixtures({ "/api/obras/obra-inventada/indice": datos }));
  return render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={["/obras/obra-inventada/indice"]}>
        <Routes><Route path="/obras/:obra/indice" element={<PaginaIndice />} /></Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Indice", () => {
  it("pinta los capitulos y las escenas en el orden de la respuesta", async () => {
    // Un orden que ninguna regla del navegador produciria: si la interfaz ordenara por id
    // o por orden, no saldria asi.
    const desordenado = structuredClone(indice);
    desordenado.capitulos.reverse();
    desordenado.capitulos[0].escenas.reverse();
    montar(desordenado);
    const capitulos = await screen.findAllByTestId("capitulo-del-indice");
    expect(capitulos.map((c) => c.getAttribute("data-capitulo"))).toEqual(["cap-a", "cap-b"]);
    const escenas = within(capitulos[0]).getAllByTestId("escena-del-indice");
    expect(escenas.map((e) => e.getAttribute("data-escena"))).toEqual(["esc-a2", "esc-a1"]);
    expect(within(capitulos[0]).getByText("Capítulo 2")).toBeInTheDocument();
  });

  it("cada capitulo enlaza con su id de capitulo", async () => {
    montar();
    const enlaces = await screen.findAllByRole("link", { name: /^Capítulo \d+$/ });
    expect(enlaces.map((a) => a.getAttribute("href"))).toEqual([
      "/obras/obra-inventada/capitulos/cap-b",
      "/obras/obra-inventada/capitulos/cap-a",
    ]);
  });

  it("cada escena del indice lleva su estado y sus hallazgos", async () => {
    montar();
    const escenas = await screen.findAllByTestId("escena-del-indice");
    expect(escenas).toHaveLength(4);
    for (const e of escenas) {
      expect(within(e).getByTestId("estado-de-escena")).toBeInTheDocument();
    }
  });
});
