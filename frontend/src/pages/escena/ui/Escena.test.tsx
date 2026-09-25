// PLAN-22 E9: la vista de una escena. PLAN-43 L2 (SPEC-43): para el lector, sin estado, sin
// hallazgos y con el titulo de su capitulo, nunca su id.
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { capituloB, escenaRendida, fetchDeFixtures } from "@/shared/testing";
import { PaginaEscena } from "./Escena";

function montar() {
  const cliente = crearCliente(fetchDeFixtures({
    "/api/escenas/esc-b2": escenaRendida, "/api/capitulos/cap-b": capituloB,
  }));
  return render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={["/obras/obra-inventada/escenas/esc-b2"]}>
        <Routes><Route path="/obras/:obra/escenas/:escena" element={<PaginaEscena />} /></Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Escena", () => {
  it("el título es el de su capítulo, no el id, y no enseña nada técnico (SPEC-43)", async () => {
    const { container } = montar();
    expect(await screen.findByRole("heading", { level: 1, name: "Capítulo 1 · El faro inventado" }))
      .toBeInTheDocument();
    expect(container.textContent).not.toMatch(/esc-b2|INV-\d+|rendición/);
    expect(screen.queryByTestId("estado-de-escena")).toBeNull();
    expect(screen.getByTestId("texto-de-escena")).toHaveTextContent("Texto rendido inventado.");
    expect(screen.getByRole("link", { name: "Su capítulo" })).toHaveAttribute(
      "href", "/obras/obra-inventada/capitulos/cap-b");
  });

  it("desde la vista de escena tambien se pide un cambio", async () => {
    montar();
    fireEvent.click(await screen.findByRole("button", { name: /Pedir un cambio/ }));
    expect(await screen.findByTestId("pedir-cambio")).toBeInTheDocument();
  });
});
