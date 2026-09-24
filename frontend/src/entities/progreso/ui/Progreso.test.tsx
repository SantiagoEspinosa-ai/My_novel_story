// PLAN-22 E13c (SPEC-22 RF-60): en que punto va una generacion, refrescado solo. Lo que
// se pinta es lo que calcula el servidor: la fase, el capitulo sobre el total y los
// segundos desde la ultima actividad.
import { act, render, screen } from "@testing-library/react";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { UMBRAL_SIN_ACTIVIDAD_SEGUNDOS } from "@/shared/config";
import { fetchDeFixtures, progresoEscribiendo } from "@/shared/testing";
import { Progreso } from "./Progreso";

const RUTA = "/api/obras/obra-inventada/progreso";

function montar(respuestas: unknown[]) {
  let n = 0;
  const pedidas: string[] = [];
  const fetch = async (url: string) => {
    pedidas.push(url);
    const r = respuestas[Math.min(n++, respuestas.length - 1)];
    return fetchDeFixtures(r === null ? {} : { [RUTA]: r })(url);
  };
  render(
    <ClienteProvider cliente={crearCliente(fetch)}>
      <Progreso obra="obra-inventada" intervaloMs={1000} />
    </ClienteProvider>,
  );
  return pedidas;
}

describe("Progreso", () => {
  it("enseña la fase y el capitulo sobre el total", async () => {
    montar([progresoEscribiendo]);
    const barra = await screen.findByTestId("progreso");
    expect(barra).toHaveTextContent("escribiendo");
    expect(barra).toHaveTextContent("capítulo 3 de 10");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "3");
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuemax", "10");
    expect(barra).not.toHaveTextContent("sin actividad");
  });

  it("marca sin actividad pasado el umbral", async () => {
    const parado = { ...progresoEscribiendo,
      segundos_desde_la_ultima_actividad: UMBRAL_SIN_ACTIVIDAD_SEGUNDOS + 60 * 7 };
    montar([parado]);
    const barra = await screen.findByTestId("progreso");
    const minutos = Math.floor(parado.segundos_desde_la_ultima_actividad / 60);
    expect(barra).toHaveTextContent(`sin actividad desde hace ${minutos} min`);
  });

  it("se refresca sola", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      const siguiente = { ...progresoEscribiendo, capitulo: 4 };
      const pedidas = montar([progresoEscribiendo, siguiente]);
      expect(await screen.findByTestId("progreso")).toHaveTextContent("capítulo 3 de 10");
      await act(async () => { await vi.advanceTimersByTimeAsync(1100); });
      expect(await screen.findByText(/capítulo 4 de 10/)).toBeInTheDocument();
      expect(pedidas.length).toBeGreaterThanOrEqual(2);
    } finally {
      vi.useRealTimers();
    }
  });

  it("sin generacion no pinta nada, y no inventa una fase", async () => {
    const pedidas = montar([null]);
    await act(async () => { await Promise.resolve(); });
    await vi.waitFor(() => expect(pedidas.length).toBeGreaterThan(0));
    expect(screen.queryByTestId("progreso")).toBeNull();
  });
});
