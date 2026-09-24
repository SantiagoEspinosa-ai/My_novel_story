// PLAN-22 E7: un dato nulo se dice «sin dato», y no se confunde con una lista vacia.
import { render, screen } from "@testing-library/react";
import { SinDato } from "./SinDato";

describe("SinDato", () => {
  it("pinta sin dato si el valor es nulo", () => {
    render(<SinDato valor={null}>{(v: string) => v}</SinDato>);
    expect(screen.getByText("sin dato")).toBeInTheDocument();
  });

  it("distingue una lista vacia de un valor nulo", () => {
    const { container } = render(<SinDato valor={[]}>{(v: string[]) => v.join(",")}</SinDato>);
    expect(container.textContent).toBe("ninguno");
    expect(container.textContent).not.toContain("sin dato");
  });

  it("un cero es un dato y se pinta", () => {
    const { container } = render(<SinDato valor={0}>{(v: number) => String(v)}</SinDato>);
    expect(container.textContent).toBe("0");
  });

  it("el texto de la ausencia se puede nombrar", () => {
    render(<SinDato valor={null} ausente="no declarado">{() => "x"}</SinDato>);
    expect(screen.getByText("no declarado")).toBeInTheDocument();
  });
});
