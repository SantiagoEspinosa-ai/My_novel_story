// PLAN-35 E8 (SPEC-35): recorrido de la portada, el indice, la version nueva y pedir un cambio,
// en Edge sin cabeza y sin modelo, sobre la base de backend/semilla_lectura.py (datos
// inventados, dos versiones y una peticion) servida en 8010 y Vite en 5183:
//
//   PW=<ruta a node_modules/playwright> OUT=<carpeta> node scripts/recorrido-seis-pantallas.mjs
//
// La semilla deja una escena planificada sin texto: el PDF no se ofrece (F-201) hasta completarla.
// Proponer un cambio no llama al modelo; «Confirmar el cambio» si gastaria y NO se pulsa.
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PW);
const BASE = "http://127.0.0.1:5183";
const OUT = process.env.OUT;
const O = "obra-semilla-inventada";
const hallazgos = [];
const b = await chromium.launch({ channel: "msedge", headless: true });
async function pagina(w, h) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  p.on("console", (m) => { if (m.type() === "error") hallazgos.push(`consola ${p.url()}: ${m.text()}`); });
  p.on("pageerror", (e) => hallazgos.push(`excepcion ${p.url()}: ${e.message}`));
  return p;
}
const ok = (c, t) => { if (c) console.log("ok  " + t); else hallazgos.push("FALLA: " + t); };

const p = await pagina(1280, 900);
await p.goto(`${BASE}/obras/${O}`);
await p.getByRole("link", { name: "Empezar a leer" }).waitFor();
await p.getByRole("link", { name: "Descargar en PDF" }).waitFor({ timeout: 5000 }).catch(() => {});
ok(await p.getByRole("link", { name: "Descargar en PDF" }).isVisible(), "portada: el PDF se ofrece");
ok((await p.getByRole("link", { name: "Descargar en PDF" }).getAttribute("href")) === `/api/obras/${O}/pdf`, "portada: el enlace del PDF");
await p.waitForTimeout(400);
await p.screenshot({ path: `${OUT}/35-1-portada.png`, fullPage: true });

await p.goto(`${BASE}/obras/${O}/indice`);
await p.getByTestId("version-actual").waitFor();
ok((await p.getByTestId("version-actual").innerText()).includes("Versión 2 (vigente)"), "indice: la version 2 es la vigente, dicha por el backend");
ok((await p.locator('[data-cambio="true"]').count()) === 1, "indice: un capitulo marcado como cambiado");
ok((await p.getByTestId("escena-del-indice").count()) > 0, "indice: las escenas siguen con su estado (CLAUDE.md)");
await p.screenshot({ path: `${OUT}/35-2-indice.png`, fullPage: true });

await p.goto(`${BASE}/obras/${O}/versiones/2/capitulos/cap-01-v2`);
await p.getByTestId("por-tu-cambio").waitFor();
ok((await p.getByTestId("por-tu-cambio").innerText()).includes("faro sea de piedra"), "capitulo cambiado: dice la peticion con las palabras del lector");
await p.screenshot({ path: `${OUT}/35-3-capitulo-cambiado.png`, fullPage: true });
await p.goto(`${BASE}/obras/${O}/versiones/2/capitulos/cap-02`);
await p.getByTestId("bloque-de-escena").first().waitFor();
ok((await p.getByTestId("por-tu-cambio").count()) === 0, "capitulo compartido: sin aviso");

await p.goto(`${BASE}/obras/${O}/versiones/2/capitulos/cap-01-v2`);
await p.getByTestId("bloque-de-escena").first().waitFor();
const boton = p.getByRole("button", { name: /Pedir un cambio/ }).first();
await boton.click();
await p.getByTestId("pedir-cambio").waitFor();
const opcion = p.locator(".pedir-cambio__opciones input[type=radio]").first();
await opcion.waitFor({ timeout: 5000 }).catch(() => {}); // los hechos llegan despues del panel
if (await opcion.count()) {
  await opcion.check();
  await p.getByLabel(/Cómo debería ser/).fill("El faro es de ladrillo (inventado).");
  await p.getByLabel(/Con tus palabras/).fill("Mejor de ladrillo (inventado).");
  await p.getByRole("button", { name: /Ver qué capítulos se tocarían/ }).click();
  await p.getByTestId("propuesta").waitFor();
  const balda = await p.getByTestId("balda").count();
  ok(balda === 1, "que se reescribe: la balda aparece");
  if (balda) ok((await p.getByTestId("capitulo-que-se-toca").count()) >= 1, "que se reescribe: al menos un capitulo resaltado");
  ok((await p.getByTestId("punto-ciego").count()) === 1, "que se reescribe: la promesa va con su punto ciego");
} else {
  hallazgos.push("AVISO: la escena no ofrece hechos para elegir; no se pudo llegar a la propuesta");
}
await p.screenshot({ path: `${OUT}/35-4-pedir-cambio.png`, fullPage: true });

const m = await pagina(390, 844);
await m.goto(`${BASE}/obras/${O}/indice`);
await m.getByTestId("version-actual").waitFor();
const ancho = await m.evaluate(() => document.documentElement.scrollWidth);
ok(ancho <= 390, `indice a 390 px sin scroll horizontal (${ancho})`);
await m.screenshot({ path: `${OUT}/35-5-indice-movil.png`, fullPage: true });
await m.goto(`${BASE}/obras/${O}`);
await m.getByRole("link", { name: "Empezar a leer" }).waitFor();
const anchoP = await m.evaluate(() => document.documentElement.scrollWidth);
ok(anchoP <= 390, `portada a 390 px sin scroll horizontal (${anchoP})`);
await b.close();
console.log("\nHALLAZGOS (" + hallazgos.length + "):\n" + hallazgos.join("\n"));
