// PLAN-22 E8 (VER-107): la portada pinta el titulo y la dedicatoria de la obra; sin
// dedicatoria, solo el titulo y nada de relleno (SPEC-22 RF-46).
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { fetchDeFixtures, indice, indiceSinDedicatoria } from "@/shared/testing";
import { PaginaPortada } from "./Portada";

const DISPONIBLE = "/api/obras/obra-inventada/pdf/disponible";

function montar(datos: typeof indice, pdf?: { disponible: boolean; motivo: string | null }) {
  const cliente = crearCliente(fetchDeFixtures({
    "/api/obras/obra-inventada/indice": datos, ...(pdf ? { [DISPONIBLE]: pdf } : {}) }));
  return render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={["/obras/obra-inventada"]}>
        <Routes><Route path="/obras/:obra" element={<PaginaPortada />} /></Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Portada", () => {
  it("pinta la dedicatoria de la obra y, sin ella, solo el titulo, sin texto de relleno", async () => {
    const con = montar(indice);
    expect(await screen.findByRole("heading", { name: "Titulo inventado" })).toBeInTheDocument();
    expect(screen.getByTestId("dedicatoria")).toHaveTextContent("Para nadie real");
    con.unmount();

    const { container } = montar(indiceSinDedicatoria);
    expect(await screen.findByRole("heading", { name: "Titulo inventado" })).toBeInTheDocument();
    expect(screen.queryByTestId("dedicatoria")).toBeNull();
    const nav = screen.getByRole("navigation");
    const fuera = container.textContent!.replace(nav.textContent!, "");
    expect(fuera).toBe("Titulo inventado");
  });

  // Reescrita por PLAN-35 E4: comprobaba que la portada enlaza **a su propia obra**, y lo sigue
  // comprobando con el enlace nuevo a empezar a leer, que lleva al primer capitulo en orden.
  it("enlaza con el primer capitulo, el indice y las fichas de su obra", async () => {
    montar(indice);
    const enlaces = await screen.findAllByRole("link");
    expect(enlaces.map((a) => a.getAttribute("href"))).toEqual([
      `/obras/obra-inventada/capitulos/${indice.capitulos[0].id}`,
      "/obras/obra-inventada/indice",
      "/obras/obra-inventada/fichas",
    ]);
  });

  it("con PDF disponible ofrece descargarlo", async () => {
    montar(indice, { disponible: true, motivo: null });
    const pdf = await screen.findByRole("link", { name: "Descargar en PDF" });
    expect(pdf).toHaveAttribute("href", "/api/obras/obra-inventada/pdf");
  });

  it("sin PDF no ofrece el boton y dice por que", async () => {
    montar(indice, { disponible: false, motivo: "la ronda 1 de la puerta no publico la obra" });
    expect(await screen.findByText(/no publico la obra/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Descargar en PDF" })).toBeNull();
  });
});
