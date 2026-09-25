// PLAN-37 H2 (SPEC-37): la historia de una novela en la administracion, como linea de tiempo.
// Todo llega resuelto del backend; la pagina lo pinta en el orden en que llega.
import { render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { fetchConMetodo, historiaDeObra } from "@/shared/testing";
import { PaginaHistoriaDeObra } from "./HistoriaDeObra";

function montar() {
  const doble = fetchConMetodo({
    "GET /api/admin/obras/obra-publicada/historia": [{ cuerpo: historiaDeObra }] });
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter initialEntries={["/admin/obras/obra-publicada"]}>
        <Routes><Route path="/admin/obras/:obra" element={<PaginaHistoriaDeObra />} /></Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("HistoriaDeObra", () => {
  it("cuenta la novela en orden, con las seis notas de cada capítulo", async () => {
    montar();
    expect(await screen.findByRole("heading", { name: "El mapa de Nerea" })).toBeInTheDocument();
    const eventos = screen.getAllByTestId(/^evento-/);
    expect(eventos.map((e) => e.getAttribute("data-tipo"))).toEqual(
      historiaDeObra.eventos.map((e) => e.tipo));
    const uno = screen.getByTestId("evento-3");
    expect(uno).toHaveTextContent("Capítulo 1");
    expect(within(uno).getAllByTestId(/^nota-/)).toHaveLength(6);
    expect(uno).toHaveTextContent("1,32 USD");
    expect(uno).toHaveTextContent("1 intento");
  });

  it("una parada y una ronda que no publica se distinguen con texto", async () => {
    montar();
    const parada = await screen.findByTestId("evento-5");
    expect(parada).toHaveTextContent("Parada en el capítulo 3");
    expect(parada).toHaveTextContent("bloqueante");
    expect(parada).toHaveTextContent("3 intentos");
    const puerta = screen.getByTestId("evento-6");
    expect(puerta).toHaveTextContent("no publica");
    expect(puerta).toHaveTextContent("Lean 2");
    expect(puerta).toHaveTextContent("INV-28 (obra): sin veredicto");
    expect(screen.getByTestId("evento-7")).toHaveTextContent("publica");
  });

  it("una versión trae su petición y sus capítulos", async () => {
    montar();
    const v = await screen.findByTestId("evento-8");
    expect(v).toHaveTextContent("Versión 2");
    expect(v).toHaveTextContent("el perro se llama Nala");
    expect(v).toHaveTextContent("capítulos 4, 5, 6");
  });

  it("las rondas del plan traen sus objeciones y dicen que no tienen hora", async () => {
    montar();
    const r1 = await screen.findByTestId("evento-1");
    expect(r1).toHaveTextContent("el recuerdo de Lisboa no aparece");
    expect(r1).toHaveTextContent("sin hora");
  });

  it("el lateral trae los totales, el coste por agente y los abiertos", async () => {
    montar();
    const lado = await screen.findByTestId("totales");
    expect(lado).toHaveTextContent("16,89 USD");
    expect(lado).toHaveTextContent("como mínimo");
    expect(lado).toHaveTextContent("escritor");
    expect(lado).toHaveTextContent("INV-26");
    expect(lado).toHaveTextContent("cap. 4");
  });

  it("el coste atribuido dice cómo se atribuyó", async () => {
    montar();
    expect(await screen.findByTestId("atribucion")).toHaveTextContent("atribucion por el progreso");
  });
});
