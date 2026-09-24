// PLAN-33 E8 (SPEC-33 RF-19, RF-20): el contador discreto. Sube con la respuesta; lo que no
// se midio dice «sin medir», y un total con huecos se marca como suelo junto a la cifra.
import { render, screen } from "@testing-library/react";
import { generacionConSuelo, generacionEnCurso, generacionSinMedir } from "@/shared/testing";
import { CosteEnVivo } from "./CosteEnVivo";

describe("CosteEnVivo", () => {
  it("sube cuando la respuesta trae más gasto", () => {
    const { rerender } = render(<CosteEnVivo coste={generacionEnCurso.coste} />);
    expect(screen.getByTestId("coste")).toHaveTextContent("1,25 USD");
    expect(screen.getByTestId("coste")).toHaveTextContent("7 delegaciones");
    rerender(<CosteEnVivo coste={{ ...generacionEnCurso.coste!, usd: 1.75, delegaciones: 8 }} />);
    expect(screen.getByTestId("coste")).toHaveTextContent("1,75 USD");
    expect(screen.getByTestId("coste")).toHaveTextContent("8 delegaciones");
  });

  it("con una delegación sin coste marca el total como suelo junto a la cifra", () => {
    render(<CosteEnVivo coste={generacionConSuelo.coste} />);
    const c = screen.getByTestId("coste");
    expect(c).toHaveTextContent("1,50 USD");
    expect(c).toHaveTextContent("como mínimo: 1 sin coste medido");
  });

  it("sin ninguna medida dice sin medir, nunca 0,00", () => {
    render(<CosteEnVivo coste={generacionSinMedir.coste} />);
    const c = screen.getByTestId("coste");
    expect(c).toHaveTextContent("sin medir");
    expect(c).not.toHaveTextContent("0,00");
  });

  it("sin generación anotada tampoco pinta un cero", () => {
    render(<CosteEnVivo coste={null} />);
    expect(screen.getByTestId("coste")).toHaveTextContent("coste sin medir");
    expect(screen.getByTestId("coste")).not.toHaveTextContent("0,00");
  });
});
