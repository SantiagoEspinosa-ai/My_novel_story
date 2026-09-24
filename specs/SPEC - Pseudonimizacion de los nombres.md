---
id: SPEC-34
titulo: Pseudonimización de los nombres en la frontera con los agentes
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-24
version: 1
---

> **Historial.** v1: redactada con las tres respuestas del autor del 2026-09-24 (los nombres
> entran por campos propios, el modelo ve nombres inventados, y se pseudonimiza todo lo que
> sale). Cuatro cuestiones abiertas al final.

# SPEC-34 — Pseudonimización de los nombres

## Qué problema resuelve

`F-146`: las sesiones delegadas de Claude Code anonimizan los nombres de personas por una
política de la organización que está fuera del repositorio. En `R4` el Entrevistador guardó
al destinatario como `[NOMBRE_ANONIMIZADO]`, el Planificador lo copió en el plan y la
cobertura rechazó las tres versiones: no hubo novela. No es estable —en las fichas que no
pasaron por el Entrevistador los nombres llegaron intactos—, y en una novela de verdad los
nombres **son** de personas reales, que es lo que la política protege. El autor decidió no
sortearla diciéndole al modelo que la ignore, sino que **los nombres reales no salgan**.

Es la segunda salvaguarda de privacidad que bloquea una función del producto, tras `F-91`, y
las dos van a la presentación como limitación declarada (`docs/proceso/trade-offs.md` `T-11`).

## Qué tiene que ser verdad al terminar

- **RF-01 · Los nombres entran fuera del modelo.** La entrevista (terminal y web) pide en
  campos propios el nombre del destinatario y el de cada elemento con nombre (mascotas,
  personas), y el harness los guarda sin que pasen por ningún agente. El Entrevistador
  trabaja con los pseudónimos. Cambia el flujo de `SPEC-25`.
- **RF-02 · El pseudónimo es un nombre inventado.** Verosímil, estable dentro de una obra,
  distinto de todos los nombres de la obra, de sus formas (`formas_de_nombre`) y de las
  vetadas. Un nombre real y su pseudónimo son una pareja guardada, no un cálculo que se
  repite.
- **RF-03 · Todo lo que sale va pseudonimizado.** Los prompts de los agentes que escriben o juzgan la novela (entrevistador, planificador, revisor del plan, escritor, editor, juez y resumidor), lo que
  devuelven las tools de la story bible (`SPEC-28`) y lo que sube a Langfuse (`SPEC-29`). La
  base guarda los nombres reales: la sustitución se hace en la frontera, en los dos sentidos.
- **RF-04 · Lo que vuelve se restituye, y lo que no se puede restituir falla a la vista.** El
  texto, el delta, el plan y la ficha que devuelve un agente se restituyen antes de guardarse
  y antes de cualquier validador. Un pseudónimo que aparezca con otra forma (un diminutivo,
  una variante) y no se pueda restituir exactamente es un **hallazgo**, no una sustitución
  aproximada ni un silencio.
- **RF-05 · Los validadores deterministas miran el texto restituido.** `INV-22` (nombres bien
  escritos) y las vetadas se comprueban sobre lo que leerá el destinatario, no sobre lo que
  escribió el modelo.
- **RF-06 · Se puede comprobar que no salió ningún nombre real.** Una prueba recorre lo
  enviado a los agentes y a Langfuse en una generación con dobles y no encuentra ninguno de
  los nombres reales de la ficha.

## Qué queda explícitamente fuera

- Un nombre real que el comprador escriba en el **texto libre** sin declararlo en un campo:
  sale tal cual y puede volver anonimizado. Se declara como punto ciego, no se detecta.
- Renombrar al destinatario (`PLAN-23` `C-4`) y lo que se conserva al entregar (`F-91`).
- Reescribir las bases ya generadas: las obras anteriores no se migran.
- Lean y TLA+: no leen nombres.

## Lo que la gobierna

`F-146`, `F-91`, `SPEC-25` (`RF-21`), `SPEC-28`, `SPEC-29`, `INV-22`, `T-11`; y el principio
de `docs/verification.md`: entre una aproximación que falla a la vista y otra que se ajusta
más y falla en silencio, la primera.

## Cuestiones abiertas para la aprobación

1. **Los nombres vetados** (`nombres_vetados` de la ficha) son de personas reales que el
   comprador no quiere en el libro, y hoy el Escritor los recibe en la lista para evitarlos.
   *Propuesta:* no se mandan; se comprueban solo sobre el texto restituido (`RF-05`). Coste:
   el Escritor no sabe qué evitar, y un veto que coincida por azar solo se caza después, con
   una reescritura.
2. **Los apellidos y los nombres compuestos** («Olivia Carranza»): ¿un pseudónimo para el
   nombre completo y otro para cada parte, o solo para el nombre completo? *Propuesta:* uno
   por cada forma que registre `formas_de_nombre`, para que «Olivia» sola también se
   sustituya.
3. **El inspector visual** (`INV-30`, `.claude/agents/inspector_visual.md`) recorre la web
   con Playwright, y la web enseña los nombres reales: es el octavo agente y el único que no
   recibe un prompt montado por el harness sino una página. *Propuesta:* la inspección se hace
   sobre una base de datos inventados, como la semilla de la lectura, y no sobre una obra real.
   Coste: `INV-30` deja de inspeccionar la novela entregada.
4. **La pantalla de la entrevista** (`SPEC-33`, de otra sesión). Hoy pinta tal cual la
   pregunta y la ficha del Entrevistador y reconstruye la conversación con
   `GET /entrevistas/{id}/turnos`. Con `RF-01` la conversación necesita un sitio donde pedir
   los nombres, y el historial tiene que decir qué se pidió fuera del modelo. La sesión del
   frontend pide revisar esa parte **antes de aprobar el plan**; el plan no se aprueba sin
   esa revisión.

