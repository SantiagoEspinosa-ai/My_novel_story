// PLAN-33 E7 (SPEC-33 RF-14..RF-17): la generacion, visible. Los capitulos en fila con su
// fase y las notas del Editor al cerrarse cada uno. Todo llega resuelto de la API.
import { act, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  fetchConMetodo, generacionEnCurso, generacionFallida, generacionParada, generacionPlanificando,
  generacionPublicada, generacionSinPublicar,
} from "@/shared/testing";
import { PaginaGeneracion } from "./Generacion";

const G = "/api/obras/obra-regalo-inventada/generacion";

function montar(respuestas: unknown[], otras: Parameters<typeof fetchConMetodo>[0] = {}) {
  const doble = fetchConMetodo({ [`GET ${G}`]: respuestas.map((cuerpo) => ({ cuerpo })), ...otras });
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter initialEntries={["/obras/obra-regalo-inventada/generacion"]}>
        <Routes>
          <Route path="/obras/:obra/generacion"
            element={<PaginaGeneracion intervaloMs={1000} />} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
  return doble;
}

describe("Generacion", () => {
  it("enseña cada capítulo con su fase en texto", async () => {
    montar([generacionEnCurso]);
    const fila = await screen.findByTestId("capitulos");
    expect(fila.children).toHaveLength(10);
    expect(screen.getByTestId("capitulo-2")).toHaveTextContent("editando");
  });

  it("un capítulo terminado dice el estado de su escena, no su última fase (F-200)", async () => {
    montar([generacionEnCurso]);
    const uno = await screen.findByTestId("capitulo-1");
    expect(uno).toHaveTextContent("consolidada");
    expect(uno).not.toHaveTextContent("resumiendo");
  });

  it("un capítulo no empezado dice no empezado", async () => {
    montar([generacionEnCurso]);
    expect(await screen.findByTestId("capitulo-7")).toHaveTextContent("no empezado");
  });

  it("parada enseña su motivo", async () => {
    montar([generacionParada]);
    const c = await screen.findByTestId("capitulo-3");
    expect(c).toHaveTextContent("parada");
    expect(c).toHaveTextContent("FalloDeTransporte");
  });

  it("las notas aparecen cuando el capítulo las trae", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const sinNotas = { ...generacionEnCurso, capitulos: generacionEnCurso.capitulos.map(
        (c) => ({ ...c, notas: [] })) };
      montar([sinNotas, generacionEnCurso]);
      await screen.findByTestId("capitulo-1");
      expect(screen.queryByTestId("notas-1")).toBeNull();
      await act(async () => { await vi.advanceTimersByTimeAsync(1100); });
      const notas = await screen.findByTestId("notas-1");
      expect(within(notas).getAllByRole("listitem")).toHaveLength(6);
      expect(notas).toHaveTextContent("coherencia de personajes");
    } finally {
      vi.useRealTimers();
    }
  });

  it("una nota bajo el umbral se distingue con texto y no solo con color", async () => {
    montar([generacionEnCurso]);
    const notas = await screen.findByTestId("notas-1");
    const ritmo = within(notas).getByTestId("nota-ritmo");
    expect(ritmo).toHaveTextContent("2/5");
    expect(ritmo).toHaveTextContent("bajo el umbral");
    expect(ritmo).toHaveTextContent("acelera el final");
    expect(within(notas).getByTestId("nota-tono")).not.toHaveTextContent("bajo el umbral");
  });

  it("reutiliza la barra de progreso de la obra", async () => {
    const { pedidas } = montar([generacionEnCurso]);
    await screen.findByTestId("capitulos");
    expect(pedidas.map((p) => p.clave))
      .toContain("GET /api/obras/obra-regalo-inventada/progreso");
  });

  // PLAN-35 F6 (SPEC-35 RF-13): de noche, y lo que la pagina dice al empezar y al acabar.
  it("un lanzamiento fallido enseña su motivo", async () => {
    montar([generacionFallida]);
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("no se pudo empezar");
    expect(alerta).toHaveTextContent("no se encuentra el ejecutable de Claude Code");
  });

  it("planificando, sin capítulos, lo dice", async () => {
    montar([generacionPlanificando]);
    expect(await screen.findByTestId("sin-capitulos")).toHaveTextContent("plan");
    expect(screen.queryByTestId("capitulos")).toBeNull();
  });

  it("publicada lleva a leer la novela", async () => {
    montar([generacionPublicada]);
    expect(await screen.findByRole("heading", { name: "La novela está escrita" })).toBeInTheDocument();
    expect(await screen.findByRole("link", { name: "Leer la novela" }))
      .toHaveAttribute("href", "/obras/obra-regalo-inventada");
  });

  it("sin publicar lleva a leer lo escrito y dice por qué", async () => {
    montar([generacionSinPublicar], {
      "GET /api/obras/obra-regalo-inventada/pdf/disponible": [{ cuerpo: {
        disponible: false, motivo: "la ronda 1 de la puerta no publico la obra: Lean no disponible" } }],
    });
    expect(await screen.findByRole("link", { name: "Leer lo escrito" }))
      .toHaveAttribute("href", "/obras/obra-regalo-inventada");
    expect(await screen.findByTestId("sin-publicar")).toHaveTextContent("Lean no disponible");
  });

  it("en curso no ofrece leer todavía", async () => {
    montar([generacionEnCurso]);
    await screen.findByTestId("capitulos");
    expect(screen.queryByRole("link", { name: /Leer/ })).toBeNull();
  });
});
