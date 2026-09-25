// PLAN-22 E16 (VER-111): pedir un cambio desde la pagina (SPEC-22 RF-47, RF-49..RF-51,
// RF-55). Lo que viaja es el hecho o el personaje elegido y las palabras del lector, nunca
// una lista de capitulos que decida la interfaz (RF-50). Antes de confirmar se enseñan los
// capitulos que se tocarian, con la promesa y su punto ciego tal como llegan (SPEC-23 D-3).
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  escenaConsolidada, fetchConMetodos, fichas, hechosDeB1, indice, propuestaConSalida,
  propuestaSinSalida, trabajoEnCola, trabajoFallido,
} from "@/shared/testing";
import { PedirCambio } from "./PedirCambio";

const OBRA = "/api/obras/obra-inventada";
const RUTAS_BASE = {
  "/api/escenas/esc-b1/hechos": hechosDeB1,
  [`${OBRA}/fichas`]: fichas,
  [`${OBRA}/indice`]: indice,
};

function montar(rutas: Record<string, unknown> = {}) {
  const falso = fetchConMetodos({
    ...RUTAS_BASE,
    [`POST ${OBRA}/cambios/propuesta`]: propuestaConSalida,
    [`POST ${OBRA}/cambios`]: { estado: 202, cuerpo: { id_trabajo: "trab-1" } },
    "/api/trabajos/trab-1": [{ estado: 200, cuerpo: trabajoEnCola },
      { estado: 200, cuerpo: trabajoFallido }],
    ...rutas,
  });
  render(
    <ClienteProvider cliente={crearCliente(falso.fetch)}>
      <MemoryRouter>
        <PedirCambio obra="obra-inventada" escena={escenaConsolidada}
          fragmento="con dos espacios" intervaloMs={1000} />
      </MemoryRouter>
    </ClienteProvider>,
  );
  return falso.llamadas;
}

async function elegirHechoYEscribir() {
  fireEvent.click(await screen.findByLabelText(/El faro existe \(inventado\)\./));
  fireEvent.change(screen.getByLabelText(/Cómo debería ser/), {
    target: { value: "El faro es de piedra (inventado)." } });
  fireEvent.change(screen.getByLabelText(/Con tus palabras/), {
    target: { value: "Quiero que el faro sea de piedra." } });
}

const posts = (llamadas: { metodo: string; url: string; cuerpo: unknown }[], sufijo: string) =>
  llamadas.filter((l) => l.metodo === "POST" && l.url.endsWith(sufijo));

