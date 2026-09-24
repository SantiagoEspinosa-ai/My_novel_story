---
id: SPEC-33
titulo: La novela regalo en la web — estantería, entrevista, generación en vivo y coste
estado: en_revision
aprobada_por: ""
fecha_aprobacion: ""
fecha: 2026-09-24
version: 2
---

> **v2 (2026-09-24):** el autor decide la confirmación de `RF-12` (la última generación, la
> referencia de 16,89 USD y lo gastado del techo) y descarta la imagen de portada. La cuestión 1
> pasa a ser qué techo aplica: hoy solo existe el de la evaluación. Las cuestiones 2 a 5 no
> cambian.

# SPEC-33 — La novela regalo en la web

> **Lo que el autor ya decidió en sesión, el 2026-09-24**, y esta spec recoge:
>
> - *«Sí, la web puede lanzar una generación. Con confirmación explícita que muestre lo que costó
>   la última —16,89 USD la novela de ejemplo— y lo gastado del techo. Sin ese paso, un clic
>   accidental cuesta el precio de una novela.»*
> - *«Sin imagen. La portada es el título y la dedicatoria, como en el dominio. En la estantería,
>   una tarjeta con tipografía cuidada y el color del tema vale igual y no abre un campo nuevo.»*
> - Sobre la paleta: *«Sigue con la provisional marcada como tal; con los tokens en un solo sitio
>   es cambiar un fichero.»*
>
> Lo que queda por decidir está en § "Cuestiones para la aprobación", cada cuestión con su
> propuesta. Hasta que este fichero diga `estado: aprobada` no hay plan.

## Qué problema resuelve

`SPEC-22` hace la lectura de una obra ya escrita y la petición de cambio. Lo que pasa **antes**
—quién es el destinatario, qué se acuerda con el comprador, cómo se escribe la novela— hoy solo
existe en la terminal: `entrevista_cli.py` y `novela_regalo.py`. En la web faltan cuatro cosas:

1. **No hay una puerta de entrada.** No se ven todas las novelas y no hay forma de empezar una.
2. **La entrevista no está en la web**, aunque sus endpoints por turno ya existen (`SPEC-25`).
3. **Una generación en curso se ve como una barra quieta.** `RF-60` de `SPEC-22` enseña la fase
   y el capítulo en curso, pero no los diez capítulos ni lo que el Editor dijo de cada uno.
   Para quien espera, el harness trabajando y el harness colgado se ven igual.
4. **El coste no se ve mientras se gasta**, y hoy no se podría enseñar: el coste de cada
   delegación **no se guarda en la base**. Llega a Langfuse (`SPEC-29`) y al libro de gasto de la
   evaluación, pero `traza_de_delegacion` no tiene ninguna columna de coste.

