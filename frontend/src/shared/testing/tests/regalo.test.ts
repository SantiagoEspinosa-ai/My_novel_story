// PLAN-33 (SPEC-22 NF-04): las fixtures de la novela regalo validan contra el congelado.
import Ajv2020 from "ajv/dist/2020";
import contrato from "../../../../../contrato/openapi.json";
import { FIXTURES_REGALO } from "../regalo";

describe("fixtures de la novela regalo", () => {
  it("cada una valida contra su esquema del congelado", () => {
    const ajv = new Ajv2020({ strict: false, allErrors: true });
    ajv.addSchema({ $id: "contrato", components: (contrato as { components: object }).components });
    for (const [nombre, { esquema, datos }] of Object.entries(FIXTURES_REGALO)) {
      const valida = ajv.compile({ $ref: `contrato#/components/schemas/${esquema}` });
      expect(valida(datos), `${nombre}: ${JSON.stringify(valida.errors)}`).toBe(true);
    }
  });
});
