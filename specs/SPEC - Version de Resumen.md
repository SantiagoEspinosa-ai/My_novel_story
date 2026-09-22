---
id: SPEC-09
titulo: Resumen se versiona, como Ficha
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-09 — Versión de `Resumen`

## Que problema resuelve

`Ficha` tiene `version_en_t`. `Resumen` no tiene ni version ni `t`. Las dos son memoria a
largo plazo, las dos se reescriben segun avanza la obra, y solo una deja rastro de cual
era su contenido en un momento dado.

La asimetria se descubrio aplicando `SPEC-08`, al preguntarse si el contexto de una llamada
es reconstruible sin guardarlo entero. La respuesta resulto ser **casi**:

| Nivel del contexto | Reconstruible | Por que |
| --- | --- | --- |
| Estado actual | Si | `EstadoDelMundo` tiene `t`, y se reconstruye acumulando deltas en orden |
| Recuperado | Si, desde `SPEC-08` | `Ficha.version_en_t` da el contenido, y la traza guarda que ids entraron |
| Inmutable | Si | No cambia |
| **Resumenes** | **No** | Una condensacion de capitulo consumida en la escena 5 no se distingue de la de la escena 40 |

Un resumen de escena se escribe una vez y no cambia. Pero una condensacion de **capitulo**
o de **parte** se rehace segun crece su ambito, y nada distingue una version de otra.

## Que tiene que ser verdad al terminar

### C-1 - `Resumen` gana su version

| Clase | Atributo nuevo | Forma |
| --- | --- | --- |
| `Resumen` | **version_en_t** | El mismo nombre y la misma forma que en `Ficha` |

El mismo nombre a proposito: son el mismo concepto sobre las dos mitades de la memoria a
largo plazo, y dos nombres para lo mismo es como `juez LLM` divergio de `juez_llm`.

### C-2 - Queda cerrada la reconstruccion de una traza

Con `C-1`, los cuatro niveles del contexto son reconstruibles desde el estado en `t` mas
los identificadores que `SPEC-08` guarda en la traza, sin almacenar el texto. Se cierra la
decision abierta *"El nivel Resumenes de una traza no es reconstruible todavia"* de
`Docs/architecture.md`.

### C-3 - Migracion

`resumen` gana una columna. **Ya no es gratis.** Desde `PLAN-01` A3 existe `backend/app/commons/db/` con migraciones versionadas y validación de secuencia, así que un atributo obligatorio nuevo necesita **su migración numerada en el mismo commit**. Las versiones no admiten huecos ni repeticiones: una publicada no se borra ni se renumera.

## Que queda explicitamente fuera

- **Cuantas versiones se conservan.** Es retencion, y sale de medir.
- **Versionar otras clases.** `Ficha` ya la tiene y `Resumen` la gana; el resto no se
  toca en esta spec.
- **Como se consulta la version historica.** Es del plan.

## Que gobierna esto

`Ficha.version_en_t` de `Docs/definitions.md` como forma a copiar; `SPEC-08` y la seccion
"La traza de una llamada al modelo" de `Docs/architecture.md`; `M-4` de `SPEC-01`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | Se versionan los tres niveles de `Resumen`, o solo capitulo y parte? | Los tres. El de escena no cambiara nunca, pero una regla con excepcion se implementa mal antes o despues, y la columna vacia no cuesta nada |
| 2 | `version_en_t` pasa a ser obligatorio en `Resumen`? | Si, como en `Ficha`. Un resumen sin version no se puede situar, y ese es justo el problema que la spec resuelve |
| 3 | Hay mas clases de memoria a largo plazo con la misma asimetria? | `AnclaDeEstilo` no: es inmutable por definicion. `Presagio` tiene `escena_de_plantado` y `escena_de_pago`, que ya lo situan. Estas dos eran las unicas |