describe("PedirCambio", () => {
  it("ofrece el fragmento, los hechos de la escena y sus presentes con su nombre", async () => {
    montar();
    expect(await screen.findByText(/con dos espacios/)).toBeInTheDocument();
    expect(await screen.findByLabelText(/La llave abre el faro/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Un nombre/ }));
    expect(await screen.findByLabelText(/Nombre inventado/)).toBeInTheDocument();
    expect(screen.getByLabelText(/per-dos/)).toBeInTheDocument();
  });

  it("manda el hecho elegido y el texto del lector, y ningun capitulo", async () => {
    const llamadas = montar();
    await elegirHechoYEscribir();
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    await screen.findByTestId("propuesta");
    const [propuesta] = posts(llamadas, "/cambios/propuesta");
    expect(propuesta.cuerpo).toEqual({
      clase: "hecho", hecho: "hec-faro", enunciado_nuevo: "El faro es de piedra (inventado).",
      texto: "Quiero que el faro sea de piedra." });
    // Al confirmar, la lista es **la que dio el backend**, no una elegida aqui.
    fireEvent.click(screen.getByRole("button", { name: /Confirmar el cambio/ }));
    await screen.findByTestId("seguimiento");
    const [cambio] = posts(llamadas, "/cambios");
    expect(cambio.cuerpo).toMatchObject({
      clase: "hecho", hecho: "hec-faro", texto: "Quiero que el faro sea de piedra.",
      capitulos_propuestos: propuestaConSalida.capitulos_propuestos,
      version_de_partida: propuestaConSalida.version_de_partida });
  });

  it("renombrar manda el personaje y el nombre nuevo", async () => {
    const llamadas = montar();
    fireEvent.click(await screen.findByRole("tab", { name: /Un nombre/ }));
    fireEvent.click(await screen.findByLabelText(/Nombre inventado/));
    fireEvent.change(screen.getByLabelText(/Nombre nuevo/), { target: { value: "Nala" } });
    fireEvent.change(screen.getByLabelText(/Con tus palabras/), {
      target: { value: "Se llama Nala." } });
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    await screen.findByTestId("propuesta");
    expect(posts(llamadas, "/cambios/propuesta")[0].cuerpo).toEqual({
      clase: "nombre", personaje: "per-uno", nombre_nuevo: "Nala", texto: "Se llama Nala." });
  });

  it("no ofrece confirmar hasta haber enseñado los capitulos", async () => {
    montar();
    await elegirHechoYEscribir();
    expect(screen.queryByRole("button", { name: /Confirmar el cambio/ })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    const propuesta = await screen.findByTestId("propuesta");
    const tocados = within(propuesta).getAllByTestId("capitulo-que-se-toca");
    expect(tocados.map((c) => c.getAttribute("data-capitulo"))).toEqual(["cap-b", "cap-a"]);
    // PLAN-35 E6: cada capitulo tocado lleva ademas la marca «se reescribe» (texto, no solo
    // color); lo que se comprueba sigue siendo el nombre de cada uno, en su orden.
    expect(tocados.map((c) => c.querySelector(".balda__titulo")?.textContent))
      .toEqual(["Capítulo 1", "Capítulo 2"]);
    expect(screen.getByRole("button", { name: /Confirmar el cambio/ })).toBeInTheDocument();
  });

  // PLAN-35 E6 (SPEC-35 RF-09): la propuesta se pinta como una balda con los capitulos de la
  // obra en su orden, y solo los que el backend propone van resaltados.
  it("la balda resalta solo los capitulos propuestos", async () => {
    montar({ [`POST ${OBRA}/cambios/propuesta`]: {
      ...propuestaConSalida, capitulos_propuestos: ["cap-a"] } });
    await elegirHechoYEscribir();
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    const balda = await screen.findByTestId("balda");
    const lomos = within(balda).getAllByRole("listitem");
    expect(lomos.map((l) => l.getAttribute("data-capitulo"))).toEqual(["cap-b", "cap-a"]);
    expect(lomos.map((l) => l.getAttribute("data-testid")))
      .toEqual(["capitulo-que-no-se-toca", "capitulo-que-se-toca"]);
    expect(within(balda).getByTestId("capitulo-que-se-toca")).toHaveTextContent("se reescribe");
  });

  it("la promesa sale con su punto ciego", async () => {
    montar();
    await elegirHechoYEscribir();
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    const propuesta = await screen.findByTestId("propuesta");
    expect(within(propuesta).getByTestId("promesa")).toHaveTextContent(propuestaConSalida.promesa);
    expect(within(propuesta).getByTestId("punto-ciego"))
      .toHaveTextContent(propuestaConSalida.punto_ciego);
  });

  it("sin salida elegida no ofrece confirmar y dice el motivo del backend", async () => {
    montar({ [`POST ${OBRA}/cambios/propuesta`]: propuestaSinSalida });
    await elegirHechoYEscribir();
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    const propuesta = await screen.findByTestId("propuesta");
    expect(propuesta).toHaveTextContent("salida sin elegir: falta la medida");
    expect(within(propuesta).getByTestId("punto-ciego")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Confirmar el cambio/ })).toBeNull();
  });

  it("un 409 enseña el motivo que da el backend", async () => {
    montar({ [`POST ${OBRA}/cambios`]: { estado: 409,
      cuerpo: { detail: "salida sin elegir: falta la medida" } } });
    await elegirHechoYEscribir();
    fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
    fireEvent.click(await screen.findByRole("button", { name: /Confirmar el cambio/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "salida sin elegir: falta la medida");
    expect(screen.queryByTestId("seguimiento")).toBeNull();
  });

  it("sigue el trabajo y, si falla, el lector ve un mensaje que se entiende y no el motivo técnico (SPEC-45)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const llamadas = montar();
      await elegirHechoYEscribir();
      fireEvent.click(screen.getByRole("button", { name: /Ver qué capítulos se tocarían/ }));
      fireEvent.click(await screen.findByRole("button", { name: /Confirmar el cambio/ }));
      const seguimiento = await screen.findByTestId("seguimiento");
      expect(await within(seguimiento).findByText("en cola")).toBeInTheDocument();
      await act(async () => { await vi.advanceTimersByTimeAsync(1100); });
      expect(await within(seguimiento).findByText("fallido")).toBeInTheDocument();
      expect(seguimiento).not.toHaveTextContent(trabajoFallido.motivo!);
      expect(seguimiento).toHaveTextContent("No se pudo aplicar tu cambio");
      expect(seguimiento).toHaveTextContent("La novela sigue como estaba");
      const antes = llamadas.filter((l) => l.url === "/api/trabajos/trab-1").length;
      await act(async () => { await vi.advanceTimersByTimeAsync(3000); });
      // Un trabajo que termino, bien o mal, no se sigue pidiendo.
      expect(llamadas.filter((l) => l.url === "/api/trabajos/trab-1").length).toBe(antes);
    } finally {
      vi.useRealTimers();
    }
  });
});
