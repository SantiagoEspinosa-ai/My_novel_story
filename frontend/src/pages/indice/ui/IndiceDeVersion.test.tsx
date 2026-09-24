// PLAN-22 E17 (VER-112): las marcas de cambio y la version anterior (SPEC-22 RF-52..RF-54).
// «Cambio» lo dice el backend capitulo a capitulo: la interfaz pinta `compartido` tal como
// llega y no compara textos. La version anterior se navega entera.
import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { fetchDeFixtures, indiceV1, indiceV2, versiones } from "@/shared/testing";
import { PaginaIndice } from "./Indice";

const OBRA = "/api/obras/obra-inventada";

function montar(rutas: Record<string, unknown>, entrada = "/obras/obra-inventada/indice") {
  const cliente = crearCliente(fetchDeFixtures({
    [`${OBRA}/versiones`]: versiones,
    [`${OBRA}/versiones/2/indice`]: indiceV2,
    [`${OBRA}/versiones/1/indice`]: indiceV1,
    ...rutas,
  }));
  return render(
    <ClienteProvider cliente={cliente}>
      <MemoryRouter initialEntries={[entrada]}>
        <Routes>
          <Route path="/obras/:obra/indice" element={<PaginaIndice />} />
          <Route path="/obras/:obra/versiones/:numero/indice" element={<PaginaIndice />} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
}

describe("Indice", () => {
  it("marca como cambiados exactamente los capitulos que marca la respuesta, sin comparar textos", async () => {
    // Marcas que ningun texto justificaria: el 1 «cambio» y el 2 no. Si la interfaz
    // comparara algo, no saldria asi.
    const raro = structuredClone(indiceV2);
    raro.capitulos[0].compartido = false;
    raro.capitulos[1].compartido = true;
    montar({ [`${OBRA}/versiones/2/indice`]: raro });
    const caps = await screen.findAllByTestId("capitulo-del-indice");
    expect(caps.map((c) => c.getAttribute("data-cambio"))).toEqual(["true", "false"]);
    expect(within(caps[0]).getByText("cambió en esta versión")).toBeInTheDocument();
    expect(within(caps[1]).queryByText("cambió en esta versión")).toBeNull();
  });

  it("sin anterior no marca nada", async () => {
    montar({}, "/obras/obra-inventada/versiones/1/indice");
    const caps = await screen.findAllByTestId("capitulo-del-indice");
    expect(caps.map((c) => c.getAttribute("data-cambio"))).toEqual(["sin-anterior", "sin-anterior"]);
    expect(screen.queryByText("cambió en esta versión")).toBeNull();
  });

  it("la version anterior se navega entera", async () => {
    montar({});
    // La vigente es la 2, y se dice.
    expect(await screen.findByTestId("version-actual")).toHaveTextContent("Versión 2");
    fireEvent.click(screen.getByRole("link", { name: /Versión 1/ }));
    expect(await screen.findByText(/Estás leyendo la versión 1/)).toBeInTheDocument();
    const caps = await screen.findAllByTestId("capitulo-del-indice");
    expect(caps.map((c) => c.getAttribute("data-capitulo"))).toEqual(["cap-b", "cap-a"]);
    const enlaces = screen.getAllByRole("link", { name: /^Capítulo \d+$/ });
    expect(enlaces.map((a) => a.getAttribute("href"))).toEqual([
      "/obras/obra-inventada/versiones/1/capitulos/cap-b",
      "/obras/obra-inventada/versiones/1/capitulos/cap-a",
    ]);
    // Que cada capitulo de la 1 se lee entero lo comprueba App.test.tsx, que compone las
    // dos paginas (FSD no deja que una pagina importe otra).
  });

  it("cada escena de una version lleva su estado de verificacion", async () => {
    montar({});
    const escenas = await screen.findAllByTestId("escena-del-indice");
    expect(escenas.map((e) => within(e).getByTestId("verificacion")
      .getAttribute("data-verificacion"))).toEqual(["sin_reverificar", "sin_reverificar", "verificada"]);
  });
});
