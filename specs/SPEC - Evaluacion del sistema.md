---
id: SPEC-31
titulo: Evaluación del sistema — cinco briefs, tuning, revisión humana y red-team
estado: aprobada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-23
fecha: 2026-09-23
version: 2
---

> **Historial.** v1: redactada con la decisión del autor sobre el presupuesto
> (2026-09-23), con `O-1` y `O-2` abiertas y tres propuestas. v2: el autor decide
> qué se ajusta y quién revisa, y confirma las tres propuestas. Sin cuestiones
> abiertas.

# SPEC-31 — Evaluación del sistema

## Qué problema resuelve

`EXAMEN.md` pide cinco briefs de prueba —al menos uno adversarial, con injection
en el texto libre, y uno diseñado para provocar una incoherencia temporal—, una
tabla por brief con los validadores que pasaron y los que fallaron, una
iteración de tuning con antes y después, la revisión humana de una novela
completa con la misma rúbrica del LLM-as-judge, y un red-team log. Y cierra:
*«un proyecto sin evals con resultados medibles… no aprueba»*.

Hoy hay **un brief de cinco** (`harness/evals/brief-incoherencia-temporal.json`,
sin ejecutar), `harness/adversarial/` está declarada y no existe, y `VER-30`
está sin implementar. Son `EX-05` y `EX-06` de `docs/cobertura-examen.md`.

## El presupuesto es una decisión, no un requisito

**Techo: 150 USD** para todas las ejecuciones de esta spec. Lo fija el autor como
**decisión de presupuesto**; el enunciado no pone ninguno.

Lo que hay que saber para leerlo: **el coste de una novela con el pipeline actual
está sin medir**. La única cifra, 21,6 USD (`harness/evals/medidas.md`), es de la
obra anterior: 54 escenas, una escalera de modelos y sin Editor ni Planificador.
No se sabe en qué dirección sesga: había más texto por capítulo, pero ahora hay
más agentes por capítulo. **No sirve como estimación**, y por eso el techo se
comprueba contra lo gastado, no contra una previsión.

## Qué tiene que ser verdad al terminar

- **RF-01.** Existen **cinco briefs** con datos inventados, ninguno de una persona
  real. Entre ellos, **uno de injection** en el texto libre y **el temporal**, que
  ya existe.
- **RF-02.** Cada brief se ejecuta de principio a fin y deja una fila en **una
  tabla por brief**, con una columna por validador y su resultado: pasó, falló,
  no aplica o sin veredicto. **Un brief que no llegó a ejecutarse dice «sin
  ejecutar»**, no se rellena.
- **RF-03.** **Una iteración de tuning**: un cambio, los mismos briefs antes y
  después, y los resultados de las dos pasadas con la versión de prompt que
  produjo cada una (`SPEC-29` `RF-05`). **Un resultado plano o peor se informa
  tal cual**: un resultado negativo es un resultado válido; lo que no vale es un
  resultado inventado.
- **RF-04.** **Revisión humana** de una novela completa con la rúbrica del Editor
  (`SPEC-26` `RF-09`: nota de 1 a 5 y justificación por criterio), comparada
  criterio a criterio con las notas del Editor sobre la misma novela. Es la
  medida con la que `SPEC-26` `RF-10` ajusta el umbral de reescritura.
- **RF-05.** **Un red-team log**: cada caso adversarial probado, qué validador lo
  detectó o que no lo detectó ninguno, y cómo se resolvió.
- **RF-06.** Si el gasto acumulado alcanza el techo, las ejecuciones se detienen y
  la tabla dice qué quedó sin ejecutar.
- **RF-07.** Los resultados de cada ejecución llegan a Langfuse como scores
  (`SPEC-29`).

### Resuelto por el autor (v2)

- **RF-08 (antes `O-1`). El tuning ajusta el prompt del Escritor**, y se mide con
  **la nota del Editor por criterio**, antes y después, sobre los mismos briefs.
  Queda dicho su punto ciego: el Editor juzga los dos lados, así que una mejora
  que solo le guste a él parecería real. La revisión humana (`RF-04`) es la otra
  fuente contra la que se contrasta.
- **RF-09 (antes `O-2`). La revisión humana la hace el autor del proyecto.**
- **RF-10 (antes `P-1`). Los tres briefs que faltan:** uno base, que es también el
  brief de ejemplo del README y el que produce `/ejemplos/novela-ejemplo.pdf`; uno
  que provoque contradicciones en la entrevista; y uno que intente colar palabras
  vetadas por variantes (acentos, plurales).
- **RF-11 (antes `P-2`). La revisión humana se hace sobre la novela del brief
  base.**
- **RF-12 (antes `P-3`). Casos del red-team log**, además de la injection: evadir
  las vetadas con variantes, y exfiltración de datos entre dos novelas. Vive en
  `harness/adversarial/`, la carpeta que `docs/architecture.md` § "El harness"
  declara para eso.

## Qué queda explícitamente fuera

- La validación visual con el browser MCP: `EX-04`, espera al frontend.
- TLC, que se ejecuta en desarrollo.
- Los documentos de `/docs` que resumen estos resultados: `EX-11`.

## Lo que la gobierna

`EXAMEN.md` § "Evaluación del sistema", §5b y § `/docs` (red-team log);
`SPEC-26` `RF-09` y `RF-10`; `SPEC-29`; `SPEC-30`; `VER-30`;
`docs/architecture.md` § "El harness"; `harness/evals/`.
