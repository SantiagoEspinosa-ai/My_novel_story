# Explainers

Uno por concepto del curso aplicado. Breves: qué es, dónde se aplica aquí y en qué
estado está. **Estado** dice lo que hay hoy, no lo que está previsto.

## Harness engineering

**Qué es.** Tratar el sistema que rodea al modelo —contexto, roles, validadores, reintentos,
memoria— como el producto, y al modelo como una pieza que falla de formas conocidas.
**Aquí.** El modelo escribe; el harness decide si lo escrito entra. Cada capítulo pasa por
puertas deterministas y por el Editor antes de aceptarse, y su delta se aplica antes del
siguiente para cortar la propagación del error (`CLAUDE.md` § "Reglas de trabajo").
**Estado.** Construido y probado; la primera ejecución real no pasó del capítulo 1.

## Spec-Driven Development

**Qué es.** Decidir qué tiene que ser verdad antes de escribir el código, y que el código
se juzgue contra eso. **Aquí.** Tres puertas en cadena —spec aprobada, plan aprobado,
código con TDD— con el estado en el frontmatter de cada fichero (`AGENTS.md`). Una spec dice
qué problema resuelve, qué tiene que ser verdad y qué queda fuera, nunca cómo.
**Estado.** Aplicado desde el primer día: ver [`spec-inicial.md`](spec-inicial.md).

## TDD

**Qué es.** Primero la prueba que falla, después el código mínimo que la pasa. **Aquí.** Es
la misma exigencia que el proyecto pone a las invariantes: *una regla que nunca ha fallado
en las pruebas no está verificada, solo declarada*. **Estado.** 625 pruebas en verde el
2026-09-23.

## Multi-agente y aislamiento del juez

**Qué es.** Repartir el trabajo en roles con contexto propio para poder atribuir los fallos
y evitar que alguien juzgue su propio texto. **Aquí.** Un agente por llamada (`A-03`); el
Juez y el Editor se lanzan desde un directorio sin `CLAUDE.md`, aislados del Escritor
(`A-06`, `F-20`). Ver `T-01` en [`trade-offs.md`](trade-offs.md). **Estado.** Construido.

## Ingeniería de contexto y memoria por niveles

**Qué es.** Decidir qué entra en el contexto de cada llamada, con un presupuesto, en vez de
mandar todo. **Aquí.** Seis niveles —inmutable, estado actual, local, recuperado,
resúmenes y salida— que suman 100.000 tokens, recortados por el nivel de menor prioridad y
nunca por el final (`CLAUDE.md` § "Límite de contexto"). Nunca se manda la novela entera al
modelo. **Estado.** Construido; el reparto está **sin ejercitar**, porque ninguna escena
real se ha acercado al techo, y el contexto de verdad enviado está sin medir (`F-58`).

## Story bible y reconstrucción por deltas

**Qué es.** Guardar el estado del mundo como hechos estructurados y reconstruirlo sumando
lo que cambia cada escena, en vez de releer el texto. **Aquí.** Cada escena devuelve texto
y delta; el estado se reconstruye acumulando deltas en orden. Cada hecho registra en qué
capítulos se usa y de qué forma (`SPEC-21`). **Estado.** Construido.

## Recuperación por similitud

**Qué es.** Traer al contexto lo más parecido a lo que se va a escribir, con embeddings.
**Aquí.** `sqlite-vec` dentro de la misma SQLite, sobre fichas de entidad, resúmenes de escena y
setups pendientes; el texto completo de las escenas se guarda pero no se recupera por similitud.
**Estado.** Construido.

## Validadores deterministas frente a LLM-as-judge

**Qué es.** Lo que se puede comprobar con código no se le pide a un modelo; el modelo juzga
lo que solo se puede juzgar. **Aquí.** Longitud, nombres exactos, palabras vetadas e
imprescindibles son código (`INV-17`, `INV-21`…`INV-24`); continuidad, tono, arco, ritmo y
personalización natural los puntúa el Editor de 1 a 5 con justificación (`INV-26`,
`INV-27`). Ver [`diagramas.md`](diagramas.md) § "Validadores". **Estado.** Construido.

## Guardrails y policy

