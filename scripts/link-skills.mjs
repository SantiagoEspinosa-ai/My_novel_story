#!/usr/bin/env node
/**
 * Recrea los enlaces de `.claude/skills/` hacia el contenido real de
 * `.agents/skills/`.
 *
 * Por qué existe este script
 * -------------------------
 * El contenido real de las skills vive en `.agents/skills/` y se versiona con
 * el repositorio. `.claude/skills/` está en `.gitignore` porque solo contiene
 * enlaces, y git en Windows no los guarda como enlaces: los convierte en
 * ficheros de texto con la ruta dentro, que no sirven para nada.
 *
 * Consecuencia: quien clona el repositorio se trae las skills pero no los
 * enlaces. Este script los rehace con un comando:
 *
 *     node scripts/link-skills.mjs
 *
 * Sobre Windows
 * -------------
 * Crear un enlace simbólico en Windows normalmente exige permisos de
 * administrador o el modo desarrollador activado. Para carpetas existe una
 * alternativa que no exige ninguna de las dos cosas: el *junction*. Por eso el
 * script usa `junction` en Windows y `dir` en el resto de sistemas. Si aun así
 * falla, cae a copiar la carpeta, que funciona siempre aunque haya que volver
 * a ejecutar el script cuando la skill cambie.
 */

import { cpSync, existsSync, lstatSync, mkdirSync, readdirSync, rmSync, symlinkSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const origen = join(raiz, ".agents", "skills");
const destino = join(raiz, ".claude", "skills");

// En Windows el tipo "junction" funciona sin privilegios; en el resto, "dir".
const tipoDeEnlace = process.platform === "win32" ? "junction" : "dir";

if (!existsSync(origen)) {
  console.error(`No existe ${relative(raiz, origen)}. ¿Estás en la raíz del repositorio?`);
  process.exit(1);
}

mkdirSync(destino, { recursive: true });

const skills = readdirSync(origen, { withFileTypes: true })
  .filter((entrada) => entrada.isDirectory())
  .map((entrada) => entrada.name);

if (skills.length === 0) {
  console.log(`No hay ninguna skill en ${relative(raiz, origen)}.`);
  process.exit(0);
}

let enlazadas = 0;
let copiadas = 0;

for (const nombre of skills) {
  const rutaOrigen = join(origen, nombre);
  const rutaDestino = join(destino, nombre);

  // Borra lo que haya: un enlace viejo, un fichero de texto que git haya
  // dejado en lugar del enlace, o una copia de una ejecución anterior.
  if (existsSync(rutaDestino) || esEnlaceRoto(rutaDestino)) {
    rmSync(rutaDestino, { recursive: true, force: true });
  }

  try {
    symlinkSync(rutaOrigen, rutaDestino, tipoDeEnlace);
    console.log(`  enlazada  ${nombre}`);
    enlazadas += 1;
  } catch (error) {
    // Sin permisos para crear el enlace: copiar es peor pero funciona.
    cpSync(rutaOrigen, rutaDestino, { recursive: true });
    console.log(`  copiada   ${nombre}  (no se pudo enlazar: ${error.code ?? error.message})`);
    copiadas += 1;
  }
}

console.log(`\n${skills.length} skill(s): ${enlazadas} enlazada(s), ${copiadas} copiada(s).`);
if (copiadas > 0) {
  console.log(
    "Las copiadas no se actualizan solas: vuelve a ejecutar el script cuando cambie su contenido.",
  );
}

/**
 * `existsSync` devuelve false para un enlace roto, así que haría que el script
 * se saltara el borrado y fallara después al crear el enlace nuevo.
 */
function esEnlaceRoto(ruta) {
  try {
    lstatSync(ruta);
    return true;
  } catch {
    return false;
  }
}
