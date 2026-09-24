# Trade-offs

Cada decisión con sus opciones, el criterio que las separó y la elección. La fuente
normativa va citada; si este resumen y la fuente discrepan, gana la fuente.

## T-01 · Un agente o varios

| | |
| --- | --- |
| **Opciones** | Un solo agente que planifica, escribe y se revisa. Varios agentes agrupados por fase. **Un agente por llamada, con contexto propio** |
| **Criterio** | Poder atribuir cada fallo a un agente concreto, y que quien juzga no juzgue su propio texto |
| **Elección** | Un agente por llamada (`A-03`), con el Juez y el Editor aislados del Escritor (`A-06`). `docs/architecture.md` diseña diez; siete tienen hoy su definición en `.claude/agents/`: entrevistador, planificador, revisor del plan, escritor, editor, juez y resumidor |
| **Lo que cuesta** | Medido en `PLAN-01` E5: **0,2508 $** por una escena de 325 palabras con un solo agente, y el desglose dice que lo caro es montar el contexto (9.476 tokens de creación de caché) y no escribir (1.188 de salida). Con `A-03` **cada agente paga su propia creación de caché** (`docs/architecture.md` § "Decisiones abiertas") |
| **Descartado** | Agrupar por fase: más barato, pero un fallo no se atribuye a nadie. Un solo agente: el sesgo de autoevaluación deja al juicio sin valor |

## T-02 · API o delegación en Claude Code

| | |
| --- | --- |
| **Opciones** | Llamar a la API con una clave. **Delegar cada agente en una sesión de Claude Code** (`claude -p`) |
| **Criterio** | Lo que hay: una suscripción, no una clave de API |
| **Elección** | Delegación (`SPEC-14`). El sobre JSON de cada sesión trae tokens y `total_cost_usd` reales |
| **Lo que cuesta** | El harness **no administra el contexto** de la sesión delegada: el límite de 100.000 tokens pasa a ser sobre lo que se manda, no sobre la ventana del otro lado (`CLAUDE.md` § "Límite de contexto") |

## T-03 · El formato de la story bible

| | |
| --- | --- |
| **Opciones** | Un fichero JSON (es lo que hace la rama `main`: `salida/biblia.json`). Una base relacional más un servicio de vectores aparte. **Una sola SQLite con `sqlite-vec`** |
| **Criterio** | Que cada hecho pueda decir en qué capítulos se usa y que el estado del mundo se reconstruya acumulando deltas en orden; y no añadir servicios |
| **Elección** | Una sola SQLite (`CLAUDE.md` § "SQLite con soporte vectorial"). Los usos de cada hecho viven en `uso_de_hecho` y la cronología en `evento_cronologico` (`SPEC-21`). La cola de trabajos va en la misma base (`A-05`) |
| **Descartado** | JSON: no se puede preguntar *«¿qué capítulos usan este hecho?»* sin leerlo entero. Servicio de vectores: una pieza más que desplegar para un volumen que SQLite aguanta |

## T-04 · El modelo de lectura

| | |
| --- | --- |
| **Opciones** | PDF con cambios pedidos desde fuera. **Web, con el cambio pedido desde la propia página**, y el PDF exportado aparte |
| **Criterio** | La regeneración selectiva se enseña mejor donde el lector la pide y ve qué capítulos cambiaron; y el enunciado exige el PDF de todas formas |
| **Elección** | Web (`SPEC-22`) más exportación a PDF de las versiones publicadas (`SPEC-27`). El PDF por versión, solo si sale gratis del diseño |

## T-05 · Qué es regenerar en una obra acumulativa

| | |
| --- | --- |
| **Opciones** | `S-1` cascada desde el punto tocado. `S-2` regenerar lo que usa el hecho y reverificar el resto. `S-3` aceptar solo cambios que no mueven el estado. `S-4` versión nueva en vez de editar la vieja. `S-5` no se puede tal como está |
| **Criterio** | No heredar un verde evaluado sobre otra obra (`D-1`), y conservar la versión anterior |
| **Elección** | `D-2` adopta `S-4`. Entre `S-1` y `S-2` decide **una medida con el umbral fijado antes de verla**: con un arrastre medio de unos dos capítulos, `S-1`; con unos ocho, `S-2` (`SPEC-23`, `en_revision`) |
| **Por qué el umbral va antes** | El sesgo conocido de la medida apunta a la baja, y un arrastre pequeño recomienda justo la salida más barata |

## T-06 · Cómo se integra TLA+ con el flujo real

