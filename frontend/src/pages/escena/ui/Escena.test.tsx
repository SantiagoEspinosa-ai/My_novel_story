// PLAN-22 E9: la vista de una escena, con su estado y sus hallazgos (SPEC-22 RF-39).
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { escenaRendida, fetchDeFixtures } from "@/shared/testing";
import { PaginaEscena } from "./Escena";

describe("Escena", () => {
  it("pinta la escena con su estado, sus hallazgos y su texto, y enlaza con su capitulo", async () => {
    const cliente = crearCliente(fetchDeFixtures({ "/api/escenas/esc-b2": escenaRendida }));
    render(
      <ClienteProvider cliente={cliente}>
        <MemoryRouter initialEntries={["/obras/obra-inventada/escenas/esc-b2"]}>
          <Routes><Route path="/obras/:obra/escenas/:escena" element={<PaginaEscena />} /></Routes>
        </MemoryRouter>
      </ClienteProvider>,
    );
    expect(await screen.findByTestId("estado-de-escena")).toHaveAttribute("data-rendida", "true");
    expect(screen.getByTestId("hallazgo")).toHaveTextContent("INV-17");
    expect(screen.getByTestId("texto-de-escena")).toHaveTextContent("Texto rendido inventado.");
    expect(screen.getByRole("link", { name: "Su capítulo" })).toHaveAttribute(
      "href", "/obras/obra-inventada/capitulos/cap-b");
  });
});
