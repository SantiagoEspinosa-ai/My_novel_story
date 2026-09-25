// PLAN-33 E13 (SPEC-33 RF-01..RF-04), reescritas en PLAN-36 G2 (SPEC-36 RF-01): la estanteria
// son lomos en baldas de madera. Lo que antes estaba en la tarjeta esta ahora en el lomo
// (titulo y estado) o en su ficha, que se abre al pulsarlo (dedicatoria, destinatario y lo que
// se puede hacer). Lo ausente se dice como ausente; el estado llega resuelto de la API.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { estanteria, fetchConMetodo } from "@/shared/testing";
import { PaginaEstanteria } from "./Estanteria";

function montar(rutas: Parameters<typeof fetchConMetodo>[0]) {
  const doble = fetchConMetodo(rutas);
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<PaginaEstanteria />} />
          <Route path="/entrevistas/:entrevista" element={<p>pagina de la entrevista</p>} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
  return doble;
}

const CON_OBRAS = { "GET /api/obras": [{ cuerpo: estanteria }] };

async function abrir(id: string) {
  fireEvent.click(await screen.findByTestId(`obra-${id}`));
  return screen.getByTestId("ficha-del-libro");
}

describe("Estanteria", () => {
  it("un lomo por obra, con su título y su estado en texto", async () => {
    montar(CON_OBRAS);
    const l = await screen.findByTestId("obra-obra-publicada");
    expect(l).toHaveTextContent("El mapa de Nerea");
    expect(l).toHaveTextContent("publicada");
    expect(screen.getAllByTestId(/^obra-/)).toHaveLength(estanteria.obras.length);
    expect(screen.getAllByTestId("balda").length).toBeGreaterThan(0);
  });

  it("pulsar un lomo abre su ficha con dedicatoria, destinatario y lo que se puede hacer",
    async () => {
      montar(CON_OBRAS);
      const f = await abrir("obra-publicada");
      expect(f).toHaveTextContent("El mapa de Nerea");
      expect(f).toHaveTextContent("Para Nerea, que siempre llega.");
      expect(f).toHaveTextContent("Nerea Salgado");
      expect(within(f).getByRole("link", { name: /Leer/ })).toHaveAttribute("href", "/obras/obra-publicada");
      expect(screen.getByTestId("obra-obra-publicada")).toHaveAttribute("aria-pressed", "true");
    });

  it("sin generación lo dice en texto", async () => {
    montar(CON_OBRAS);
    expect(await screen.findByTestId("obra-obra-a-medias")).toHaveTextContent("sin generación");
  });

  it("sin título, el lomo lo dice", async () => {
    montar(CON_OBRAS);
    expect(await screen.findByTestId("obra-obra-a-medias")).toHaveTextContent("sin título");
  });

  it("destinatario ausente se ve como dato ausente, y la dedicatoria sigue", async () => {
    montar(CON_OBRAS);
    const f = await abrir("obra-entregada");
    expect(within(f).getByText("destinatario sin dato")).toHaveAttribute("data-sin-dato", "true");
    expect(f).toHaveTextContent("A mi hermana.");
  });

  it("cada ficha lleva a donde se puede seguir", async () => {
    montar(CON_OBRAS);
    expect(within(await abrir("obra-a-medias")).getByRole("link", { name: /Seguir la entrevista/ }))
      .toHaveAttribute("href", "/entrevistas/ent-3");
    expect(within(await abrir("obra-escribiendose")).getByRole("link", { name: /Ver cómo se escribe/ }))
      .toHaveAttribute("href", "/obras/obra-escribiendose/generacion");
  });

  it("hay un solo botón para encargar, y abre una entrevista nueva", async () => {
    const { pedidas } = montar({
      ...CON_OBRAS,
      "POST /api/entrevistas": [{ estado: 201, cuerpo: { id: "ent-nueva", obra: "obra-nueva" } }],
    });
    await screen.findByTestId("obra-obra-publicada");
    const botones = screen.getAllByRole("button", { name: "Encargar una novela" });
    expect(botones).toHaveLength(1);
    fireEvent.click(botones[0]);
    expect(await screen.findByText("pagina de la entrevista")).toBeInTheDocument();
    expect(pedidas.map((p) => p.clave)).toContain("POST /api/entrevistas");
  });

  it("una estantería vacía lo dice y sigue ofreciendo el botón", async () => {
    montar({ "GET /api/obras": [{ cuerpo: { obras: [] } }] });
    expect(await screen.findByText(/Todavía no hay ninguna novela/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Encargar una novela" })).toBeEnabled();
  });
});
