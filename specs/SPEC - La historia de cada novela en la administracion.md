---
id: SPEC-37
titulo: La historia de cada novela en la administración (línea de tiempo)
estado: aprobada
aprobada_por: "autor del proyecto, en sesión: «quiero la c» sobre docs/proceso/propuestas-visuales/administracion.html"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# SPEC-37 — La historia de cada novela

## Qué problema resuelve

La administración de `SPEC-36` es una tabla plana: dice cuánto costó una novela y cuántos
hallazgos tiene, pero no **qué pasó**. El autor quiere ver, por novela, las seis notas del
Editor por capítulo, el coste desglosado por capítulo y por agente, los hallazgos abiertos con
su invariante y su severidad, las paradas (dónde, por qué y cuántos intentos), Lean y la puerta
de publicación, y qué cambió en cada versión. Entre tres propuestas eligió **la C, la línea de
tiempo**.

## Qué tiene que ser verdad al terminar

- **RF-01 · Una página por novela**, `/admin/obras/{id}`, a la que lleva cada fila de la
  administración de `SPEC-36` `RF-03`, que se queda como índice.
- **RF-02 · La historia en orden**: la entrevista cerrada, las rondas del plan con sus
  objeciones, cada capítulo escrito con sus **seis notas**, su estado, sus intentos y su coste,
  cada **parada** con su capítulo y su motivo, cada **ronda de la puerta** con el código de Lean y
  las condiciones que no se cumplieron, y cada **versión nueva** con las palabras de su petición
  y los capítulos que cambiaron. Lo que no tiene hora (las rondas del plan) va en su sitio
  lógico y lo dice.
- **RF-03 · Al lado, fijo**: el coste total y las delegaciones (suelo si lo es), la nota media,
  las paradas, la versión vigente, **el coste por agente** y los **hallazgos abiertos** con su
  invariante, su severidad y su capítulo.
- **RF-04 · El coste por capítulo se atribuye, y se dice cómo.** El gasto no guarda el capítulo.
  Cada delegación se atribuye a la última fase del progreso de la obra anterior a ella, que el
  pipeline apunta justo antes de cada llamada; a la versión, por su fecha de creación. **Todo lo
  resuelve el backend**; la página lo pinta.

## Qué queda explícitamente fuera

- Guardar el capítulo en cada gasto (una migración): se atribuye por el progreso, y el punto
  ciego (dos fases en el mismo segundo) se declara.
- Acciones desde la página, y login (`SPEC-36`).

## Lo que la gobierna

`SPEC-36` `RF-03`, `SPEC-33` `RF-18` (el gasto de cada delegación), `SPEC-23` (versiones),
`SPEC-30` (la puerta), `CLAUDE.md` (la interfaz muestra estado, no lo calcula).
