---
name: spec-and-plan
description: >
  Run this project's gated workflow: spec, then implementation plan, then code.
  Use when starting any change that decides something new, when asked to write
  or update a spec or an implementation plan, when asked to start coding a
  feature, or when checking whether a gate is open. Enforces that no plan is
  written without an approved spec and no code without an approved plan, and
  that specs and docs are updated when the work lands.
---

# Spec, plan y código

El proceso de trabajo de este repositorio, ejecutable. La versión normativa está
en `AGENTS.md` § Proceso de trabajo; esta skill lo aplica.

```
docs/  →  spec aprobada  →  plan aprobado  →  código (TDD)  →  spec y docs/ al día
```

## Lo primero: ¿qué puerta está abierta?

Antes de escribir nada, comprueba en qué punto estás. **Esto no es una
formalidad: es lo que la skill hace.**

| Te piden | Comprueba | Si no se cumple |
| --- | --- | --- |
| Un cambio en `docs/` | ¿Es documental o decide algo nuevo? | Si decide algo nuevo: hace falta spec |
| Un plan | ¿Su spec tiene `estado: aprobada`? | **No escribas el plan.** Dilo y escribe o termina la spec |
| Código | ¿Su plan tiene `estado: aprobada`? | **No escribas código**, ni andamiaje |

Decir "no, esta puerta está cerrada" es el trabajo. No la abras por tu cuenta ni
pidas permiso para saltártela: termina lo que falta.

## Dónde vive todo

**Un fichero por spec, plano en `specs/`.** Sin carpetas anidadas. Hoy existe
`specs/SPEC - Backend.md`, que es `SPEC-01`, la spec del backend del harness.
Los planes van en `specs/plans/PLAN-NN.md`, con el mismo identificador que su
spec.

La aprobación es el frontmatter del propio fichero:

```yaml
---
id: SPEC-01
titulo: ...
estado: en_revision      # borrador | en_revision | aprobada | obsoleta
aprobada_por:            # quién, solo cuando estado es "aprobada"
fecha_aprobacion:        # cuándo
---
```

Haberlo hablado en el chat **no** es una aprobación. `SPEC-NN` es un
identificador estable: no se reutiliza ni se renumera, y lo que deja de aplicar
pasa a `obsoleta`. **Los identificadores internos de una spec (`RF-xx`, `O-x`,
`M-x`, `P-x`) tampoco se renumeran al reescribirla**, aunque cambien de sitio.

## 1. La spec

Un fichero propio en `specs/`, con su `SPEC-NN` en el frontmatter.

**Antes de escribirla, pregunta.** Es la parte que más se salta y la que más
cuesta después. Una spec con huecos rellenados por suposición es peor que no
tener spec, porque parece acordada. Pregunta lo que no esté claro, y pregunta
también lo que parezca obvio si cambia el resultado.

Responde a tres cosas, y solo a tres:

1. **Qué problema resuelve.** El hueco concreto, no la solución.
2. **Qué tiene que ser verdad al terminar.** Criterios numerados y comprobables,
   para poder citarlos desde el plan y desde `docs/verification.md`.
3. **Qué queda explícitamente fuera.** Lo que no se hace y por qué.

Más dos secciones cortas: **qué la gobierna** (`INV-xx`, `A-xx`, `VER-xx`, y qué
documento manda) y **qué documentos quedan al día al terminar**.

**Una spec no dice cómo se hace.** Nada de ficheros, funciones ni orden de
tareas: eso es el plan. Si te sale un nombre de fichero, va en el plan.

**Si la spec modifica `CLAUDE.md`, dilo explícitamente**, porque es el documento
que manda en lo técnico.

## 2. El plan

Vive en `specs/plans/PLAN-NN.md`, con el mismo identificador que su spec.

- **Comprueba primero que la spec está aprobada**, en el frontmatter de su
  propio fichero. Si no, para.
- Dice qué ficheros se tocan, en qué orden, **qué prueba cubre cada paso** y qué
  filas `VER-xx` de `docs/verification.md` cierra.
- **Cada paso deja el repositorio funcionando.** Un paso que solo tiene sentido
  con el siguiente son un paso.
- Cada paso cita el criterio de la spec que satisface.

## 3. El código

- **Comprueba primero que el plan está aprobado.** Si no, para.
- **TDD, en este orden:** la prueba que falla, el código mínimo que la pasa, el
  refactor. Ningún código de producción nace sin una prueba que haya fallado
  antes.
- **Al terminar, en el mismo commit:** spec al día, `docs/` al día y la fila
  `VER-xx` actualizada si se ha cerrado alguna.

## Cuando el código descubre que la spec estaba mal

Pasa, y es sano. Lo que no vale es seguir.

Se para, se corrige la spec, se vuelve a aprobar, y si el plan cambia de forma,
también. **El código nunca avanza por delante de la spec**: en cuanto lo hace, la
spec deja de gobernar lo que se va a hacer y pasa a describir mal lo ya hecho. A
las tres semanas es ficción y nadie la lee.

## Números y aprobaciones

Dos reglas del proyecto que aquí se aplican constantemente:

- **Ningún número sin medir.** Si un criterio necesita un umbral y ese número no
  existe, el criterio dice que falta medirlo. No se pone un valor provisional:
  un umbral inventado que queda escrito deja de distinguirse de uno medido.
- **No cambies tú el `estado` a `aprobada`.** Lo aprueba una persona, y su
  nombre y la fecha van en el frontmatter.