**Defecto documental encontrado al preparar esta spec.** El comentario de la rama de
`FalloDeTransporte` en `novela_regalo.py` dice que *«el coste de lo escrito vive en
`traza_de_delegacion»*, y no vive ahí. Se registra en `docs/verification.md` con el siguiente
`F-xx` libre en el momento del commit.

## Qué tiene que ser verdad al terminar

Los identificadores `RF-xx` son de esta spec y no se renumeran.

### La estantería

- **RF-01** — La página de inicio enseña **todas las obras** de la base, cada una en una tarjeta
  con su **portada** (título y dedicatoria, `SPEC-32`), el **nombre del destinatario** y su
  **estado**. La tarjeta es tipográfica, con el color del tema: **no hay imagen** y no se añade
  ningún campo a `Obra` (decisión del autor, arriba).
- **RF-02** — El estado de una obra lo da el backend a partir de su último `ProgresoDeGeneracion`,
  con los literales de `fase_de_generacion`. Una obra sin progreso dice **«sin generación»**, no
  una fase inventada. La interfaz no lo calcula (`CLAUDE.md`).
- **RF-03** — Si el destinatario ya no se puede leer, porque la ficha se borró, la tarjeta lo dice
  como dato ausente y sigue enseñando la dedicatoria, que sobrevive al borrado (`SPEC-32`).
- **RF-04** — Un botón **«Generar novela»**, visible y único en la página, abre una entrevista
  nueva.

### La entrevista como conversación

- **RF-05** — La entrevista se hace en la web como **una conversación**: una pregunta cada vez, y
  las preguntas y respuestas anteriores visibles encima. No es un formulario.
- **RF-06** — Lo que el backend devuelve en cada turno —lo que **falta**, los **avisos** y las
  **contradicciones**— aparece **en ese turno, dentro de la conversación**, no en un panel aparte
  ni al final.
- **RF-07** — Mientras el turno está en curso (`202` y un trabajo), la conversación lo dice. Si el
  trabajo falla, se enseña su motivo y la respuesta del comprador no se pierde.
- **RF-08** — Los hechos propuestos se confirman o se descartan desde la propia conversación
  (`SPEC-25`).
- **RF-09** — Cerrar la entrevista solo se ofrece cuando el backend dice `puede_cerrar`. Si el
  cierre devuelve `409`, se enseñan su motivo, lo que falta y las contradicciones, tal como vienen.
- **RF-10** — **La conversación sobrevive a recargar la página**: el historial de turnos es estado
  del backend, no de la página. Eso exige una clase nueva en `docs/definitions.md`, que va allí
  antes que el código (cuestión 2).

### Lanzar la generación

- **RF-11** — Una entrevista cerrada ofrece **lanzar la generación** de su obra. Lanzarla arranca
  un trabajo y devuelve su identificador; no bloquea (`CLAUDE.md`, llamadas asíncronas). Es el
  mismo pipeline de `SPEC-26` que corre `novela_regalo.py`, no una segunda copia.
- **RF-12** — **Lanzar gasta dinero, y la web pide una confirmación explícita antes.** Sin ese
  paso, un clic accidental cuesta el precio de una novela (decisión del autor, arriba). La
  confirmación enseña tres cifras, cada una con su procedencia a la vista:
  - **Lo que costó la última generación medida en esta base**, marcada como suelo si le falta
    alguna delegación, o **«sin medir»** si no hay ninguna.
  - **La referencia de la novela de ejemplo: 16,8905 USD en 36 delegaciones, todas con coste
    medido** (`R1`, `harness/evals/medidas.md`). Hoy esa cifra no está en la base: la web la
    enseña **como referencia con su fuente**, no como un coste de esta base.
  - **Lo gastado frente al techo** (cuestión 1).

  Una confirmación que no se puede leer sin haberla aceptado no cuenta: el botón que gasta no
  está disponible hasta que las cifras han cargado.
- **RF-13** — No puede haber dos generaciones de la misma obra en curso a la vez. La segunda
  petición recibe `409` con el motivo.

### La generación, visible

- **RF-14** — La página de una generación enseña **los capítulos en fila**, cada uno con su fase,
  que se refresca sola. La fase de cada capítulo la da el backend a partir de las filas de
  `ProgresoDeGeneracion`: cada cambio de fase ya añade una fila con su capítulo. Un capítulo al
  que todavía no se ha llegado se enseña como **no empezado**, que es la ausencia de una fase y no
  un valor nuevo de la enumeración.
- **RF-15** — Se enseñan **todas las fases de `fase_de_generacion`**, no solo planificando,
  escribiendo, editando y publicado. `parada` y `esperando_revision` tienen que verse, con su
  motivo; agruparlas con otras escondería justo lo que quien espera necesita saber (cuestión 3).
- **RF-16** — Al cerrarse un capítulo aparecen **sus seis notas del Editor** —criterio, nota,
  justificación e instrucción—, leídas de las `ValoracionDelEditor` del borrador vigente, y se
  marcan las que bajan del umbral que abre el hallazgo `INV-26`.
- **RF-17** — Se mantiene lo que `RF-60` de `SPEC-22` ya enseña: desde cuándo está en la fase y
  **«sin actividad desde hace N min»** pasado el umbral.

### El coste en vivo

- **RF-18** — **Cada delegación guarda su coste en la base** junto a su traza, también la del
  Planificador y la del Revisor. Es un atributo nuevo de la traza de delegación: se define primero
  en `docs/definitions.md` y lleva su migración en el mismo commit (`CLAUDE.md`).
- **RF-19** — Una delegación que no trae coste guarda **ausente, nunca cero**. En la web se lee
  **«sin medir»**, y el total, si alguna falta, se marca como **suelo** allí mismo, no en una
  nota al pie (la misma regla que `coste_es_suelo` de `SPEC-29`).
- **RF-20** — La página de la generación enseña un **contador discreto** con el coste acumulado y
  el número de delegaciones, que sube con cada delegación.
- **RF-21** — **El total de la web cuadra con el informe de `novela_regalo.py`** sobre la misma
  generación. Si no cuadra, uno de los dos cuenta mal, y la prueba lo tiene que cazar.

### Lo que atraviesa todo

- **RF-22** — Todo lo que se enseña usa los tokens de `shared/ui/tema` (`SPEC-22` `RF-59`): ningún
  color escrito fuera de allí. La paleta sigue siendo la provisional marcada como tal hasta que el
  autor pase la de Qaracter.
- **RF-23** — Cada ruta nueva entra en el contrato congelado en el mismo commit (`SPEC-22`
  `RF-33`), y el frontend se construye contra fixtures sacados de él.
- **RF-24** — Las páginas nuevas se inspeccionan en un navegador real con Playwright MCP, sobre
  una base con datos inventados (como `PLAN-22` E11–E13), sin gastar dinero.

## Qué queda explícitamente fuera

| Fuera | Por qué |
| --- | --- |
| **Una imagen de portada** | **Decisión del autor: sin imagen.** Para constancia, la tensión que había: los modelos de este proyecto escriben texto, no generan imágenes. Una portada SVG dibujada por un modelo abría un campo nuevo en `Obra` y un coste sin medir; un proveedor externo de imágenes salía de la delegación en Claude Code (`SPEC-14`) |
| La lectura de la obra y la petición de cambio | Son de `SPEC-22` / `PLAN-22`, y de `PLAN-23` |
| El texto libre de la entrevista | Sus endpoints existen. Queda fuera salvo que la cuestión 4 lo meta |
| Cerrar puertas desde la web | `A-04`, como en `PLAN-22` |
| Parar o reanudar una generación desde la web | Reanudar ya ocurre al relanzar (`F-38`, `F-67`). Un botón de parada es otra decisión |
| Streaming (SSE o WebSocket) | Se refresca por sondeo, con el intervalo en configuración. Cambiarlo a streaming no cambia ningún `RF` |
| Autenticación | El proyecto no la tiene (`SPEC-22` `D-1`) |
| Una generación real para verlo | Gasta dinero y necesita un sí explícito, igual que `PLAN-22` E20b |

## Lo que la gobierna

- `CLAUDE.md`: la interfaz muestra estado y no lo calcula; las llamadas al modelo son asíncronas
  (trabajo con identificador); las migraciones se versionan; una escena se muestra con su estado
  y sus hallazgos abiertos.
- `SPEC-22`: `RF-33` (el contrato congelado), `RF-59` (la identidad visual) y `RF-60` (el
  progreso), que esta spec amplía sin cambiar.
- `SPEC-25` (la entrevista y sus endpoints), `SPEC-26` (el pipeline de la novela regalo),
  `SPEC-29` (el coste y el suelo), `SPEC-32` (la dedicatoria de la obra).
- `INV-26` (el umbral de las notas del Editor), `A-04`.

## Cuestiones para la aprobación

Cada una lleva una propuesta. Aprobar la spec sin comentarios es aprobar las propuestas.

1. **Qué techo, y qué hace al tocarlo.** Hoy **el único techo de gasto que existe es el de la
   evaluación**: `evaluacion.techo_de_gasto_usd = 150` en `backend/config/sistema.json`
   (`SPEC-31`). Ninguno gobierna una generación lanzada desde la web. *Propuesta:*
   - **Un techo propio de las generaciones**, en `sistema.json` junto al de la evaluación y
     validado igual. Mezclar el gasto de la web con el de la evaluación haría que el uno se
     comiera el presupuesto del otro sin que nadie lo decidiera.
   - **Su valor lo pones tú.** No lo relleno: un techo es una decisión de presupuesto, no una
     medida. Hasta que lo pongas, la confirmación dice **«techo sin definir»** y no bloquea.
   - **«Lo gastado»** es la suma de los costes guardados en esta base (`RF-18`). Lo generado antes
     de `RF-18` no tiene coste guardado, así que la suma **sesga hacia abajo** y se enseña como
     suelo.
   - **Al tocar el techo**, si lo gastado ya lo alcanza, el botón que gasta **no está
     disponible** y se dice por qué.
2. **Dónde vive el historial de la entrevista.** *Propuesta:* una clase nueva en
   `docs/definitions.md` para el turno de entrevista (pregunta, tema, respuesta, avisos,
   contradicciones, cuándo), guardada con la entrevista y **borrada con la ficha**. El historial
   contiene datos personales del destinatario y no debe sobrevivir a la ficha que los justifica.
   La otra salida es no guardarlo y perder la conversación al recargar.
3. **Las fases que se enseñan.** *Propuesta:* las nueve de `fase_de_generacion` tal cual, con
   etiqueta de texto. No se agrupan en las cuatro que se pidieron.
4. **El texto libre.** *Propuesta:* fuera en esta versión. La conversación es por turnos, y el
   texto libre es otro modo de entrada con su propia validación de longitud.
5. **El intervalo de refresco.** *Propuesta:* en configuración del frontend, con 2 s por defecto.
   Es parametrizable y no bloquea.
