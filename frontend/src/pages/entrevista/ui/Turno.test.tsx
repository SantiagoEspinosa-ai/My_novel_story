// PLAN-33 E2 (vive en la pagina: steiger pide fundir un slice con una sola referencia) (SPEC-33 RF-05, RF-06): un turno de la conversacion. Lo que el codigo dijo en
// ese turno -lo que falta, los avisos, las contradicciones- se ve dentro del turno, no en
// un panel aparte.
import { render, screen, within } from "@testing-library/react";
import { turnoConAviso, turnoSinNada, turnoViejo } from "@/shared/testing";
import { Turno } from "./Turno";

describe("Turno", () => {
  it("enseña los avisos y las contradicciones dentro del turno", () => {
    render(<Turno turno={turnoConAviso} />);
    const t = screen.getByTestId("turno-1");
    expect(t).toHaveTextContent(turnoConAviso.respuesta);
    expect(t).toHaveTextContent(turnoConAviso.pregunta);
    const notas = within(t).getByTestId("observaciones");
    expect(notas).toHaveTextContent(turnoConAviso.avisos![0]);
    expect(notas).toHaveTextContent(turnoConAviso.contradicciones_abiertas![0].descripcion);
    expect(notas).toHaveTextContent("falta: " + turnoConAviso.falta![0]);
  });

  it("sin avisos no pinta un panel vacío", () => {
    render(<Turno turno={turnoSinNada} />);
    expect(screen.queryByTestId("observaciones")).toBeNull();
  });

  it("cada aviso lleva texto, no solo color", () => {
    render(<Turno turno={turnoConAviso} />);
    const notas = screen.getByTestId("observaciones");
    expect(within(notas).getByText("aviso")).toBeInTheDocument();
    expect(within(notas).getByText("contradicción")).toBeInTheDocument();
  });

  it("un turno de antes de guardar sus avisos lo dice, en vez de callarse", () => {
    render(<Turno turno={turnoViejo} />);
    expect(screen.getByTestId("turno-1")).toHaveTextContent("avisos de este turno no guardados");
  });
});
