---
id: SPEC-20
titulo: Qué se puede editar a mano sin invalidar lo ya firmado
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: 85ebef4
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-20 — Qué se puede editar a mano

## Qué problema resuelve

`VER-64` mide que `INV-03` bloquea en torno al **29%** de las escenas. Sobre una obra de
sesenta, eso son **diecisiete paradas que piden intervención**. `F-38` dejó el desatasco
barato —el bucle reanuda, los hallazgos se cierran y una instrucción humana entra en el
reintento— pero **no dijo qué se puede tocar**.

Y la pregunta no es de comodidad. Editar a mano el sitio equivocado es la forma más directa
de romper lo que el harness existe para proteger:

> El estado del mundo **se reconstruye acumulando los deltas de escena en orden** y no se
> relee del texto (`CLAUDE.md`). Un estado editado a mano deja de ser reconstruible, y a
> partir de ahí **nadie puede saber si el canon se deriva de la obra o de una corrección que
> alguien hizo un martes**.

---

## C-1 · La regla, en una frase

> **Se puede editar todo lo no consolidado, más el plan. Se puede editar lo que ninguna
> escena consolidada haya usado todavía. El estado consolidado no se toca a mano nunca.**

Las tres partes hacen trabajos distintos:

| Qué | Por qué |
| --- | --- |
| **Lo no consolidado** | No ha entrado en el canon, así que cambiarlo no propaga nada. Un borrador rechazado, un hallazgo abierto, una escena `planificada` |
| **El plan** | La escaleta, los hechos declarados, el conocimiento inicial y los beats son **entrada**, no resultado. Corregir un plan es replanificar, que es una cosa legítima |
| **Lo no usado todavía** | Un hecho declarado que ninguna escena consolidada ha revelado aún no sostiene nada. En cuanto una escena lo usa, deja de ser editable |

## C-2 · El estado consolidado no se toca, y esto es lo que lo hace cumplir

`EstadoDelMundo` —entidades vivas, ubicaciones, accesos, registro de conocimiento— es
**derivado**. No hay edición manual que sea correcta sobre un dato derivado: lo que hay es
corregir el delta que lo produjo, y eso ya no es editar, es **rehacer la escena**.

Así que la vía correcta para arreglar un estado equivocado tiene un solo camino: **deshacer
la consolidación de esa escena y volver a generarla**. Eso es caro y tiene que serlo, porque
todo lo que vino después se generó leyendo ese estado.

## C-3 · Lo que está en uso se dice, y no se adivina

Un hecho, un lugar o un personaje está **en uso** desde el momento en que una escena
`consolidada` lo referencia en su delta o en el registro de conocimiento.

La comprobación es una consulta, no un juicio, y por eso la hace el código: quien vaya a
editar pregunta y obtiene un sí o un no **con la lista de escenas que lo usan**. Un "no se
puede" sin decir quién lo impide obliga a ir a buscarlo a mano, que es exactamente el coste
que `F-38` existía para quitar.

## C-4 · Toda edición manual deja rastro

Quién, cuándo y por qué. Sin esto, una obra con diecisiete intervenciones es indistinguible
de una que salió sola, y **lo que el harness mide deja de significar nada**: `VER-64` estaría
contando paradas de un sistema que alguien fue corrigiendo por el camino.

Es el mismo argumento que obligó a poner motivo al cerrar un hallazgo (`F-38`).

## Qué queda explícitamente fuera

- **Deshacer una consolidación.** `C-2` dice que es el único camino correcto para un estado
  equivocado, y **no lo implementa**: hace falta decidir qué pasa con las escenas
  posteriores, que se generaron leyendo ese estado.
- **Una interfaz.** Esto define qué se puede tocar y qué deja rastro, no cómo se toca.
- **Editar el texto de un borrador a mano.** Un borrador es lo que devolvió el agente; si
  se edita, deja de serlo, y `VER-60` —que compara el manuscrito con el borrador auditado—
  dejaría de significar nada.

## Qué gobierna esto

`EstadoDelMundo`, `HechoCanonico`, `RegistroDeConocimiento` y `estado_de_escena` de
`Docs/definitions.md`; el *"el estado del mundo se reconstruye acumulando los deltas"* de
`CLAUDE.md`; `F-38` y `VER-60` de `Docs/verification.md`.

## Preguntas respondidas al aprobar

| # | Pregunta | Respuesta |
| --- | --- | --- |
| 1 | ¿Qué se puede editar? | Todo lo no consolidado, más el plan, más lo que ninguna escena consolidada haya usado |
| 2 | ¿Y el estado consolidado? | **Nunca.** Es derivado, y la vía correcta es rehacer la escena que lo produjo |
| 3 | ¿Cómo se sabe si algo está en uso? | Se pregunta al código, y responde con la lista de escenas que lo usan |
| 4 | ¿Las ediciones dejan rastro? | Sí, con motivo. Sin él, una obra intervenida no se distingue de una que salió sola |
