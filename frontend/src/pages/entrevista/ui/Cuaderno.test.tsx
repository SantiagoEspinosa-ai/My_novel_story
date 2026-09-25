// PLAN-35 F4 y F5 (SPEC-35 RF-04..RF-07, SPEC-34 RF-01): la entrevista con Xime, el cuaderno y
// el cuaderno completo. Lo que se sabe, lo que falta y los nombres llegan resueltos del
// backend: la pagina no cuenta ni traduce. Datos inventados.
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { ClienteProvider, crearCliente } from "@/shared/api";
import { ENTREVISTADORA } from "@/shared/config";
import {
  confirmacionConUltima, fetchConMetodo, historialAbierto, historialCerrado, historialConNombre,
  historialListo, historialNuevo,
} from "@/shared/testing";
import { PaginaEntrevista } from "./Entrevista";

const E = "/api/entrevistas/ent-inventada";

function montar(rutas: Parameters<typeof fetchConMetodo>[0]) {
  const doble = fetchConMetodo(rutas);
  render(
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
  return doble;
}

describe("Entrevista con Xime", () => {
  it("la primera respuesta es el nombre y va al campo de nombres", async () => {
    const { pedidas } = montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialNuevo }, { cuerpo: historialConNombre }],
      [`PUT ${E}/nombres`]: [{ cuerpo: {} }],
    });
    expect(screen.queryByLabelText("Tu respuesta")).toBeNull();
    fireEvent.change(await screen.findByLabelText(/Su nombre/),
      { target: { value: "Nerea Salgado" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar el nombre" }));
    await screen.findByText(/¿Cuántos años tiene Nerea\?/);
    const put = pedidas.find((p) => p.clave === `PUT ${E}/nombres`);
    expect(put?.cuerpo).toMatchObject({ destinatario: "Nerea Salgado" });
    expect(pedidas.map((p) => p.clave)).not.toContain(`POST ${E}/turnos`);
    expect(await screen.findByLabelText("Tu respuesta")).toBeInTheDocument();
  });

  it("un turno contestado en el cuaderno se ve como tal", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialConNombre }] });
    expect(await screen.findByTestId("turno-1")).toHaveTextContent("escrito en el cuaderno");
  });

  it("cada pregunta la firma Xime, con el nombre de la configuración", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }] });
    const turno = await screen.findByTestId("turno-2");
    expect(within(turno).getByText(ENTREVISTADORA.nombre)).toBeInTheDocument();
    expect(screen.getAllByText(ENTREVISTADORA.nombre).length).toBeGreaterThan(2);
  });

  it("el cuaderno enseña lo sabido y lo que falta tal como llega", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }] });
    const c = await screen.findByTestId("cuaderno");
    expect(c).toHaveTextContent("Faltan 8 de 11");
    expect(c).toHaveTextContent("cumpleaños");
    expect(c).toHaveTextContent("41 años");
    expect(within(screen.getByTestId("cuaderno-falta")).getAllByRole("listitem")).toHaveLength(8);
  });

  it("el cuaderno enseña los nombres reales", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }] });
    const n = await screen.findByTestId("cuaderno-nombres");
    expect(n).toHaveTextContent("Nerea Salgado");
    expect(n).toHaveTextContent("Nora");
    expect(n).toHaveTextContent("su perra");
    expect(n).toHaveTextContent("Tomás");
    expect(n).toHaveTextContent("Nora Quintana");
  });

  it("añadir una mascota manda los nombres completos", async () => {
    const { pedidas } = montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }],
      [`PUT ${E}/nombres`]: [{ cuerpo: {} }],
    });
    const n = await screen.findByTestId("cuaderno-nombres");
    fireEvent.change(within(n).getByLabelText("Nombre"), { target: { value: "Pipa" } });
    fireEvent.change(within(n).getByLabelText("Es"), { target: { value: "mascota" } });
    fireEvent.change(within(n).getByLabelText("Relación"), { target: { value: "su gata" } });
    fireEvent.click(within(n).getByRole("button", { name: "Añadir" }));
    await waitFor(() => expect(pedidas.map((p) => p.clave)).toContain(`PUT ${E}/nombres`));
    expect(pedidas.find((p) => p.clave === `PUT ${E}/nombres`)?.cuerpo).toEqual({
      destinatario: "Nerea Salgado", regalado_por: "Tomás",
      otros: [{ nombre: "Nora", tipo: "mascota", relacion: "su perra" },
        { nombre: "Pipa", tipo: "mascota", relacion: "su gata" }],
      vetados: ["Nora Quintana"],
    });
  });

  it("vetar un nombre manda la lista con él", async () => {
    const { pedidas } = montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }],
      [`PUT ${E}/nombres`]: [{ cuerpo: {} }],
    });
    const n = await screen.findByTestId("cuaderno-nombres");
    fireEvent.change(within(n).getByLabelText("Nombre que no debe aparecer"),
      { target: { value: "Leo Barrios" } });
    fireEvent.click(within(n).getByRole("button", { name: "Vetar" }));
    await waitFor(() => expect(pedidas.map((p) => p.clave)).toContain(`PUT ${E}/nombres`));
    expect((pedidas.find((p) => p.clave === `PUT ${E}/nombres`)?.cuerpo as { vetados: string[] })
      .vetados).toEqual(["Nora Quintana", "Leo Barrios"]);
  });

  it("un aviso de nombre se confirma desde el cuaderno", async () => {
    const { pedidas } = montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialAbierto }],
      [`POST ${E}/avisos/confirmar`]: [{ cuerpo: {} }],
    });
    const n = await screen.findByTestId("cuaderno-nombres");
    expect(n).toHaveTextContent("comparte nombre de pila");
    fireEvent.click(within(n).getByRole("button", { name: "Entendido" }));
    await waitFor(() => expect(pedidas.find((p) => p.clave === `POST ${E}/avisos/confirmar`)
      ?.cuerpo).toEqual({ vetado: "Nora Quintana" }));
  });
});

