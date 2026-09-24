# Procedencia de esta skill

| | |
| --- | --- |
| **Origen** | Oficial de Feature-Sliced Design v2.1 |
| **Repositorio** | https://github.com/feature-sliced/skills |
| **Ruta en upstream** | `feature-sliced-design/` |
| **Commit** | `ac06682d3a4862e71cf9b51f62b1c298e0b192d0` (2026-09-14) |
| **Instalada** | 2026-09-21, con `npx skills add`, en el commit `0cb14f9` de este repositorio |

`SKILL.md` y los nueve `references/` son idénticos a los de ese commit. Se comprobó el 2026-09-24 descargando cada fichero de ese commit y comparándolo con el vendorizado, sin contar finales de línea.

**`evals/` no sale de ese commit.** En upstream está en la raíz, como `evals/cases.json`; aquí es `evals/evals.json` con otro `README.md`, y no coincide con ninguno de los commits de la rama por defecto que tocan `evals/README.md`. Origen sin localizar: puede venir de otra rama o de una versión posterior. Entró en `0cb14f9`.

**El hash `e2b86275` que figuraba en el README es el `computedHash` del contenido** que guardaba el `skills-lock.json` borrado en `763a4d7`, no un commit.