| | |
| --- | --- |
| **Opciones** | Modelar lo que hace el código. **Modelar lo que dice el documento del flujo** |
| **Criterio** | Encontrar lo que una lectura no ve |
| **Elección** | Se modeló el documento, y eso destapó `CE-3`: la frase *«en orden»* implementada literalmente es un contador que reescribe la novela entera ante un cambio del lector (`specs/tla/README.md`) |
| **Pendiente** | ~~La especificación corresponde al flujo de la rama `main`, no a `backend/`.~~ **Hecho el 2026-09-24** (`EX-07`): el modelo nuevo, `specs/tla/HarnessBackend.tla`, modela `backend/` y la tabla de acción a función está rehecha contra él. La escalera de modelos desapareció con `main`; en su lugar hay seis topes con su contador cada uno |
| **Segunda elección, con `backend/`** | Esta vez se modeló **el código**, no un documento, pero con una regla que hace el mismo trabajo que modelar la frase: **un paso de TLA+ es una transacción de la base**, no una función. Donde el código escribe dos veces seguidas en dos `with con:`, el modelo tiene dos acciones y una caída puede caer entre ellas. Eso destapó `F-112`, que ninguna lectura de `ciclo.py` hace evidente porque las dos llamadas están en líneas contiguas. Y cada comportamiento dudoso es un interruptor (`BackendDeHoy.cfg` frente a `HarnessBackend.cfg`), así que el modelo corregido dice qué tiene que cumplir el arreglo sin tocar `backend/` desde la sesión de TLA+ |
| **Coste de la elección** | El modelo corresponde al código **de hoy**, y el código cambia en varias ramas a la vez. La regeneración (`PLAN-23`) se modela sobre el diseño aprobado, con su código a medio escribir en otra rama; la tabla del README dice qué acción existe hoy y cuál espera a qué paso |

## T-07 · Qué invariantes de Lean se priorizan

| | |
| --- | --- |
| **Opciones** | Las cuatro que el enunciado pone de ejemplo |
| **Criterio** | Que haya **dato real** del que puedan disparar |
| **Elección** | Las cuatro están escritas (`L-1`…`L-4`). `L-1` (orden de la fábula) y `L-3` (dos lugares a la vez) son las que **dispararon** sobre una base con el esquema real (`specs/lean/README.md` § "El caso real"); `L-2` (edad) necesita las fechas de nacimiento, que declara el plan (`SPEC-26` `RF-04`); `L-4` (aparecer tras un evento que excluye) **no puede disparar hoy**, porque nadie guarda en qué evento un personaje deja de poder aparecer (`F-46`). El enunciado pide dos |

## T-08 · Un capítulo rendido, ¿se publica?

| | |
| --- | --- |
| **Opciones** | Publicarlo con sus hallazgos visibles. **Bloquear la publicación** |
| **Criterio** | El del autor: **un capítulo que se rindió no es un capítulo que pasó** |
| **Elección** | Bloquea (`SPEC-30`). **Es una decisión nuestra, más estricta que el enunciado**, que no habla de rendición |

## T-09 · Qué sube a Langfuse

| | |
| --- | --- |
| **Opciones** | Todo, para que las trazas sean legibles. Solo medidas. **Medidas, scores y prompts del sistema como plantilla** |
| **Criterio** | `SPEC-25` `RF-21` borra la ficha al entregar, y lo que sale a Langfuse no lo borra nadie |
| **Elección** | No suben ni el contenido de las respuestas ni ningún dato del destinatario (`SPEC-29` § "El límite") |

## T-10 · Qué pueden hacer las tools

| | |
| --- | --- |
| **Opciones** | Contar como tools los JSON validados. Tools de lectura y escritura. **Tools de solo lectura** |
| **Criterio** | Que sean tools de verdad —el enunciado pide un span por llamada— sin abrir una segunda vía para escribir el estado |
| **Elección** | Tres tools de lectura de la story bible, solo para Escritor y Editor; el delta sigue siendo JSON (`SPEC-28`) |

## T-11 · La privacidad contra la personalización (limitación declarada)

| | |
| --- | --- |
| **Opciones** | Mandar los nombres reales a las sesiones delegadas. Pedir al modelo que ignore la política de anonimización. **Pseudonimizar en el harness**: los nombres salen como marcadores y se restituyen al volver |
| **Criterio** | El producto personaliza con nombres de personas reales, y eso es justo lo que protegen dos salvaguardas: la ficha se borra al entregar (`SPEC-25` `RF-21`) y la organización anonimiza los datos personales en las sesiones de Claude Code. Ninguna se sortea |
| **Elección** | Pseudonimización en el harness (`F-146`, decidida el 2026-09-24, pendiente de spec y plan). **Limitación declarada**: es la segunda vez que una salvaguarda de privacidad bloquea una función —la primera, `F-91`: una novela entregada no tiene destinatario con el que regenerar desde la web— y las dos se presentan como límite del sistema, no como detalle resuelto |
