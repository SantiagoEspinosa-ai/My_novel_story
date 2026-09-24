# Procedencia de esta skill

| | |
| --- | --- |
| **Última revisión contra la documentación oficial** | 2026-09-21 |
| **Estado** | Vendorizada, sin mantenimiento aguas arriba |
| **Contrastar de nuevo antes de** | 2027-03-21 (seis meses), o antes si algo de aquí no cuadra |

Esta skill **no se instaló con `npx skills add`** y por eso no aparece en
`skills-lock.json`. Se recuperó a mano, y conviene saber de dónde sale.

## Qué pasó

El encargo pedía instalar la skill anunciada en
`https://mcpmarket.com/es/tools/skills/sqlite-vector-search-sqlite-vec`, que
figura como *SQLite Vector Search (sqlite-vec)*, de `existential-birds`.

Esa skill **ya no existe en su repositorio**. El autor la eliminó en el commit
`242d64b` (*"refactor!: restructure marketplace for official submission"*, PR
#115), junto con `docling` y `github-projects`, bajo el epígrafe
`### Removed: vendor skills from beagle-core` de su CHANGELOG. El listado de
mcpmarket está desactualizado y anuncia algo que el autor borró.

Otras dos fuentes que aparecen en buscadores tampoco sirven:

- `anderskev/amelia` — tampoco contiene ya una skill `sqlite-vec`.
- `aibot88/sec_skill_store` — no es del autor original: es un agregador que
  rastrea y re-hospeda skills de terceros. No se usó por procedencia dudosa.

## De dónde salen estos ficheros

Del historial de git del repositorio original, en el estado inmediatamente
anterior al borrado:

- Repositorio: `https://github.com/existential-birds/beagle`
- Commit: `7d9355fa712164ec8dd739d1d433e2e8ff799069` (2026-05-27)
- Ruta original: `plugins/beagle-core/skills/sqlite-vec/`
- Ficheros: `SKILL.md`, `references/setup.md`, `references/tables.md`,
  `references/queries.md`, `references/operations.md`

Se copiaron tal cual, sin modificarlos.

## Revisión de seguridad

Se revisó el contenido antes de instalarlo, porque una skill corre con los
permisos completos del agente. Los cinco ficheros son **documentación**: SQL y
Python de ejemplo sobre la extensión `sqlite-vec`. No hay scripts ejecutables,
ni llamadas de red, ni instrucciones al agente más allá del uso de la
extensión.

## Qué tener en cuenta: esto envejece en silencio

Aquí está el riesgo real, y por eso este fichero lleva una fecha de revisión
arriba.

**Es una skill congelada que describe una librería viva.** El contenido quedó
fijado en mayo de 2026 y su autor la abandonó, así que no recibirá ninguna
actualización. `sqlite-vec`, en cambio, sigue desarrollándose: cambian firmas de
funciones, aparecen operadores de filtrado nuevos, se corrigen comportamientos
de `vec0`. Dentro de unos meses esta skill afirmará cosas que ya no son ciertas
y **nada lo avisará**: no fallará, no dará error, simplemente describirá una
versión de la librería que ya no existe. Una skill obsoleta es más peligrosa que
ninguna skill, porque se lee con la misma confianza que una al día.

**Regla de uso.** Antes de confiar en cualquier afirmación concreta de esta
skill —una firma, un operador de filtrado, una regla de las claves de
partición, un comportamiento dependiente de versión— contrástala con la
documentación oficial:

- `https://alexgarcia.xyz/sqlite-vec` — documentación de la extensión
- `https://alexgarcia.xyz/sqlite-vec/api-reference.html` — referencia de la API
- `https://github.com/asg017/sqlite-vec` — el proyecto real

Si algo de la skill contradice a esa documentación, **gana la documentación** y
hay que corregir la skill.

**Al revisarla, actualiza la fecha de la tabla de arriba.** Una fecha de
revisión que no se mueve deja de informar: hace creer que se comprobó hace poco
cuando lo que pasó es que nadie la ha mirado. Si la revisas y todo sigue
correcto, eso también es una revisión y la fecha cambia igual.
