// PLAN-33 E3 (SPEC-33 RF-05..RF-10): la entrevista como conversacion. Todo lo que se pinta
// sale del historial del backend; la pagina no calcula si se puede cerrar.
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import {
  confirmacionConUltima, fetchConMetodo, historialAbierto, historialCerrado, historialListo,
} from "@/shared/testing";
import { PaginaEntrevista } from "./Entrevista";

const E = "/api/entrevistas/ent-inventada";
const T = "/api/trabajos/trab-1";

function montar(rutas: Parameters<typeof fetchConMetodo>[0]) {
  const doble = fetchConMetodo(rutas);
  const utils = render(
    <ClienteProvider cliente={crearCliente(doble.fetch)}>
      <MemoryRouter initialEntries={["/entrevistas/ent-inventada"]}>
        <Routes>
          <Route path="/entrevistas/:entrevista"
            element={<PaginaEntrevista intervaloMs={10} />} />
          <Route path="/obras/:obra/generacion" element={<p>pagina de la generacion</p>} />
        </Routes>
      </MemoryRouter>
    </ClienteProvider>,
  );
  return { ...doble, ...utils };
}

async function responder(texto: string) {
  fireEvent.change(await screen.findByLabelText("Tu respuesta"), { target: { value: texto } });
  fireEvent.click(screen.getByRole("button", { name: "Responder" }));
}

const encolado = [{ estado: 202, cuerpo: { id_trabajo: "trab-1" } }];

describe("Entrevista", () => {
  it("las preguntas anteriores siguen visibles al llegar la nueva", async () => {
    const { pedidas } = montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }, { cuerpo: historialListo }],
      [`POST ${E}/turnos`]: encolado,
      [`GET ${T}`]: [{ cuerpo: { estado: "terminado", motivo: null } }],
    });
    await screen.findByText(historialAbierto.primera_pregunta);
    await responder("Nada más");
    await screen.findByText("Perfecto, ¿cerramos la ficha?");
    expect(screen.getByText(historialAbierto.primera_pregunta)).toBeInTheDocument();
    expect(screen.getByTestId("turno-1")).toBeInTheDocument();
    expect(screen.getByTestId("turno-3")).toBeInTheDocument();
    expect(pedidas.find((p) => p.clave === `POST ${E}/turnos`)?.cuerpo)
      .toEqual({ respuesta: "Nada más" });
  });

  it("al recargar reconstruye la conversación del historial", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }] });
    expect(await screen.findByTestId("turno-2")).toBeInTheDocument();
    expect(screen.getByTestId("turno-1")).toHaveTextContent(historialAbierto.turnos[0].respuesta);
  });

  it("mientras el turno está en curso lo dice", async () => {
    montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }],
      [`POST ${E}/turnos`]: encolado,
      [`GET ${T}`]: [{ cuerpo: { estado: "en_curso", motivo: null } }],
    });
    await responder("Se llama Nerea");
    expect(await screen.findByRole("status")).toHaveTextContent("El entrevistador está pensando");
    expect(screen.getByRole("button", { name: "Responder" })).toBeDisabled();
  });

  it("si el trabajo falla enseña su motivo y conserva la respuesta escrita", async () => {
    montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }],
      [`POST ${E}/turnos`]: encolado,
      [`GET ${T}`]: [{ cuerpo: {
        estado: "fallido", motivo: "el entrevistador no devolvio una ficha valida" } }],
    });
    await responder("Se llama Nerea");
    expect(await screen.findByRole("alert")).toHaveTextContent("no devolvio una ficha valida");
    expect(screen.getByLabelText("Tu respuesta")).toHaveValue("Se llama Nerea");
  });

  it("cerrar solo se ofrece con puede_cerrar", async () => {
    const { unmount } = montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }] });
    await screen.findByTestId("turno-1");
    expect(screen.queryByRole("button", { name: "Cerrar la ficha" })).toBeNull();
    unmount();
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialListo }] });
    expect(await screen.findByRole("button", { name: "Cerrar la ficha" })).toBeEnabled();
  });

  it("un 409 al cerrar enseña motivo, faltan y contradicciones tal como vienen", async () => {
    montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialListo }],
      [`POST ${E}/cerrar`]: [{ estado: 409, cuerpo: { detail: {
        motivo: "no se puede cerrar", faltan: ["dedicatoria"], avisos: [],
        contradicciones: [{ tipo: "edad_y_genero", descripcion: "el romance pide 12 años" }],
      } } }],
    });
    fireEvent.click(await screen.findByRole("button", { name: "Cerrar la ficha" }));
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("no se puede cerrar");
    expect(alerta).toHaveTextContent("dedicatoria");
    expect(alerta).toHaveTextContent("el romance pide 12 años");
  });

  it("confirmar un hecho propuesto lo pide al backend y vuelve a leer", async () => {
    const confirmado = { ...historialAbierto, hechos_propuestos: [
      { ...historialAbierto.hechos_propuestos[0], estado: "confirmado" as const }] };
    const { pedidas } = montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }, { cuerpo: confirmado }],
      [`POST ${E}/hechos/hp-1/confirmar`]: [{ cuerpo: {} }],
    });
    fireEvent.click(await screen.findByRole("button", { name: "Confirmar" }));
    await waitFor(() =>
      expect(screen.getByTestId("hecho-hp-1")).toHaveTextContent("confirmado"));
    expect(pedidas.map((p) => p.clave)).toContain(`POST ${E}/hechos/hp-1/confirmar`);
  });

  it("una entrevista cerrada ofrece escribir la novela y lleva a su generación", async () => {
    montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialCerrado }],
      ["GET /api/generaciones/gasto"]: [{ cuerpo: confirmacionConUltima }],
      [`POST /api/obras/${historialCerrado.obra}/generaciones`]: [
        { estado: 202, cuerpo: { id_trabajo: "trab-9", generacion: "gen-9" } }],
    });
    const boton = await screen.findByRole("button", { name: /Sí, escribir la novela/ });
    await waitFor(() => expect(boton).toBeEnabled());
    fireEvent.click(boton);
    expect(await screen.findByText("pagina de la generacion")).toBeInTheDocument();
  });

  it("una entrevista cerrada no ofrece responder y lo dice", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialCerrado }] });
    expect(await screen.findByText("La ficha está cerrada.")).toBeInTheDocument();
    expect(screen.queryByLabelText("Tu respuesta")).toBeNull();
  });
});