describe("CuadernoCompleto", () => {
  it("con puede_cerrar enseña la propuesta y el aviso de que cerrar no tiene vuelta atrás",
    async () => {
      montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialListo }] });
      const c = await screen.findByTestId("cuaderno-completo");
      expect(c).toHaveTextContent("El faro de Nerea");
      expect(c).toHaveTextContent("Un faro de papel devuelve a Nerea al mar.");
      expect(c).toHaveTextContent("Para Nerea, que siempre vuelve.");
      expect(c).toHaveTextContent(/no tiene vuelta atrás/);
      expect(within(c).getByRole("button", { name: "Cerrar la ficha" })).toBeEnabled();
      expect(screen.queryByLabelText("Tu respuesta")).toBeNull();
    });

  it("quiero cambiar algo vuelve a la conversación", async () => {
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: historialListo }] });
    fireEvent.click(await screen.findByRole("button", { name: "Quiero cambiar algo" }));
    expect(await screen.findByLabelText("Tu respuesta")).toBeInTheDocument();
    expect(screen.queryByTestId("cuaderno-completo")).toBeNull();
  });

  it("sin dedicatoria lo dice y no se inventa una", async () => {
    const sin = { ...historialListo, cuaderno: { ...historialListo.cuaderno,
      propuesta: { ...historialListo.cuaderno.propuesta, dedicatoria: null } } };
    montar({ [`GET ${E}/turnos`]: [{ cuerpo: sin }] });
    expect(await screen.findByTestId("cuaderno-completo")).toHaveTextContent("sin dedicatoria");
  });

  it("cerrada, viene la confirmación de gasto sin quitarle nada", async () => {
    montar({
      [`GET ${E}/turnos`]: [{ cuerpo: historialCerrado }],
      ["GET /api/generaciones/gasto"]: [{ cuerpo: confirmacionConUltima }],
    });
    expect(await screen.findByTestId("ultima")).toBeInTheDocument();
    expect(screen.getByTestId("referencia")).toBeInTheDocument();
    expect(screen.getByTestId("gastado")).toBeInTheDocument();
  });
});
