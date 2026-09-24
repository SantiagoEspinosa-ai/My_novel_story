// PLAN-33 E12 (SPEC-33 RF-12, RF-13; vive en la pagina: steiger funde un slice con una sola referencia): lanzar gasta dinero, y la web pide una confirmacion
// explicita antes. Ensena tres cifras con su procedencia; el boton que gasta no esta hasta
// que han cargado, ni cuando lo gastado alcanza el techo. La regla la impone el backend.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  confirmacionConUltima, confirmacionEnElTecho, confirmacionVacia, fetchConMetodo,
} from "@/shared/testing";
import { ConfirmarGeneracion } from "./ConfirmarGeneracion";

const GASTO = "GET /api/generaciones/gasto";
const LANZAR = "POST /api/obras/obra-regalo-inventada/generaciones";

function montar(rutas: Parameters<typeof fetchConMetodo>[0], alLanzar = vi.fn()) {
  const doble = fetchConMetodo(rutas);
  render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <ConfirmarGeneracion obra="obra-regalo-inventada" alLanzar={alLanzar} />
    </ClienteProvider>,
  );
  return { ...doble, alLanzar };
}

const boton = () => screen.getByRole("button", { name: /Sí, escribir la novela/ });

describe("ConfirmarGeneracion", () => {
  it("el botón que gasta no está disponible hasta que las cifras han cargado", async () => {
    let soltar: (r: Response) => void = () => {};
    const fetch = (url: string) => url.endsWith("/gasto")
      ? new Promise<Response>((r) => { soltar = r; })
      : Promise.resolve(new Response("{}", { status: 404 }));
    render(
      <ClienteProvider cliente={crearCliente(fetch)}>
        <ConfirmarGeneracion obra="obra-regalo-inventada" alLanzar={() => {}} />
      </ClienteProvider>,
    );
    expect(boton()).toBeDisabled();
    soltar(new Response(JSON.stringify(confirmacionConUltima), { status: 200 }));
    await waitFor(() => expect(boton()).toBeEnabled());
  });

  it("enseña la referencia con su fuente", async () => {
    montar({ [GASTO]: [{ cuerpo: confirmacionConUltima }] });
    const r = await screen.findByTestId("referencia");
    expect(r).toHaveTextContent("16,89 USD");
    expect(r).toHaveTextContent("36 delegaciones");
    expect(r).toHaveTextContent("harness/evals/medidas.md");
  });

  it("lo gastado lleva la marca de suelo, y frente al techo", async () => {
    montar({ [GASTO]: [{ cuerpo: confirmacionConUltima }] });
    const g = await screen.findByTestId("gastado");
    expect(g).toHaveTextContent("17,40 USD");
    expect(g).toHaveTextContent("de 50 USD");
    expect(g).toHaveTextContent("como mínimo");
    expect(screen.getByTestId("ultima")).toHaveTextContent("16,95 USD");
    expect(screen.getByTestId("ultima")).toHaveTextContent("como mínimo");
  });

  it("sin generaciones previas dice sin medir", async () => {
    montar({ [GASTO]: [{ cuerpo: confirmacionVacia }] });
    expect(await screen.findByTestId("ultima")).toHaveTextContent("sin medir");
    expect(screen.getByTestId("gastado")).toHaveTextContent("sin medir");
    expect(screen.getByTestId("gastado")).not.toHaveTextContent("0,00");
  });

  it("en el techo el botón no está disponible y dice por qué", async () => {
    montar({ [GASTO]: [{ cuerpo: confirmacionEnElTecho }] });
    expect(await screen.findByRole("alert")).toHaveTextContent("alcanza el techo");
    expect(boton()).toBeDisabled();
  });

  it("lanzar pide la generación y avisa con su identificador", async () => {
    const { pedidas, alLanzar } = montar({
      [GASTO]: [{ cuerpo: confirmacionConUltima }],
      [LANZAR]: [{ estado: 202, cuerpo: { id_trabajo: "trab-1", generacion: "gen-nueva" } }],
    });
    await waitFor(() => expect(boton()).toBeEnabled());
    fireEvent.click(boton());
    await waitFor(() => expect(alLanzar).toHaveBeenCalledWith("gen-nueva"));
    expect(pedidas.filter((p) => p.clave === LANZAR)).toHaveLength(1);
  });

  it("un 409 al lanzar enseña su motivo", async () => {
    montar({
      [GASTO]: [{ cuerpo: confirmacionConUltima }],
      [LANZAR]: [{ estado: 409, cuerpo: { detail: "ya hay una generacion de la obra en curso" } }],
    });
    await waitFor(() => expect(boton()).toBeEnabled());
    fireEvent.click(boton());
    expect(await screen.findByRole("alert")).toHaveTextContent("ya hay una generacion");
  });
});