**Qué es.** Reglas que se aplican en código, fuera del modelo, y dejan rastro. **Aquí.**
Palabras vetadas en tres niveles —global, franja de edad y novela— con normalización de
mayúsculas, acentos, plurales y género; si aparece una, el capítulo vuelve al Escritor con
tope, y cada decisión queda en el audit log (`SPEC-25`). **Estado.** Construido y probado
por nivel y por variante.

## Contenido no confiable y prompt injection

**Qué es.** Tratar el texto que pega el usuario como datos, nunca como instrucciones.
**Aquí.** El texto libre viaja en un sobre delimitado que no se puede cerrar desde dentro,
solo produce hechos que el comprador confirma, y nunca llega al Escritor (`SPEC-25`,
`VER-68`). **Estado.** Construido y probado con un doble; sin probar contra el modelo real
(ver [`red-team-log.md`](red-team-log.md)).

## Hooks

**Qué es.** Scripts que Claude Code ejecuta en momentos fijos de una sesión. **Aquí.** Uno
de validación del capítulo al terminar el Escritor, y otro de policy antes de cada
herramienta, solo sobre las delegaciones del pipeline (`SPEC-26` `RF-17`..`RF-19`).
**Estado.** Construidos. En la primera ejecución real no dejaron constancia, porque Claude
Code solo los carga desde la raíz del repositorio (`F-61`); cerrado en `1ad5691`, y en la
segunda ejecución real ya se ejecutan. El de policy es desde `SPEC-28` una allowlist por agente.

## Skills y subagentes

**Qué es.** Instrucciones empaquetadas que el agente carga cuando la tarea lo pide, y
agentes con definición propia. **Aquí.** Ver [`claude-code.md`](claude-code.md).

## Reintentos con límite y rendición

**Qué es.** Volver a intentar lo que falla, con tope, y decidir qué pasa al agotarlo.
**Aquí.** Topes por tipo de fallo; al agotarlos, una escena se rinde solo si no queda
ninguna invariante `bloqueante` abierta, y un capítulo rendido **no se publica** (`SPEC-30`,
decisión nuestra). **Estado.** Reintentos y rendición construidos; la puerta de publicación,
aprobada y sin construir.

## Checkpoint y reanudación

**Qué es.** Poder retomar tras un fallo sin rehacer ni perder trabajo. **Aquí.** El bucle
salta lo que ya está hecho y lo dice (`F-38`). TLA+ enseñó que un checkpoint tiene que
guardar la decisión que provocaron los intentos, no solo el contador (`CE-4`).
**Estado.** Construido.

## Observabilidad

**Qué es.** Poder ver qué hizo cada llamada, cuánto costó y qué versión de prompt la
produjo. **Aquí.** Una traza propia por delegación, con dos campos de tokens de fuentes
independientes (`VER-41`); Langfuse con un límite de qué sube (`SPEC-29`). **Estado.** La
traza propia existe; **Langfuse está aprobado y sin construir**.

## Verificación formal de la historia: Lean 4

**Qué es.** Convertir los hechos temporales en proposiciones que un demostrador comprueba.
**Aquí.** Desde la SQLite se genera un fichero Lean con eventos, momentos, presencias y
fechas de nacimiento, y cuatro invariantes (`L-1`…`L-4`) devuelven 0, 1 o 2 —«sin
veredicto» no es «aprobado»— (`specs/lean/`). **Estado.** Funciona fuera del pipeline;
enchufarlo a la puerta de publicación es `SPEC-30`.

## Model checking del sistema: TLA+

**Qué es.** Describir el harness como máquina de estados y dejar que TLC recorra todas las
ejecuciones de un modelo pequeño. **Aquí.** Cinco capítulos y dos intentos; cinco
invariantes de seguridad más `TypeOK`, y dos propiedades temporales —`VersionesSoloCrecen`
y `Terminacion`, la de vivacidad—; cinco contraejemplos documentados
(`specs/tla/`). **Estado.** Verificado sobre el flujo de la rama `main`; rehacerlo contra
`backend/` está decidido y pendiente (`EX-07`).

## Evals y red-teaming

**Qué es.** Medir el sistema entero contra briefs fijos, y buscar a propósito cómo romperlo.
Son dos preguntas distintas con dos corpus distintos (`docs/architecture.md` § "El
harness"). **Aquí.** Cinco briefs, tabla por brief, una iteración de tuning y un red-team log
(`SPEC-31`). **Estado.** Aprobado; uno de los cinco briefs escrito y **ninguno ejecutado**.
