// PLAN-22 E6 (VER-106): los datos de prueba se derivan del congelado (SPEC-22 NF-04) y
// validan contra su esquema; y toda fixture que hable de capitulos trae al menos dos en
// una obra (NF-05, Regla 11).
import Ajv2020 from "ajv/dist/2020";
import contrato from "../../../../../contrato/openapi.json";
import { FIXTURES } from "../fixtures";

function validador() {
  const ajv = new Ajv2020({ strict: false, allErrors: true });
  ajv.addSchema({ $id: "contrato", components: (contrato as { components: object }).components });
  return (esquema: string) => ajv.compile({ $ref: `contrato#/components/schemas/${esquema}` });
}

describe("fixtures", () => {
  it("cada fixture valida contra su esquema del congelado", () => {
    const compilar = validador();
    expect(Object.keys(FIXTURES).length).toBeGreaterThan(0);
    for (const [nombre, { esquema, datos }] of Object.entries(FIXTURES)) {
      const valida = compilar(esquema);
      const ok = valida(datos);
      expect(ok, `${nombre}: ${JSON.stringify(valida.errors)}`).toBe(true);
    }
  });

  it("una fixture que no respeta el congelado no valida", () => {
    const valida = validador()("Indice");
    const { datos } = FIXTURES.indice;
    const roto = structuredClone(datos) as { capitulos: { estado: string }[] };
    roto.capitulos[0].estado = "terminado";
    expect(valida(roto)).toBe(false);
  });

  it("toda fixture con capitulos tiene al menos dos en una obra", () => {
    const conCapitulos = Object.entries(FIXTURES).filter(
      ([, f]) => typeof f.datos === "object" && f.datos !== null && "capitulos" in f.datos,
    );
    expect(conCapitulos.length).toBeGreaterThan(0);
    for (const [nombre, { datos }] of conCapitulos) {
      const capitulos = (datos as { capitulos: unknown[] }).capitulos;
      expect(capitulos.length, nombre).toBeGreaterThanOrEqual(2);
    }
  });
});
