// PLAN-22 E17 (VER-112, SPEC-22 RF-53): la version anterior se navega entera, desde el
// indice de la vigente hasta el texto de cada escena de la anterior. Compone las paginas,
// asi que vive en app/ (FSD: una pagina no importa otra).
import { fireEvent, render, screen, within } from "@testing-library/react";
import { crearCliente } from "@/shared/api";
import {
  capituloAV1, capituloB, fetchDeFixtures, indiceV1, indiceV2, versiones,
} from "@/shared/testing";
import { App } from "./App";

const OBRA = "/api/obras/obra-inventada";

describe("App", () => {
  it("la version anterior se navega entera", async () => {
    window.history.pushState({}, "", "/obras/obra-inventada/indice");
    const capituloBV1 = { ...capituloB, numero: 1, compartido: null,
      escenas: capituloB.escenas.map((e) => ({ ...e, estado_de_verificacion: "verificada" })) };
    render(<App cliente={crearCliente(fetchDeFixtures({
      [`${OBRA}/versiones`]: versiones,
      [`${OBRA}/versiones/2/indice`]: indiceV2,
      [`${OBRA}/versiones/1/indice`]: indiceV1,
      [`${OBRA}/versiones/1/capitulos/cap-b`]: capituloBV1,
      [`${OBRA}/versiones/1/capitulos/cap-a`]: capituloAV1,
    }))} />);
    fireEvent.click(await screen.findByRole("link", { name: /Versión 1/ }));
    for (const [n, capitulo] of [[0, capituloBV1], [1, capituloAV1]] as const) {
      const enlaces = await screen.findAllByRole("link", { name: /^Capítulo \d+$/ });
      fireEvent.click(enlaces[n]);
      const bloques = await screen.findAllByTestId("bloque-de-escena");
      expect(bloques.map((b) => b.getAttribute("data-escena")))
        .toEqual(capitulo.escenas.map((e) => e.id));
      for (const b of bloques) {
        expect(within(b).getByTestId("verificacion")).toBeInTheDocument();
        // Una version que no es la vigente se lee, pero no se pide sobre ella.
        expect(within(b).queryByRole("button", { name: /Pedir un cambio/ })).toBeNull();
      }
      expect(screen.getByText(/Estás leyendo la versión 1/)).toBeInTheDocument();
      fireEvent.click(screen.getByRole("link", { name: /Índice · versión 1/ }));
    }
  });
});
