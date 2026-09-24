// PLAN-22 E10 (VER-107): las fichas enlazan los capitulos que trae la respuesta, ni uno mas,
// y lo que no consta se dice (SPEC-22 RF-43, RF-44).
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { fetchDeFixtures, fichas } from "@/shared/testing";
import { PaginaFichas } from "./Fichas";

async function montar() {
  const cliente = crearCliente(fetchDeFixtures({ "/api/obras/obra-inventada/fichas": fichas }));
  render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={["/obras/obra-inventada/fichas"]}>
        <Routes><Route path="/obras/:obra/fichas" element={<PaginaFichas />} /></Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
  return screen.findAllByTestId("ficha");
}

const ficha = (todas: HTMLElement[], id: string) =>
  todas.find((f) => f.getAttribute("data-ficha") === id)!;

describe("Fichas", () => {
  it("cada ficha enlaza exactamente los capitulos que trae la respuesta, ni uno mas", async () => {
    const todas = await montar();
    const esperado = [...fichas.personajes, ...fichas.lugares];
    expect(todas.map((f) => f.getAttribute("data-ficha"))).toEqual(esperado.map((f) => f.id));
    for (const f of esperado) {
      const hrefs = within(ficha(todas, f.id)).queryAllByRole("link")
        .map((a) => a.getAttribute("href"));
      expect(hrefs).toEqual((f.capitulos_donde_aparece ?? []).map(
        (c) => `/obras/obra-inventada/capitulos/${c.id}`));
    }
    expect(within(ficha(todas, "per-uno")).getAllByRole("link").map((a) => a.textContent))
      .toEqual(["Capítulo 1", "Capítulo 2"]);
  });

  it("un nombre nulo pinta el id y lo dice", async () => {
    const todas = await montar();
    const nombre = within(ficha(todas, "per-dos")).getByTestId("nombre");
    // F-81: el aviso va fuera del titulo, en su propia linea; dentro partia el titulo en dos.
    expect(nombre).toHaveTextContent(/^per-dos$/);
    expect(within(ficha(todas, "per-dos")).getByTestId("aviso-de-nombre"))
      .toHaveTextContent("sin nombre guardado");
    expect(within(ficha(todas, "per-uno")).getByTestId("nombre")).toHaveTextContent(/^Nombre inventado$/);
  });

  it("alias, rol y atmosfera nulos pintan «sin dato»", async () => {
    const todas = await montar();
    const dos = ficha(todas, "per-dos");
    expect(within(dos).getByTestId("alias")).toHaveTextContent("sin dato");
    expect(within(dos).getByTestId("rol_dramatico")).toHaveTextContent("sin dato");
    expect(within(ficha(todas, "lug-faro")).getByTestId("atmosfera")).toHaveTextContent("sin dato");
    expect(within(ficha(todas, "per-uno")).getByTestId("rol_dramatico")).toHaveTextContent("protagonista");
  });

  it("presentes sin declarar se dicen «no declarado»", async () => {
    const todas = await montar();
    expect(within(ficha(todas, "per-dos")).getByTestId("capitulos")).toHaveTextContent("no declarado");
    // Una lista vacia es otra cosa: se miro y no aparece en ninguno.
    const casa = within(ficha(todas, "lug-casa")).getByTestId("capitulos");
    expect(casa).toHaveTextContent("ninguno");
    expect(casa).not.toHaveTextContent("no declarado");
  });
});
