---
id: SPEC-40
titulo: Ante los agentes, el destinatario es el protagonista de una ficción
estado: aplicada
aprobada_por: "autor del proyecto, en sesión: «b» (la opción B: no presentarlo como destinatario ante los agentes)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
fecha_aplicacion: 2026-09-25
commit_de_aplicacion: c5c7120
---

# SPEC-40 — El protagonista ante los agentes

## Qué problema resuelve

`SPEC-34` saca los nombres reales del modelo, y no basta. En la primera generación real en esta
máquina, el Planificador recibió el pseudónimo del destinatario y **lo escribió igualmente como
`[NOMBRE_ANONIMIZADO]`** en las tres rondas del plan. La cobertura rechazó las tres y no hubo
novela. El Entrevistador hizo lo mismo en una de sus preguntas. Los personajes que inventó el
Planificador y la mascota pasaron intactos: la política de la organización no mira si el nombre
es real, mira que sea **la persona que recibe el regalo**, y los prompts se lo dicen con todas
las letras («novela para regalar», «destinatario», «el comprador»).

El autor eligió **no presentarlo como destinatario ante los agentes** (la opción B) antes que
restituir la marca de anonimización (la A). Y, como con `SPEC-34`, sin decirle al modelo que
ignore la política.

## Qué tiene que ser verdad al terminar

- **RF-01 · Una sola vista de la ficha para los agentes.** Lo que ven de la ficha el Entrevistador,
  el Planificador y el Revisor lleva al destinatario como **`protagonista`**, y no lleva quién
  regala, la dedicatoria ni los nombres vetados (`SPEC-34` `RF-07`). La base sigue guardando la
  ficha tal cual; la vista se hace en la frontera.
- **RF-02 · Ningún prompt ni definición de agente habla del regalo.** Lo que se envía a los
  agentes del pipeline —y sus definiciones en `.claude/agents/`— describe **una novela
  personalizada y a su protagonista**: ni «destinatario», ni «regalo» o «regalar», ni
  «comprador», ni «dedicatoria». Al Entrevistador se le dice que habla con **quien encarga la
  novela**. Se excluye al inspector visual, que no escribe la novela: mira la web.
- **RF-03 · Lo que vuelve al agente también.** Las objeciones de la cobertura que se devuelven al
  Planificador nombran al «protagonista».
- **RF-04 · Lo que vuelve del agente se entiende.** Una ficha que el Entrevistador devuelve con
  `protagonista` se lee como `destinatario`.
- **RF-05 · Se comprueba.** Una prueba recorre todo lo que se envía a los agentes en una entrevista
  y una generación con dobles y no encuentra esas palabras; otra, las definiciones de los agentes.

## Qué queda explícitamente fuera

- Restituir `[NOMBRE_ANONIMIZADO]` (la opción A): el autor no la eligió.
- Saber sin gastar si basta: la política vive en el modelo. **Se comprueba con una prueba real
  barata, que decide el autor.**
- Cambiar lo que ve el comprador en la web: allí sigue siendo su regalo.

## Lo que la gobierna

`SPEC-34` (los nombres fuera del modelo), `F-146`, `SPEC-25`, `SPEC-26`.
