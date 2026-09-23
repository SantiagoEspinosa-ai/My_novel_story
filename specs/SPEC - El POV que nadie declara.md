---
id: SPEC-18
titulo: El POV que nadie declara, y qué hace un sin_veredicto
estado: aprobada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-18 — El POV que nadie declara

## Qué problema resuelve

En una generación real el modelo escribió la escena **sobre otro personaje del planificado**:
la escaleta pedía *"Marta recorre la casa heredada"* y el bloque inmutable exige *"tercera
persona limitada sobre Marta"*, y el texto salió sobre Ana. `INV-04` **no miró nada**
(`F-34`), y al hacer que dejara de callarse apareció la causa de fondo (`F-36`):

> `Docs/definitions.md` marca en negrita `Escena.pov`, `Escena.lugar` y `Borrador.pov_usado`.
> La tabla no guardaba los dos primeros y **nada rellena el tercero**. Ninguna prueba lo notó
> **porque la invariante que los necesita se saltaba en silencio**.

Es el mismo patrón que `F-29` con `F-31`: dos defectos que solo son visibles de uno en uno.

Y deja una pregunta que el proyecto no había respondido: **qué hace un `sin_veredicto`.**

---

## C-1 · `pov_usado` lo declara el agente en su respuesta

El contrato del Escritor lo exige, como ya exige el delta.

**No se deriva del texto**, y el motivo es la Regla 3: `VER-48` contrasta la señal
morfológica del texto **contra el `pov_usado` que declara el `Borrador`**. Si las dos salen
del mismo sitio, el validador se compara consigo mismo y deja de verificar nada.

## C-2 · El prompt dice qué POV se planificó

Hoy no se lo decimos, y **esa es la causa directa de que el modelo eligiera** — y eligiera
mal.

Es la Regla 4 entera: exigir en el contrato lo que el prompt no pide es pedir lo imposible,
y el rechazo sería merecido pero inútil. Las dos mitades o ninguna.

## C-3 · Un `sin_veredicto` no detiene la escena, pero impide cerrar el capítulo

*"No se pudo comprobar"* y *"se violó"* **no son lo mismo**, y hasta ahora el código los
trataba igual porque `sin_veredicto` heredaba la severidad de su invariante.

Tampoco puede pasar como éxito: `SPEC-10` C-2 ya decidió que **quien no se dejó auditar no
gana por defecto**.

El sitio exacto donde eso es verdad ya existe y es el de un `mayor`: **deja seguir la escena
e impide firmar el capítulo** (`SPEC-04` C-2). Obliga a resolverlo antes de cerrar, sin
detener una obra por un dato que falta.

**Esto no reclasifica ninguna invariante.** La severidad de `INV-04` sigue siendo
`bloqueante` para una violación confirmada; lo que cambia es qué hace el harness con un
hallazgo cuyo **estado** dice que no hubo juicio.

## C-4 · `Escena.pov` y `Escena.lugar` son obligatorios también en el esquema

El dominio los marca obligatorios y la tabla aceptaba nulo. Un esquema que permite lo que el
dominio prohíbe es una frontera que no lo es.

## Qué queda explícitamente fuera

- **`VER-48`**, el contraste morfológico. `C-1` le da la fuente independiente que necesitaba;
  escribirlo es otra cosa.
- **Reclasificar `INV-04`.** Ver `C-3`.
- **El resto de atributos obligatorios sin columna**, si los hubiera. Esta spec cierra los
  tres que `F-36` encontró.

### Migración

`escena.pov` y `escena.lugar` pasan a `NOT NULL`. Numerada y en el mismo commit.

## Qué gobierna esto

`Escena.pov`, `Escena.lugar`, `Borrador.pov_usado`, `INV-04` y `estado_de_hallazgo` de
`Docs/definitions.md`; `SPEC-04` C-2 y `SPEC-10` C-2; `F-34` y `F-36` de
`Docs/verification.md`; `VER-48`; y las Reglas 3 y 4.

## Preguntas respondidas al aprobar

| # | Pregunta | Respuesta |
| --- | --- | --- |
| 1 | ¿De dónde sale `pov_usado`? | Del agente, declarado. Derivarlo del texto sería un eco de `VER-48` |
| 2 | ¿El prompt dice el POV planificado? | Sí, y es la causa directa de `F-34` |
| 3 | ¿Un `sin_veredicto` detiene la escena? | No, pero impide cerrar el capítulo. No es una violación y tampoco gana por defecto |
| 4 | ¿`pov` y `lugar` obligatorios en el esquema? | Sí. El esquema no puede permitir lo que el dominio prohíbe |
