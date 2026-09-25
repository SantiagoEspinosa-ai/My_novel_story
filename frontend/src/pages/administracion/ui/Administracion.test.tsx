// PLAN-36 G4 (SPEC-36 RF-03): la administracion, sin login. Todo llega resuelto del backend;
// la pagina lo pinta. Datos inventados.
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { administracion, fetchConMetodo } from "@/shared/testing";
import { PaginaAdministracion } from "./Administracion";

function montar() {
  const doble = fetchConMetodo({ "GET /api/admin/obras": [{ cuerpo: administracion }] });
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter><PaginaAdministracion /></MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Administracion", () => {
  it("cada novela con su fase, coste, hallazgos y Lean, tal como llegan", async () => {
    montar();
    const fila = await screen.findByTestId("admin-obra-publicada");
    expect(fila).toHaveTextContent("El mapa de Nerea");
    expect(fila).toHaveTextContent("publicada");
    expect(fila).toHaveTextContent("12,30 USD");
    expect(fila).toHaveTextContent("30");
    expect(fila).toHaveTextContent("1 mayor");
    expect(fila).toHaveTextContent("0");
    expect(screen.getAllByTestId(/^admin-obra-/)).toHaveLength(administracion.obras.length);
    // SPEC-37 RF-01: cada novela lleva a su historia.
    expect(within(fila).getByRole("link")).toHaveAttribute("href", "/admin/obras/obra-publicada");
  });

  it("un coste con suelo lo dice, y lo ausente se dice", async () => {
    montar();
    const f = await screen.findByTestId("admin-obra-escribiendose");
    expect(f).toHaveTextContent("como mínimo");
    const sin = screen.getByTestId("admin-obra-a-medias");
    expect(within(sin).getAllByText("—").length).toBeGreaterThan(0);
    expect(sin).toHaveTextContent("sin generación");
  });

  it("enseña lo gastado frente al techo y avisa de que no tiene login", async () => {
    montar();
    expect(await screen.findByTestId("admin-gastado")).toHaveTextContent("14,70 USD de 50 USD");
    expect(screen.getByRole("note")).toHaveTextContent("sin login");
  });
});
