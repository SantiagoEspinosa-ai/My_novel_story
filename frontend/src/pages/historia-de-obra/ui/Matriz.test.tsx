// PLAN-38 M3 (SPEC-38): la pagina de cada novela se abre en la matriz por capitulo. Todo llega
// resuelto del backend, medias y totales incluidos; la pagina lo pinta. Datos inventados.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { NOTA_DEL_EDITOR } from "@/shared/ui";
import { fetchConMetodo, historiaDeObra, matrizDeObra } from "@/shared/testing";
import { PaginaHistoriaDeObra } from "./HistoriaDeObra";

const M = "/api/admin/obras/obra-publicada/matriz";

function montar(entrada = "/admin/obras/obra-publicada") {
  const doble = fetchConMetodo({
    [`GET ${M}`]: [{ cuerpo: matrizDeObra }],
    [`GET ${M}?version=1`]: [{ cuerpo: { ...matrizDeObra, version: 1 } }],
    "GET /api/admin/obras/obra-publicada/historia": [{ cuerpo: historiaDeObra }],
  });
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter initialEntries={[entrada]}>
        <Routes><Route path="/admin/obras/:obra" element={<PaginaHistoriaDeObra />} /></Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
  return doble;
}

describe("Matriz", () => {
  it("una fila por capítulo con las seis notas escritas y en color", async () => {
    montar();
    const uno = await screen.findByTestId("fila-1");
    const notas = within(uno).getAllByTestId(/^celda-/);
    expect(notas.map((n) => n.textContent)).toEqual(["4", "5", "3", "4", "2", "5"]);
    expect(notas[4]).toHaveAttribute("data-nota", "2");
    expect(notas[4].style.background).not.toBe("");
    expect(uno).toHaveTextContent("1,32 USD");
    expect(uno).toHaveTextContent("1 mayor");
    expect(screen.getAllByTestId(/^fila-\d/)).toHaveLength(3);
  });

  it("un capítulo parado se marca con texto, y el que cambió también", async () => {
    montar();
    expect(await screen.findByTestId("fila-2")).toHaveTextContent("parada");
    expect(screen.getByTestId("fila-3")).toHaveTextContent("cambió");
    expect(screen.getByTestId("fila-1")).toHaveTextContent("igual");
  });

  it("la fila de medias y totales", async () => {
    montar();
    const t = await screen.findByTestId("fila-totales");
    expect(t).toHaveTextContent("3,22 USD");
    expect(t).toHaveTextContent("4");
    expect(t).toHaveTextContent("1 de 3");
  });

  it("la leyenda explica cada color", async () => {
    montar();
    const l = await screen.findByTestId("leyenda");
    for (const d of Object.values(NOTA_DEL_EDITOR)) expect(l).toHaveTextContent(d.etiqueta);
  });

  it("las cuatro cifras de arriba", async () => {
    montar();
    const c = await screen.findByTestId("cifras");
    expect(c).toHaveTextContent("16,89 USD");
    expect(c).toHaveTextContent("36");
    expect(c).toHaveTextContent("14,70 USD de 50 USD");
    expect(c).toHaveTextContent("3");
  });

  it("debajo, las paradas y la puerta; al lado, el coste por agente, los abiertos y el aviso", async () => {
    montar();
    expect(await screen.findByTestId("paradas")).toHaveTextContent("bloqueante");
    expect(screen.getByTestId("puerta")).toHaveTextContent("Lean 2");
    expect(screen.getByTestId("puerta")).toHaveTextContent("no publica");
    const lado = screen.getByTestId("panel-lateral");
    expect(lado).toHaveTextContent("escritor");
    expect(lado).toHaveTextContent("INV-26");
    expect(screen.getByTestId("atribucion")).toHaveTextContent("atribucion");
  });

  it("cambiar de versión pide esa versión", async () => {
    const { pedidas } = montar();
    fireEvent.click(await screen.findByRole("link", { name: /Versión 1/ }));
    await waitFor(() => expect(pedidas.map((p) => p.clave)).toContain(`GET ${M}?version=1`));
  });

  it("la línea de tiempo es la segunda pestaña", async () => {
    montar();
    fireEvent.click(await screen.findByRole("link", { name: "Línea de tiempo" }));
    expect(await screen.findByTestId("evento-0")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Por capítulo" })).toBeInTheDocument();
  });
});

describe("Matriz › sin capítulos", () => {
  it("una novela sin capítulos escritos sigue nombrando los seis criterios del Editor (F-216)", async () => {
    const vacia = { ...matrizDeObra, filas: [] };
    const doble = fetchConMetodo({ [`GET ${M}`]: [{ cuerpo: vacia }] });
    render(
      <ClienteProvider cliente={crearCliente(doble.fetch)}>
        <MemoryRouter initialEntries={["/admin/obras/obra-publicada"]}>
          <Routes><Route path="/admin/obras/:obra" element={<PaginaHistoriaDeObra />} /></Routes>
        </MemoryRouter>
      </ClienteProvider>,
    );
    for (const c of ["cont.", "tono", "arco", "pers.", "ritmo", "perso."]) {
      expect(await screen.findByRole("columnheader", { name: c })).toBeInTheDocument();
    }
  });
});
