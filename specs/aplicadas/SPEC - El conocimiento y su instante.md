---
id: SPEC-17
titulo: El conocimiento inicial y el instante en que se evalúa t
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: d77cc40
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-17 — El conocimiento y su instante

## Qué problema resuelve

`SPEC-16` arregló un punto muerto y, al ejecutar, apareció **el mismo patrón un nivel más
abajo**. Dos veces, y las dos sobre la misma tabla:

- **`F-32`** — El `RegistroDeConocimiento` arranca vacío, así que **ninguna acción es posible
  en la primera escena de una obra**. Un personaje llega a la escena 1 sabiendo cosas de
  antes del relato —Ana heredó la casa— y no hay dónde declararlo. El plan declara qué hechos
  existen (`SPEC-15`) y **no quién los sabe ya**.
- **`F-33`** — La puerta verifica **antes** de consolidar, así que lo que la escena revela no
  está en el registro cuando `INV-03` mira. **Aprender y actuar en la misma escena bloquea
  siempre**, y es el caso narrativo más común que existe: Marta encuentra la llave y abre el
  sótano.

Las dos son la misma pregunta en dos instantes: **cuándo cuenta que alguien sabe algo.** Una
en el instante cero y otra dentro de la escena. Por eso van juntas.

---

## C-1 · El conocimiento inicial lo declara la `Escaleta`

`Escaleta` gana `conocimiento_inicial[]`, con la forma `{sujeto, hecho, grado}`.

`SPEC-15` ya decidió que el plan declara **qué hechos existen**; quién los sabe al empezar es
material del mismo plan y por el mismo argumento: un dato que nace al escribirse es un dato
que nadie planificó, y entonces no se puede comprobar que la novela entregue lo que se
propuso.

## C-2 · Va en el `RegistroDeConocimiento`, no en una tabla aparte

Con `desde_escena` marcando **anterior al relato**, no una escena.

Una tabla aparte duplicaría la pregunta *"quién sabe qué"* en dos sitios, y la copia que
alguien olvidara actualizar sería justo la que `INV-03` leyera. **La corrección de una
duplicación no es mantener las dos copias sincronizadas: es no tener dos.**

`desde_escena` es hoy `NOT NULL`, así que esto **necesita su migración versionada**.

## C-3 · Lo anterior al relato lleva su propia `fuente`

`RegistroDeConocimiento.fuente` gana un valor para *anterior al relato*.

Sin él, la decisión abierta que `SPEC-16` dejó sobre la fuente —una invariante que exija que
enterarse de algo tenga una explicación— **nacería ya incumplida** por las entradas
iniciales, que no tienen escena de origen porque preceden al texto.

## C-4 · Lo que la escena revela cuenta para las acciones de esa misma escena

`INV-03` evalúa contra el registro **más las revelaciones del delta que está juzgando**.

`INV-03` dice *"no conoce en `t`"*, y **`t` dentro de una escena no es un punto, es un
intervalo**. Enterarse y obrar en el mismo intervalo es lo normal, no la excepción.

Su enunciado no cambia y su severidad tampoco.

## C-5 · Lo que esto le quita a `INV-03`, dicho en voz alta

Con `C-4`, a un personaje le basta **declarar la revelación** para poder actuar. La
invariante deja de poder distinguir *"lo sabía"* de *"acaba de decir que lo sabe"*.

**Se acepta, y se declara como punto ciego.** La defensa real no es esta invariante: es la
de la **fuente** que `SPEC-16` dejó abierta, porque ahí es donde se comprueba que enterarse
tenga una explicación en el texto.

La alternativa sería **ordenar los beats dentro de la escena** y comprobar que la revelación
precede a la acción. Es lo único que detectaría *"actuó antes de enterarse"* dentro de una
misma escena, cuesta bastante más, y **queda escrito aquí para que quien lo necesite sepa
que se consideró y por qué no se hizo**.

## Qué queda explícitamente fuera

- **La invariante de la fuente.** Sigue abierta desde `SPEC-16`; `C-3` solo evita que nazca
  incumplida.
- **El orden intra-escena.** Ver `C-5`.
- **Reabrir `INV-03`.** Ni enunciado ni severidad cambian.

### Migración

Sí, y es la primera del proyecto que no es gratis: `conocimiento.desde_escena` pierde su
`NOT NULL`. Va numerada y en el mismo commit.

## Qué gobierna esto

`RegistroDeConocimiento`, `Escaleta` e `INV-03` de `Docs/definitions.md`; `F-32` y `F-33` de
`Docs/verification.md`; `VER-64`, que no tendrá dato utilizable hasta que esto se aplique; y
la Regla 5, de la que `F-33` es una instancia dentro del propio arreglo de `SPEC-16`.

## Preguntas respondidas al aprobar

| # | Pregunta | Respuesta |
| --- | --- | --- |
| 1 | ¿Dónde se declara el conocimiento inicial? | En la `Escaleta`, junto a los `HechoCanonico` |
| 2 | ¿Registro o tabla aparte? | El `RegistroDeConocimiento`, con `desde_escena` anterior al relato. No se tienen dos copias |
| 3 | ¿Qué `fuente` lleva? | Un valor propio, o la invariante de la fuente nace incumplida |
| 4 | ¿En qué instante se evalúa `t`? | Lo que la escena revela cuenta para las acciones de esa escena: `t` es un intervalo |
| 5 | Con la 4, `INV-03` pierde filo. ¿Se acepta? | Sí, y se declara como punto ciego. La defensa es la invariante de la fuente |
