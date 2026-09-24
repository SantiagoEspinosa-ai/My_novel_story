// PLAN-22 E6 (VER-106, VER-16): el frontend no toca la base, solo shared/api habla con la
// red, y ninguna prueba llama a un backend (SPEC-22 NF-01, NF-06).
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { MENSAJE_FETCH } from "./setup";

// La raiz del frontend: vitest corre desde ella (npm test).
const RAIZ = process.cwd();
const CLIENTES_DE_BASE = [
  "sqlite3", "better-sqlite3", "sql.js", "pg", "mysql", "mysql2", "mongodb", "mongoose",
  "prisma", "@prisma/client", "knex", "sequelize", "typeorm", "drizzle-orm", "redis",
  "@libsql/client", "sqlite",
];

function ficheros(dir: string): string[] {
  return readdirSync(dir).flatMap((n: string) => {
    const r = join(dir, n);
    return statSync(r).isDirectory() ? ficheros(r) : [r];
  });
}

describe("frontera", () => {
  it("ningun paquete es un cliente de base de datos", () => {
    const pkg = JSON.parse(readFileSync(join(RAIZ, "package.json"), "utf-8"));
    const deps = Object.keys({ ...pkg.dependencies, ...pkg.devDependencies });
    expect(deps.filter((d) => CLIENTES_DE_BASE.includes(d))).toEqual([]);
  });

  it("solo shared/api llama a fetch", () => {
    const fuera = ficheros(join(RAIZ, "src"))
      .filter((f) => /\.(ts|tsx)$/.test(f) && !/\.test\.tsx?$/.test(f))
      .filter((f) => !relative(join(RAIZ, "src"), f).startsWith(["shared", "api"].join(sep)))
      .filter((f) => /\bfetch\s*\(/.test(readFileSync(f, "utf-8")));
    expect(fuera.map((f) => relative(RAIZ, f))).toEqual([]);
    // Y shared/api existe y lo hace: si nadie lo llamara, la regla pasaria sin mirar nada.
    const cliente = readFileSync(join(RAIZ, "src", "shared", "api", "cliente.ts"), "utf-8");
    expect(cliente).toMatch(/fetch/);
  });

  it("una prueba que llama a fetch sin inyectarlo falla", () => {
    expect(() => fetch("/api/obras/x/indice")).toThrow(MENSAJE_FETCH);
  });
});
