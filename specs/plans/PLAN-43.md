---
id: PLAN-43
spec: SPEC-43
titulo: La lectura es para el lector
estado: aprobada
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo lo demás»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-43

### L1 · El título del capítulo (`RF-02`)

`docs/definitions.md`: `Capitulo` gana `titulo`, opcional, que sale del plan aprobado. No se añade columna: no es un atributo obligatorio y el plan ya lo guarda. `features/lectura` lo lee de `plan_de_obra`, del último plan aprobado de la obra, por id de capítulo. `CapituloDelIndice` y `CapituloLeido` llevan `titulo: str | None`. Se regenera el contrato.

**Prueba que falla primero:** `test_el_capitulo_lleva_el_titulo_del_plan_aprobado`, y `test_sin_plan_el_titulo_es_nulo`.

### L2 · La lectura sin nada técnico (`RF-01`, `RF-02`, `RF-03`)

`entities/escena` gana `TextoDeEscena`: solo el texto, o «todavía no está escrito». `pages/capitulo`, `pages/escena` y `pages/indice` lo usan en lugar de `EscenaConEstado`, y dejan de pintar las etiquetas de estado. El título pasa a «Capítulo N · título». Al pie del capítulo va `NavegacionEntreCapitulos` (anterior, siguiente e índice), sacada del índice de la misma versión.

**Pruebas que fallan primero:** `Capitulo › no enseña estado ni hallazgos`, `Capitulo › el título es Capítulo N y el del capítulo`, `Capitulo › navega al anterior, al siguiente y al índice`, `Escena › el título no es el id`, `Indice › no enseña estados`. Las pruebas que pedían estado y hallazgos en la lectura se reescriben (`VER-18` pasa a la administración).

### L3 · La administración enseña cada escena con su estado y sus hallazgos (`RF-04`)

`pages/historia-de-obra` gana una tercera pestaña, «Escenas» (`?vista=escenas`): cada capítulo con sus escenas en `EscenaConEstado` sin texto, leídas del índice de la obra.

**Prueba que falla primero:** `HistoriaDeObra › la pestaña Escenas enseña el estado y los hallazgos de cada escena`.

### L4 · `docs/` (`RF-05`)

`CLAUDE.md` § React: la distinción entre lectura y administración. `VER-18` se actualiza a dónde vive ahora la regla. `AGENTS.md`. La spec pasa a `aplicada`.
