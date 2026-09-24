// PLAN-22 E6b (SPEC-22 RF-59): la identidad visual vive en un solo sitio. Cambiar la paleta
// es cambiar src/shared/ui/tema/, y ningun otro fichero de src escribe un color.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import contrato from "../../../../../contrato/openapi.json";
import { contraste } from "./contraste";
import {
  COLORES, ESTADO_DE_ESCENA, ESTADO_DE_HALLAZGO, FASE_DE_GENERACION, SEVERIDAD,
} from "./tokens";

const SRC = join(process.cwd(), "src");
const TEMA = join("shared", "ui", "tema");
const COLOR_LITERAL = /#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab|lab|lch|hwb)\s*\(/;
const COLOR_CON_NOMBRE = /(?:color|background|border|fill|stroke)[\w-]*\s*:\s*["']?(?:white|black|red|green|blue|gray|grey|orange|yellow|purple|pink|brown|navy|teal)\b/i;

function ficheros(dir: string): string[] {
  return readdirSync(dir).flatMap((n: string) => {
    const r = join(dir, n);
    return statSync(r).isDirectory() ? ficheros(r) : [r];
  });
}

const enumDe = (nombre: string) =>
  (contrato as { components: { schemas: Record<string, { enum?: string[] }> } })
    .components.schemas[nombre].enum!;

describe("tema", () => {
  it("ningun fichero de src fuera de shared/ui/tema escribe un color literal", () => {
    const culpables = ficheros(SRC)
      .filter((f) => /\.(ts|tsx|css)$/.test(f) && !/\.test\.tsx?$/.test(f))
      .filter((f) => !relative(SRC, f).startsWith(TEMA + sep))
      .filter((f) => {
        const t = readFileSync(f, "utf-8");
        return COLOR_LITERAL.test(t) || COLOR_CON_NOMBRE.test(t);
      })
      .map((f) => relative(SRC, f));
    expect(culpables).toEqual([]);
  });

  it("cada estado de escena tiene su color y su etiqueta de texto", () => {
    for (const [vocabulario, mapa] of [
      ["EstadoDeEscena", ESTADO_DE_ESCENA], ["EstadoDeHallazgo", ESTADO_DE_HALLAZGO],
      ["Severidad", SEVERIDAD], ["FaseDeGeneracion", FASE_DE_GENERACION],
    ] as const) {
      const literales = enumDe(vocabulario);
      expect(Object.keys(mapa).sort(), vocabulario).toEqual([...literales].sort());
      for (const l of literales) {
        const t = (mapa as Record<string, { etiqueta: string; fondo: string; texto: string }>)[l];
        expect(t.etiqueta.trim().length, `${vocabulario}.${l}`).toBeGreaterThan(0);
        expect(t.fondo).toMatch(/^#[0-9a-f]{6}$/i);
        expect(t.texto).toMatch(/^#[0-9a-f]{6}$/i);
      }
    }
    // Una rendida no se confunde con una aceptada ni por el color ni por el texto.
    expect(ESTADO_DE_ESCENA.aceptada_por_rendicion.fondo).not.toBe(ESTADO_DE_ESCENA.aceptada.fondo);
    expect(ESTADO_DE_ESCENA.aceptada_por_rendicion.etiqueta).not.toBe(ESTADO_DE_ESCENA.aceptada.etiqueta);
  });

  it("los tokens tienen contraste suficiente entre texto y fondo", () => {
    const pares: [string, string, string][] = [
      ["texto sobre fondo", COLORES.texto, COLORES.fondo],
      ["texto sobre superficie", COLORES.texto, COLORES.superficie],
      ["texto suave sobre superficie", COLORES.textoSuave, COLORES.superficie],
      ["texto sobre acento", COLORES.sobreAcento, COLORES.acento],
      ["enlace sobre fondo", COLORES.enlace, COLORES.fondo],
      ...[ESTADO_DE_ESCENA, ESTADO_DE_HALLAZGO, SEVERIDAD, FASE_DE_GENERACION].flatMap((m) =>
        Object.entries(m).map(([k, v]) => [k, v.texto, v.fondo] as [string, string, string])),
    ];
    for (const [nombre, texto, fondo] of pares) {
      expect(contraste(texto, fondo), nombre).toBeGreaterThanOrEqual(4.5);
    }
  });

  it("el contraste se calcula como WCAG", () => {
    expect(contraste("#000000", "#ffffff")).toBeCloseTo(21, 0);
    expect(contraste("#777777", "#ffffff")).toBeCloseTo(4.48, 1);
  });
});
