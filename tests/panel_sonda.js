// Sonda del panel para los tests: corre el JavaScript REAL de panel.html fuera
// del navegador y cuenta que datos ha conseguido cargar.
//
// Por que existe: el panel es una sola pagina sin dependencias y sin build, asi
// que la unica forma honesta de comprobar que un capitulo del disco llega a la
// pantalla es ejecutar su codigo tal cual y mirar el resultado. Reimplementar
// aqui la logica de carga probaria la copia, no el panel.
//
//   node tests/panel_sonda.js <ruta a panel.html> <url base servida>
//
// Imprime por salida estandar un JSON con los capitulos cargados y el detalle
// de cada peticion, para que el test de pytest lo lea.
const fs = require("fs");
const vm = require("vm");

const [rutaPanel, base] = process.argv.slice(2);
if (!rutaPanel || !base) {
  console.error("uso: node panel_sonda.js <panel.html> <url base>");
  process.exit(2);
}

const html = fs.readFileSync(rutaPanel, "utf8");
const script = html.slice(html.indexOf("<script>") + 8, html.lastIndexOf("</script>"));

// DOM de mentira: el panel pinta en elementos que aqui no existen. Se traga
// cualquier propiedad y cualquier llamada, porque lo que se mide es que DATOS
// carga, no que dibuja.
const elemento = new Proxy(function () {}, {
  get(t, p) {
    if (p === "classList") return { add() {}, remove() {}, toggle() {}, contains: () => false };
    if (p === "dataset") return {};
    if (p === "textContent" || p === "innerHTML" || p === "value") return "";
    if (p === "hidden") return false;
    if (p === Symbol.toPrimitive) return () => "";
    return elemento;
  },
  set() { return true; },
  apply() { return elemento; },
});

const documento = {
  querySelector: () => elemento,
  querySelectorAll: () => [],
  addEventListener() {},
  documentElement: elemento,
  body: elemento,
  createElement: () => elemento,
};

const sandbox = {
  document: documento,
  console: { log() {}, warn() {}, error() {} },
  // El panel decide por location.protocol si carga por red o espera archivos a
  // mano. Aqui siempre es por red, que es el modo que se quiere probar.
  location: { protocol: "http:", hash: "", href: base + "panel.html" },
  matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
  history: { replaceState() {}, pushState() {} },
  exportar: (o) => { global.__panel = o; },
  addEventListener() {},
  requestAnimationFrame: (f) => f(),
  setTimeout, clearTimeout,
  // `setInterval` se anula a proposito. El panel arranca un sondeo periodico de
  // `estado.json` y un reloj de un segundo para el cronometro, que en un
  // navegador es justo lo que se quiere y aqui dejaria el proceso de node vivo
  // para siempre: la sonda se colgaria y con ella los tests. Lo que se mide es
  // la PRIMERA carga, que no necesita ningun intervalo.
  setInterval: () => 0,
  clearInterval: () => {},
  // El navegador resuelve las rutas relativas contra la pagina; node no, asi que
  // se resuelven aqui.
  fetch: (ruta, opts) => fetch(new URL(ruta, base).href, opts),
  URL, JSON, Promise, Math, Array, Object, String, Number,
  Map, Set, RegExp, Date, Intl, parseInt, parseFloat, isNaN,
};
sandbox.window = sandbox;
sandbox.globalThis = sandbox;

vm.createContext(sandbox);
// `D` y `RED` se declaran con let/const, asi que viven en el ambito lexico del
// script y no en el global del sandbox: hay que sacarlos desde dentro.
vm.runInContext(script + "\n;exportar({ D: D, RED: RED });", sandbox, { filename: "panel.html" });

// El arranque del panel lanza cargarPorRed() sin await. Se espera a que la
// bandera `cargando` baje, en vez de dormir un rato fijo: un tiempo fijo o
// sobra o se queda corto segun la maquina.
const LIMITE_MS = 30000;
const arranque = Date.now();
(function esperar() {
  const { D, RED } = global.__panel;
  if (RED.cargando || (!RED.base && Date.now() - arranque < 1000)) {
    if (Date.now() - arranque > LIMITE_MS) {
      console.error("la carga del panel no termino en " + LIMITE_MS + " ms");
      process.exit(3);
    }
    return setTimeout(esperar, 50);
  }
  process.stdout.write(JSON.stringify({
    base: RED.base,
    capitulos: Array.from(D.capitulos.keys()).sort((a, b) => a - b),
    fuentes: Array.from(D.fuentes),
    intentos: RED.intentos.map(x => ({ ruta: x.ruta, ok: x.ok, motivo: x.motivo || "" })),
  }));
  // Salida explicita: si el panel dejara cualquier cosa pendiente en el bucle de
  // eventos, el proceso no terminaria y el test se quedaria esperando hasta su
  // tiempo limite. Ya hemos escrito todo lo que habia que escribir.
  process.exit(0);
})();
