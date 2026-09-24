// PLAN-22 E7 (VER-18): una escena nunca se pinta sin su estado y sus hallazgos abiertos
// (SPEC-22 RF-39), y la rendicion llega resuelta de la API (RF-40).
import { render, screen } from "@testing-library/react";
import {
  escenaConsolidada, escenaPlanificada, escenaRendida, escenaSinVeredicto,
} from "@/shared/testing";
import { EscenaConEstado } from "./EscenaConEstado";

describe("EscenaConEstado", () => {
  it("no pinta el texto si falta el estado o la lista de hallazgos", () => {
    const { estado: _e, ...sinEstado } = escenaConsolidada;
    const { hallazgos_abiertos: _h, ...sinHallazgos } = escenaConsolidada;
    for (const incompleta of [sinEstado, sinHallazgos]) {
      const { container, unmount } = render(
        <EscenaConEstado escena={incompleta as unknown as typeof escenaConsolidada} />,
      );
      expect(container.textContent).not.toContain("Primer texto");
      expect(screen.getByRole("alert")).toHaveTextContent(/sin su estado o sus hallazgos/);
      unmount();
    }
  });

  it("una rendida se ve distinta de una aceptada", () => {
    const aceptada = { ...escenaConsolidada, estado: "aceptada" as const };
    const { unmount } = render(<EscenaConEstado escena={aceptada} />);
    const limpia = screen.getByTestId("estado-de-escena");
    expect(limpia).toHaveTextContent("aceptada");
    expect(limpia).not.toHaveTextContent(/rendici/);
    expect(limpia).toHaveAttribute("data-rendida", "false");
    unmount();
    render(<EscenaConEstado escena={escenaRendida} />);
    const rendida = screen.getByTestId("estado-de-escena");
    expect(rendida).toHaveTextContent(/aceptada por rendici/);
    expect(rendida).toHaveAttribute("data-rendida", "true");
  });

  it("un sin_veredicto se pinta como sin veredicto y no como abierto", () => {
    render(<EscenaConEstado escena={escenaSinVeredicto} />);
    const h = screen.getByTestId("hallazgo");
    expect(h).toHaveTextContent("INV-27");
    expect(h).toHaveTextContent("sin veredicto");
    expect(h).not.toHaveTextContent(/\babierto\b/);
    expect(h).toHaveAttribute("data-estado", "sin_veredicto");
  });

  it("una escena sin texto pinta su estado y no un hueco", () => {
    const { container } = render(<EscenaConEstado escena={escenaPlanificada} />);
    expect(screen.getByTestId("estado-de-escena")).toHaveTextContent("planificada");
    expect(screen.getByTestId("texto-de-escena")).toHaveTextContent("sin texto todavía");
    expect(container.textContent).toContain("sin hallazgos abiertos");
  });

  it("un verde heredado no se pinta como verificado", () => {
    // PLAN-22 E17 (SPEC-22 RF-54): consolidada, y en esta version sin reverificar.
    const { unmount } = render(
      <EscenaConEstado escena={escenaConsolidada} verificacion="sin_reverificar" />);
    const v = screen.getByTestId("verificacion");
    expect(v).toHaveAttribute("data-verificacion", "sin_reverificar");
    expect(v).toHaveTextContent(/sin reverificar/);
    expect(v).not.toHaveTextContent(/^verificada/);
    unmount();
    render(<EscenaConEstado escena={escenaConsolidada} verificacion="verificada" />);
    expect(screen.getByTestId("verificacion")).toHaveTextContent(/^verificada/);
  });

  it("fuera de una version no se inventa un estado de verificacion", () => {
    render(<EscenaConEstado escena={escenaConsolidada} />);
    expect(screen.queryByTestId("verificacion")).toBeNull();
  });
});

