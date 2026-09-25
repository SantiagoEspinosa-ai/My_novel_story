// PLAN-35 E7 (SPEC-35 RF-10): un capitulo cambiado de una version que nacio de una peticion dice
// que peticion lo cambio, con las palabras del lector, y enlaza a como era antes. Un capitulo
// compartido, o una version sin peticion, no lleva aviso: no se inventa un porque.
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { capituloA, capituloAV1, fetchDeFixtures, versiones } from "@/shared/testing";
import { PaginaCapitulo } from "./Capitulo";

const O = "/api/obras/obra-inventada";
const PALABRAS = "En realidad el faro era de piedra";

const capituloAV2 = {
  ...capituloAV1, id: "cap-a-v2", numero: 2, compartido: false,
  escenas: capituloAV1.escenas.map((e) => ({ ...e, capitulo: "cap-a-v2" })),
};
const capituloBV2 = { ...capituloAV2, id: "cap-b", compartido: true };

function montar(capitulo: string, datos: unknown, peticion: string | null) {
  const cliente = crearCliente(fetchDeFixtures({
    [`${O}/versiones`]: versiones,
    [`${O}/versiones/2/capitulos/${capitulo}`]: datos,
    [`${O}/versiones/2/peticion`]: { texto: peticion },
  }));
  render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={[`/obras/obra-inventada/versiones/2/capitulos/${capitulo}`]}>
        <Routes>
          <Route path="/obras/:obra/versiones/:numero/capitulos/:capitulo"
            element={<PaginaCapitulo />} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Capitulo de una version", () => {
  it("un capitulo cambiado dice que peticion lo cambio", async () => {
    montar("cap-a-v2", capituloAV2, PALABRAS);
    const aviso = await screen.findByTestId("por-tu-cambio");
    expect(aviso).toHaveTextContent(PALABRAS);
    expect(aviso.querySelector("a")?.getAttribute("href"))
      .toBe("/obras/obra-inventada/versiones/1/indice");
  });

  it("un capitulo compartido no lleva aviso", async () => {
    montar("cap-b", capituloBV2, PALABRAS);
    await screen.findAllByTestId("bloque-de-escena");
    expect(screen.queryByTestId("por-tu-cambio")).toBeNull();
  });

  it("una version sin peticion no lleva aviso", async () => {
    montar("cap-a-v2", capituloAV2, null);
    await screen.findAllByTestId("bloque-de-escena");
    expect(screen.queryByTestId("por-tu-cambio")).toBeNull();
  });

  it("el capitulo cambiado se lee sin estados: son de la administracion (SPEC-43)", async () => {
    montar("cap-a-v2", capituloAV2, PALABRAS);
    const bloques = await screen.findAllByTestId("bloque-de-escena");
    expect(bloques).toHaveLength(capituloA.escenas.length);
    expect(screen.queryByTestId("verificacion")).toBeNull();
    expect(screen.queryByTestId("estado-de-escena")).toBeNull();
  });
});
