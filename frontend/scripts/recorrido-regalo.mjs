// PLAN-33 E15 (VER-133): recorrido de la web real en Edge sin cabeza, sin modelo y sin gastar,
// sobre la base de backend/semilla_regalo.py servida en 8010 y Vite en 5183:
//
//   PW=<ruta a node_modules/playwright> OUT=<carpeta de capturas> node scripts/recorrido-regalo.mjs
//
// Usa el Playwright que trae la cache de npx del browser MCP (@playwright/mcp). No pulsa
// «Responder» (llamaria al Entrevistador) ni «Sí, escribir la novela» (gasta). No sustituye
// a mirar las capturas: F-200 paso todas las comprobaciones y solo lo vio una captura.
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW);

const BASE = "http://127.0.0.1:5183";
const OUT = process.env.OUT;
const hallazgos = [];
const navegador = await chromium.launch({ channel: "msedge", headless: true });

async function pagina(ancho, alto) {
  const p = await navegador.newPage({ viewport: { width: ancho, height: alto } });
  p.on("console", (m) => { if (m.type() === "error") hallazgos.push(`consola ${p.url()}: ${m.text()}`); });
  p.on("pageerror", (e) => hallazgos.push(`excepcion ${p.url()}: ${e.message}`));
  return p;
}

function comprobar(cond, texto) { if (!cond) hallazgos.push("FALLA: " + texto); else console.log("ok  " + texto); }

const p = await pagina(1280, 900);
await p.goto(BASE + "/");
await p.getByRole("heading", { name: "La estantería" }).waitFor();
await p.getByTestId("obra-obra-publicada").waitFor();
comprobar(await p.getByTestId(/^obra-/).count() === 4, "la estanteria tiene las 4 obras");
comprobar((await p.getByRole("button", { name: "Generar novela" }).count()) === 1, "un solo boton Generar novela");
comprobar(await p.getByTestId("obra-obra-a-medias").getByText("sin generación").isVisible(), "a medias dice sin generacion");
await p.screenshot({ path: `${OUT}/1-estanteria.png`, fullPage: true });
const ancho = await p.evaluate(() => document.documentElement.scrollWidth);
comprobar(ancho <= 1280, `sin scroll horizontal en escritorio (${ancho})`);

await p.getByTestId("obra-obra-a-medias").getByRole("link", { name: /Seguir la entrevista/ }).click();
await p.getByRole("heading", { name: "La entrevista" }).waitFor();
await p.getByTestId("turno-2").waitFor();
comprobar(await p.getByTestId("observaciones").first().isVisible(), "el aviso se ve dentro de su turno");
comprobar(await p.getByRole("button", { name: "Responder" }).isDisabled(), "Responder desactivado con la respuesta vacia");
await p.screenshot({ path: `${OUT}/2-entrevista.png`, fullPage: true });

await p.goto(BASE + "/");
await p.getByTestId("obra-obra-lista").getByRole("link", { name: /Escribir la novela/ }).click();
await p.getByTestId("gastado").waitFor();
const gastado = await p.getByTestId("gastado").innerText();
comprobar(gastado.includes("14,70 USD") && gastado.includes("de 50 USD") && gastado.includes("como mínimo"), "gastado 14,70 de 50 como minimo: " + gastado.replace(/\n/g, " | "));
comprobar((await p.getByTestId("referencia").innerText()).includes("16,89 USD"), "la referencia de 16,89");
comprobar(await p.getByRole("button", { name: /Sí, escribir la novela/ }).isEnabled(), "el boton que gasta, disponible y SIN pulsar");
await p.screenshot({ path: `${OUT}/3-confirmar.png`, fullPage: true });

await p.goto(BASE + "/obras/obra-en-curso/generacion");
await p.getByTestId("capitulos").waitFor();
await p.getByTestId("notas-2").waitFor();
comprobar((await p.getByTestId("capitulo-3").innerText()).includes("editando"), "el capitulo 3 editando");
const uno = await p.getByTestId("capitulo-1").innerText();
comprobar(uno.includes("consolidada") && !uno.includes("resumiendo"), "F-200: el capitulo 1 terminado dice consolidada, no resumiendo");
comprobar((await p.getByTestId("capitulo-7").innerText()).includes("no empezado"), "el capitulo 7 no empezado");
comprobar((await p.getByTestId("notas-2").getByTestId("nota-ritmo").innerText()).includes("bajo el umbral"), "la nota 2/5 del cap. 2, bajo el umbral");
const coste = await p.getByTestId("coste").innerText();
comprobar(coste.includes("2,40 USD") && coste.includes("como mínimo"), "coste en vivo 2,40 como minimo: " + coste.replace(/\n/g, " | "));
await p.screenshot({ path: `${OUT}/4-generacion.png`, fullPage: true });

const m = await pagina(390, 844);
await m.goto(BASE + "/");
await m.getByTestId("obra-obra-publicada").waitFor();
const anchoMovil = await m.evaluate(() => document.documentElement.scrollWidth);
comprobar(anchoMovil <= 390, `sin scroll horizontal a 390 px (${anchoMovil})`);
await m.screenshot({ path: `${OUT}/5-estanteria-movil.png`, fullPage: true });
await m.goto(BASE + "/obras/obra-en-curso/generacion");
await m.getByTestId("capitulos").waitFor();
const anchoGen = await m.evaluate(() => document.documentElement.scrollWidth);
comprobar(anchoGen <= 390, `generacion sin scroll horizontal a 390 px (${anchoGen})`);
await m.screenshot({ path: `${OUT}/6-generacion-movil.png`, fullPage: true });

await navegador.close();
console.log("\nHALLAZGOS (" + hallazgos.length + "):\n" + hallazgos.join("\n"));
