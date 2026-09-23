---
id: SPEC-24
titulo: Dónde se declara una analepsis, y quién la declara
estado: aprobada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-24 — Dónde se declara una analepsis, y quién la declara

> **Qué cuenta como aprobación aquí.** La decisión literal del autor:
> *«Mi decisión: declarar una analepsis es un acto del plan, no del texto. Va
> en `MomentoNarrativo`, rellenada desde la escaleta, igual que el POV y el
> cambio de valor. Si la declarara el Escritor en el delta, cualquier salto no
> intencionado se convertiría en analepsis declarada a posteriori y la
> invariante volvería a no comprobar nada por la otra puerta.»*

## Qué problema resuelve

`INV-08` dice que `t_fabula` es monótono dentro de una línea argumental
**salvo analepsis declarada**, y hoy **no hay dónde declararla**.
`MomentoNarrativo` tiene `t_fabula`, `t_discurso` y `duracion_ficcional`, y
ningún campo que diga *esto es deliberado* (`F-50`).

**Tener los dos ejes no puede bastar, y el motivo es lógico y no de
implementación.** Una analepsis *es* que `t_fabula` retroceda mientras
`t_discurso` avanza — que es exactamente la forma de la violación que `INV-08`
persigue. Si la declaración se dedujera de los dos instantes, sería
indistinguible de lo que la invariante busca, y `INV-08` dejaría de comprobar
nada.

La consecuencia de no resolverlo es de plazo corto y previsible. En terror la
analepsis es material del género —casi todo el miedo vive en la diferencia
entre fábula y discurso—, así que la primera obra con un salto temporal bien
hecho hará saltar la puerta de capítulo. Y entonces alguien concluirá que
`INV-08` da falsos positivos y la relajará, que es como se pierde una
invariante correcta.

## Quién declara, y por qué no el Escritor

La declaración es **un acto del plan**, no del texto: la rellena la escaleta,
igual que `pov` y que `cambio_de_valor`, y llega a la escena antes de que se
escriba una palabra.

**Si la declarara el Escritor en su delta, la invariante volvería a no
comprobar nada, esta vez por la otra puerta.** Cualquier salto temporal no
intencionado —el modelo se despista con las fechas— se convertiría en analepsis
declarada *a posteriori*: el mismo actor que comete la desviación sería quien
la autoriza, y no quedaría ninguna desviación posible. Una excepción que
declara quien la comete no es una excepción, es una amnistía.

Es el mismo razonamiento que ya gobierna `pov` y `pov_usado`: el plan declara
lo que la escena **debe** hacer, el delta declara lo que **hizo**, y la puerta
compara. Lo que aquí no existe es la mitad del plan.

## Qué tiene que ser verdad al terminar

1. `MomentoNarrativo` tiene un atributo que declara que el retroceso temporal
   es deliberado, definido primero en `Docs/definitions.md` y solo después
   dibujado en `Docs/domain-knowledge.md`.
2. Ese atributo lo rellena **la escaleta**, en el mismo momento y por el mismo
   camino que `pov` y `cambio_de_valor`. Ninguna ruta del Escritor lo escribe.
3. `INV-08` deja pasar la inversión cuyo evento posterior en el discurso lo
   lleva declarado, y sigue deteniendo todas las demás.
4. Una inversión declarada y una no declarada **se distinguen en el hallazgo**:
   hoy la puerta dice que toda inversión sale porque no hay dónde declararla, y
   ese texto deja de ser cierto en cuanto exista el campo.
5. La verificación formal de `specs/lean/` recibe el mismo dato y `L-1` lo
   respeta. Lean ya modela el campo (`Evento.analepsis`) y su fixture lo
   ejercita con una analepsis legítima que no debe marcarse; lo que falta es
   que el generador lo pueda leer de algún sitio.
6. Existe su migración, en el mismo commit que el cambio de atributo.

## Qué queda explícitamente fuera

- **Detectar una analepsis que el plan no declaró pero el texto sí narra.** Eso
  es comparar prosa con dato, y es un juez. `INV-08` sigue comparando dato con
  dato.
- **Decidir si la escaleta acierta.** Que el plan declare una analepsis no dice
  que sea buena idea: dice que es deliberada. Juzgar la estructura no es de
  esta invariante.
- **El nombre y el tipo del atributo.** Un booleano y una referencia a la
  escena de la que se retrocede son las dos formas obvias, y la segunda dice
  más. Se decide al escribir el plan de implementación.
- **Las otras tres invariantes de `specs/lean/`.** `L-2`, `L-3` y `L-4` no
  dependen de esto.

## Lo que la gobierna

`INV-08` de `Docs/definitions.md`; `MomentoNarrativo` y su atributo doble
`t_fabula` / `t_discurso`; la puerta de capítulo de `Docs/architecture.md`;
`F-50` y `F-47` de `Docs/verification.md`; y `L-1` de `specs/lean/README.md`,
que es la segunda fuente que hoy comprueba lo mismo por otro camino.
