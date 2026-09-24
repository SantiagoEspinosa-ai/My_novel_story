---
name: spec-plan-codigo-con-puertas
description: "En My_novel_story no se escribe código sin plan aprobado, ni plan sin spec aprobada, y el código se escribe con TDD actualizando spec y Docs al terminar."
metadata: 
  node_type: memory
  pinned: true
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-21T17:49:36.403Z
---

# Spec → plan → código, con puertas que no se saltan

El usuario definió este proceso de trabajo de forma explícita y pidió dejarlo
escrito en `AGENTS.md`. Son tres puertas en cadena, y ninguna se salta porque el
cambio parezca pequeño:

```
Docs/  →  spec aprobada  →  plan aprobado  →  código (TDD)  →  spec y Docs/ al día
```

- **No se crea un plan de implementación si su spec no está aprobada.**
- **No se escribe código si el plan no está aprobado**, ni siquiera ficheros de
  andamiaje.
- **El código se escribe con TDD**: primero la prueba que falla, después el
  código mínimo que la pasa, después el refactor.
- **Al terminar, en el mismo commit**: spec al día, `Docs/` al día y la fila
  `VER-xx` de `Docs/verification.md` actualizada si se cerró alguna.

## Lo que cuenta como aprobación

Un campo `estado` en el frontmatter del propio fichero (`borrador | en_revision
| aprobada | obsoleta`, más `aprobada_por` y `fecha_aprobacion`). Haberlo
hablado en el chat **no** es una aprobación.

**Un fichero por spec, y dos carpetas según su estado.** El usuario descartó
primero la convención de una carpeta por spec, y después la de un único documento
que las contuviera todas: cada documento es una spec y nada más. Las specs en
curso viven planas en `specs/`; los planes van aparte, en
`specs/plans/PLAN-NN.md`.

**Una spec aplicada se mueve a `specs/aplicadas/` con `git mv`, no se borra.**
El usuario pidió esta carpeta al ver que había tres specs aplicadas en tres
sitios distintos: una retirada y dos sueltas en `specs/`. Antes de moverla se
le pone `estado: aplicada`, `fecha_aplicacion` y `commit_de_aplicacion`. Ese
hash **necesita un commit propio**, porque no existe hasta después de commitear
el cambio que la aplica: primero el commit que aplica, luego el que anota el
hash. Mover el fichero no rompe nada porque en este proyecto las specs se
referencian siempre por identificador (`SPEC-03`) y nunca por ruta.

`SPEC-NN` es un identificador estable que no se reutiliza ni se renumera, y los
identificadores internos de una spec (`RF-xx`, `O-x`, `M-x`, `P-x`) tampoco se
renumeran al reescribirla.

## Dos matices que el usuario pidió expresamente

1. **Antes de escribir una spec hay que preguntar.** Dijo literalmente
   "pregúntame para aclarar la spec". Una spec con huecos rellenados por
   suposición es peor que no tener spec, porque parece acordada. Las dudas se
   preguntan al escribirla, no se descubren implementando.
2. **Si implementando se descubre que la spec estaba mal, se para.** Se corrige
   la spec, se vuelve a aprobar y, si el plan cambia de forma, también. El
   código nunca avanza por delante de la spec: en cuanto lo hace, la spec deja
   de gobernar y pasa a describir mal lo ya hecho.

Distingue además dos clases de cambio en `Docs/`: el puramente documental
(corregir, aclarar, dibujar algo ya decidido) se hace directo, sin spec; el que
decide algo nuevo (una clase, una invariante, una decisión de arquitectura, un
umbral) necesita spec aprobada antes.

## Reformatear una spec aprobada no la devuelve a la puerta

Al reescribir `SPEC-22` de spec de cambio a SRS, el usuario lo dijo así:

> *"`SPEC-22` ya está aprobada en su versión 1, así que la versión 2 es la misma
> spec reformateada: conserva su estado y su fecha de aprobación, y deja el
> cambio de forma en el historial."*

De ahí sale la regla: **un cambio de forma conserva `estado`, `aprobada_por` y
`fecha_aprobacion`**, sube la `version` y explica en el historial qué se movió.
Lo que dispara una aprobación nueva es **decidir algo distinto**, no
reorganizarlo. Bajar una spec aprobada a `en_revision` por haberla reformateado
bloquea su plan y su código sin que nadie haya cambiado de opinión.

Va con dos cosas que el usuario pidió en el mismo encargo y que son la otra mitad
de la regla:

- **Conservar lo que hace buena a la spec al reformatearla**, nombrándolo: en
  aquel caso el principio de que los validadores de un lado comprueban su lado,
  la lista de lo que falta con su estado, y los puntos ciegos declarados. Un
  reformateo que pierda eso ha perdido más de lo que ganó.
- **No renumerar ni retirar los identificadores de la versión anterior.** Los
  `C-x`, `D-x` y `G-xx` siguen existiendo y cada requisito nuevo dice de qué
  `C-x` sale, para que lo aprobado se pueda seguir rastreando.
