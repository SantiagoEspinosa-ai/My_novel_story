# Verificación — My_novel_story

2026-09-21 · @Santiago Espinosa Domínguez

Cómo se prueba que **el sistema** hace lo que dice que hace. Este documento no
evalúa la novela que el sistema escribe: de eso se ocupan las invariantes
`INV-01`…`INV-16`, que aquí son el objeto verificado, no el sujeto.

Generado con la skill `verification-plan` (`.agents/skills/verification-plan/`)
a partir de la semilla de contexto que se lista abajo.

## Qué se verifica aquí

Hay dos preguntas que se confunden con facilidad y este documento responde solo
a la segunda:

| Pregunta | Quién la responde |
| --- | --- |
| ¿Es buena la novela? ¿Da miedo? ¿Se sostiene la continuidad? | Las invariantes `INV-01`…`INV-16` de `Docs/definitions.md`, ejecutadas por el harness |
| ¿Están bien implementadas esas invariantes, el presupuesto de contexto, la máquina de estados y los agentes? | **Este documento** |

Dicho de otro modo: `INV-05` dice que ninguna escena se da por buena sin su
delta aplicado. Que esa regla exista es dominio. Que el código la cumpla de
verdad, y que falle cuando debe fallar, es lo que se planifica aquí.

Cubre los dos niveles del marco de referencia: **nivel artefacto** (¿es correcto
el código?) y **nivel proceso** (¿se comportan los agentes de forma fiable?), en
secciones separadas.

## Semilla de contexto

| Documento | Qué afirmaciones aporta |
| --- | --- |
| `CLAUDE.md` | Stack, presupuesto de 100.000 tokens y su reparto, reglas de Pydantic y enumeraciones, reglas de persistencia |
| `AGENTS.md` | Precedencia entre documentos, reglas de uso del modelo de dominio, estabilidad de identificadores |
| `Docs/definitions.md` | Las dieciséis invariantes con su nivel y severidad, los vocabularios controlados, la política de casos negativos |
| `Docs/domain-knowledge.md` | La máquina de estados de la escena y la secuencia de generación |
| `Docs/architecture.md` | Reglas de dependencia entre features, contrato de los agentes, cola de trabajos, reglas de presentación del frontend |

Si la semilla cambia, este plan cambia. Una fila cuyo origen desaparezca del
documento de partida se marca obsoleta, no se borra.

## Resumen de cobertura

| Clase | Afirmaciones | Cubiertas hoy |
| --- | --- | --- |
| T — Test | 18 | 0 |
| A — Analysis | 12 | 0 |
| I — Inspection | 1 | 0 |
| D — Demonstration | 0 | 0 |
| U — Unverifiable | 6 | — |
| **Total** | **37** | **0** |

**Cero cubiertas, y es el dato correcto.** No existen todavía `backend/`,
`frontend/` ni `harness/`, y `CLAUDE.md` dice literalmente que aún no hay build
ni tests. Este documento es el plan, no el informe. No hay ningún porcentaje de
cobertura de código aquí porque no se ha medido ninguno.

## Nivel artefacto — ¿es correcto el código?

| ID | Afirmación | Origen | Clase | Metodología | Criterio de salida | Dónde vive | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VER-01 | Ningún esquema Pydantic tiene un campo que no esté en `Docs/definitions.md` | `CLAUDE.md` § FastAPI | A | static analysis | Un comprobador recorre los esquemas y los contrasta con las fichas de clase; cero campos huérfanos | `harness/esquema/` | pendiente |
| VER-02 | Un valor fuera de un vocabulario controlado es error de validación, no aviso | `CLAUDE.md` § FastAPI | T | unit testing | Cada enumeración rechaza un valor inventado con error de validación | `commons/dominio/tests/` | pendiente |
| VER-03 | El endpoint de generación no bloquea: devuelve un identificador de trabajo | `CLAUDE.md` § FastAPI | T | integration testing | La respuesta llega antes de que termine la generación y trae un identificador consultable | `features/generacion/tests/` | pendiente |
| VER-04 | Un trabajo encolado sobrevive a un reinicio del servidor | `Docs/architecture.md` § Persistencia | T | integration testing | Se encola, se mata el proceso, se levanta, y el trabajo sigue ahí y se completa | `commons/trabajos/tests/` | pendiente |
| VER-05 | Ninguna llamada al modelo supera los 100.000 tokens, salida incluida | `CLAUDE.md` § Límite de contexto | T | property-based testing | Para cualquier estado generado, el contexto ensamblado más la reserva de salida cabe en el límite | `features/contexto/tests/` | pendiente |
| VER-06 | Cuando no cabe, se recorta por el nivel de menor prioridad, nunca truncando por el final | `CLAUDE.md` § Límite de contexto | T | property-based testing | Ningún recorte parte un bloque por la mitad, y el nivel inmutable nunca se toca antes que los resúmenes | `features/contexto/tests/` | pendiente |
| VER-07 | Nunca se manda el texto completo de la obra al modelo | `CLAUDE.md` § Límite de contexto | T | unit testing | Con una obra de muchas escenas, el contexto ensamblado no contiene el texto de ninguna escena salvo la anterior | `features/contexto/tests/` | pendiente |
| VER-08 | El texto completo de una escena se guarda pero no se recupera por similitud | `CLAUDE.md` § SQLite | T | integration testing | La búsqueda vectorial solo devuelve fichas, resúmenes y presagios; nunca una fila de texto completo | `commons/db/tests/` | pendiente |
| VER-09 | El estado del mundo se reconstruye acumulando deltas en orden, sin releer el texto | `CLAUDE.md` § SQLite | T | property-based testing | Para cualquier secuencia de deltas, reconstruir desde cero da el mismo estado que aplicarlos incrementalmente | `features/consolidacion/tests/` | pendiente |
| VER-10 | Ninguna escena pasa a `consolidada` sin su delta aplicado (`INV-05`) | `Docs/definitions.md` § Invariantes | T | unit testing | Intentar consolidar sin delta aplicado falla; la escena siguiente no se puede generar | `features/consolidacion/tests/` | pendiente |
| VER-11 | `bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y dejan seguir | `CLAUDE.md` § Reglas de trabajo | T | unit testing | Un hallazgo de cada severidad produce exactamente el comportamiento declarado, no uno decidido caso por caso | `commons/invariantes/tests/` | pendiente |
| VER-12 | Todo hallazgo cita su invariante por identificador, nunca por descripción | `CLAUDE.md` § Reglas de trabajo | A | static analysis | Todo `Hallazgo` construido lleva un identificador del registro `INV-xx`; no hay ninguno con texto libre | `commons/invariantes/` | pendiente |
| VER-13 | Una feature nunca importa de otra feature, salvo `orquestacion/` | `Docs/architecture.md` § Backend | A | static analysis | Un comprobador de importaciones falla el build ante cualquier import cruzado no autorizado | CI | pendiente |
| VER-14 | `commons/` nunca importa de una feature | `Docs/architecture.md` § Backend | A | static analysis | Mismo comprobador; la flecha va en un solo sentido | CI | pendiente |
| VER-15 | Los `Enum` de los vocabularios controlados viven solo en `commons/dominio/` | `Docs/architecture.md` § Backend | A | static analysis | No hay ninguna definición de `Enum` de dominio fuera de esa carpeta | CI | pendiente |
| VER-16 | El frontend nunca accede a la base de datos ni calcula estado de dominio | `CLAUDE.md` § React | A | static analysis | El frontend no tiene dependencia de ningún cliente de base de datos; toda la lógica de dominio llega resuelta por la API | CI | pendiente |
| VER-17 | Un módulo del frontend solo importa de capas FSD estrictamente inferiores, sin cross-imports entre slices | `Docs/architecture.md` § A-09 | A | static analysis | El comprobador de FSD pasa sin violaciones | CI | pendiente |
| VER-18 | Una escena nunca se muestra sin su estado y sus hallazgos abiertos | `CLAUDE.md` § React | T | unit testing | El componente de escena no renderiza texto si falta el estado o la lista de hallazgos | `frontend/.../tests/` | pendiente |
| VER-19 | Un dato sin medir se muestra "sin medir", nunca como cero | `Docs/architecture.md` § Frontend | T | unit testing | Con el valor ausente, la interfaz pinta "sin medir"; con el valor cero, pinta cero | `frontend/.../tests/` | pendiente |
| VER-20 | El Escritor devuelve texto y delta en la misma respuesta | `Docs/architecture.md` § Agentes | T | contract testing | Una respuesta sin delta, o con delta fuera de esquema, se rechaza sin llegar a las puertas | `features/generacion/tests/` | pendiente |
| VER-21 | Todo cambio de un atributo obligatorio en `Docs/definitions.md` lleva su migración en el mismo commit | `CLAUDE.md` § SQLite | A | CI/CD integration | Un commit que toque un atributo obligatorio sin añadir migración falla en CI | CI | pendiente |
| VER-22 | Cada invariante `INV-01`…`INV-16` tiene al menos un caso de prueba negativo | `Docs/definitions.md` § Invariantes | A | mutation testing | Un comprobador cuenta casos negativos por identificador y falla si alguno está a cero | `harness/` | pendiente |
| VER-23 | Ningún identificador publicado se reutiliza ni se renumera | `AGENTS.md` § Reglas de uso | A | static analysis | El conjunto de identificadores solo crece; lo retirado queda marcado obsoleto, no borrado | CI | pendiente |

## Nivel proceso — ¿se comportan los agentes de forma fiable?

| ID | Afirmación | Origen | Clase | Metodología | Criterio de salida | Dónde vive | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VER-24 | Cada llamada de agente deja una traza consultable después del hecho | `Docs/architecture.md` § Agentes | T | runtime observability / tracing | Toda llamada emite traza con agente, escena, niveles de contexto enviados y tokens reales; se comprueba en el visor de trazas, no leyendo variables de entorno | `commons/modelo/` | pendiente |
| VER-25 | El Juez no recibe el prompt ni el razonamiento del Escritor | `Docs/architecture.md` § A-06 | T | unit testing | El contexto que llega al Juez contiene texto y rúbrica, y nada del prompt del Escritor | `features/verificacion/tests/` | pendiente |
| VER-26 | El Juez no aprueba sistemáticamente lo que una persona rechaza | `Docs/architecture.md` § A-06 | T | evals | Existe una medición publicada de concordancia entre Juez y persona sobre un conjunto de escenas. **El umbral se fija después de la primera medición, no antes** | `harness/evals/` | pendiente |
| VER-27 | La salida de cada agente valida contra su esquema tipado, o se rechaza | `Docs/architecture.md` § Agentes | T | guardrails | Una salida fuera de esquema no llega nunca a la capa siguiente; se rechaza y se registra | `commons/modelo/` | pendiente |
| VER-28 | No existe ningún camino de `planificada` a `consolidada` que no pase por `en_verificación` | `Docs/domain-knowledge.md` § Ciclo de vida | A | model checking | Exploración exhaustiva de la máquina de estados: ningún camino alcanzable salta la puerta | `features/orquestacion/tests/` | pendiente |
| VER-29 | La aceptación de una escena la ejecuta una persona, nunca el worker | `Docs/architecture.md` § A-04 | T | human-in-the-loop review | El worker no tiene ninguna ruta de código que lleve una escena a `aceptada` | `features/orquestacion/tests/` | pendiente |
| VER-30 | El Escritor no viola las reglas de la amenaza cuando se le empuja a hacerlo | `Docs/definitions.md` § `INV-10` | I | red-teaming / adversarial testing | Una tanda de prompts adversarios documentada, con sus resultados, revisada por una persona | `harness/adversarial/` | pendiente |
| VER-31 | Los cambios generados por agente pasan por la misma tubería que los escritos a mano | `Docs/architecture.md` § Pruebas | A | CI/CD integration | No hay ninguna ruta que publique cambios saltándose CI | CI | pendiente |

**Progressive rollout y sandboxed execution no aplican hoy** y por eso no tienen
fila. La primera porque hay un solo usuario y una sola obra, así que no hay
tráfico que repartir; la segunda porque ningún agente ejecuta código. Si alguna
de las dos cosas cambia, hay que añadir su fila.

## No verificable hoy

| ID | Afirmación | Qué falta exactamente | Decisión abierta que lo desbloquea |
| --- | --- | --- | --- |
| VER-32 | La distancia estilométrica a las anclas se mantiene bajo umbral (`INV-15`) | Medir la distancia sobre un corpus de referencia y fijar el número con esa medición | `Docs/definitions.md` § Decisiones abiertas → **"Umbrales"** |
| VER-33 | La varianza de la curva de dread supera el mínimo fijado (`INV-16`) | Lo mismo: primero medir, después fijar | `Docs/definitions.md` § Decisiones abiertas → **"Umbrales"** |
| VER-34 | Cada agente cabe en su parte del presupuesto de contexto | Instrumentar el consumo por agente durante varias escenas y repartir con esos números | `Docs/architecture.md` § Decisiones abiertas → "Reparto de tokens por agente" |
| VER-35 | Cuando el Juez marca `INV-03` y la regla de continuidad no ve nada, gana el correcto | La decisión de quién gana | `Docs/definitions.md` → "Desempate juez vs. regla", y su reflejo en `Docs/architecture.md` |
| VER-36 | El coste por escena es sostenible para una obra completa | Coste real de una escena con la decisión `A-03` (una llamada por agente) | Ninguna. Nace aquí, y hay que abrirla |
| VER-37 | El reparto por niveles de `CLAUDE.md` basta para una escena real | Ensamblar el contexto de una escena real y ver si los niveles caben o hay que reajustarlos | Ninguna. Nace aquí, y hay que abrirla |

Seis filas `U` sobre treinta y siete. Cinco de las seis esperan una medición
—`VER-35` espera una decisión, no un número— y **ninguna lleva un umbral
provisional**, porque un umbral inventado que queda escrito deja de distinguirse
de uno medido.

### `VER-32` y `VER-33` son la decisión "Umbrales", no un problema aparte

Conviene no perderlo de vista: la decisión abierta **"Umbrales"** de
`Docs/definitions.md` dice que las invariantes `menor` (`INV-15` e `INV-16`)
necesitan números concretos antes de poder ejecutarse, y que sin ellos *el
harness las salta en silencio*. `VER-32` y `VER-33` son exactamente eso mismo
visto desde aquí. **Son una sola decisión con dos fichas, y se resuelven a la
vez o no se resuelven.**

Quien cierre "Umbrales" en `Docs/definitions.md` tiene que cerrar `VER-32` y
`VER-33` en el mismo commit, y al revés. Si se resuelven por separado acaba
pasando lo peor de los dos mundos: un número fijado en un documento que el otro
sigue dando por pendiente, o dos números distintos para la misma comprobación.

Las otras tres filas que esperan medición no están cubiertas por esa decisión.
`VER-34` tiene la suya en `Docs/architecture.md`; `VER-36` y `VER-37` **no
tienen ninguna todavía** y aparecen abajo para que se abran.

## Casos negativos

Toda fila de clase `T` necesita una entrada que la viole a propósito. Una regla
que nunca ha fallado en las pruebas no está verificada, solo declarada.

| ID | Caso negativo | Qué debe cazarlo |
| --- | --- | --- |
| VER-02 | `rol_dramático = "narrador"`, que no está en la enumeración | Validación del esquema |
| VER-03 | Un generador que tarda mucho más que el tiempo de respuesta del endpoint | El test comprueba que la respuesta llega igualmente |
| VER-04 | Matar el proceso con un trabajo a medias | El worker lo retoma al arrancar |
| VER-05 | Un estado del mundo con cientos de entidades vivas | El ensamblador recorta en vez de desbordar |
| VER-06 | Un contexto que excede por poco, con el nivel inmutable al máximo | Se recorta `Resúmenes` antes que `Inmutable`, y ningún bloque queda partido |
| VER-07 | Una obra con cuarenta escenas consolidadas | El contexto no contiene el texto de la escena 3 |
| VER-08 | Una consulta de similitud cuyo vecino más próximo sea un texto completo | La consulta no puede devolverlo: no está indexado |
| VER-09 | Una secuencia de deltas con un movimiento y una muerte en el mismo `t` | Reconstrucción total y reconstrucción incremental coinciden |
| VER-10 | Consolidar una escena cuyo delta no se ha aplicado | La transición se rechaza |
| VER-11 | Un hallazgo `mayor` en una escena por lo demás correcta | La escena sigue; el hallazgo queda abierto y visible |
| VER-18 | Una respuesta de la API sin la lista de hallazgos | El componente no renderiza el texto |
| VER-19 | Un contador de tokens ausente frente a uno con valor cero | "sin medir" en el primero, `0` en el segundo |
| VER-20 | Una respuesta del Escritor con texto y sin delta | Se rechaza antes de las puertas |
| VER-24 | Una llamada que falla con excepción | También deja traza |
| VER-25 | Un contexto de Juez al que se le cuela el prompt del Escritor | El test lo detecta |
| VER-26 | Una escena mala que el Escritor considera buena | Se mide si el Juez la aprueba |
| VER-27 | Una salida del modelo con un campo de más | Se rechaza y se registra |
| VER-29 | El worker intentando llevar una escena a `aceptada` | No existe tal ruta; el intento no compila o falla |

## Orden de implantación

Primero lo que corta la propagación del error, después lo barato, al final lo
caro:

1. **VER-10, VER-11, VER-28** — la máquina de estados y las puertas. Mientras
   esto no esté, cualquier fallo se hereda en todas las escenas siguientes.
2. **VER-13, VER-14, VER-15, VER-16, VER-17, VER-23** — los comprobadores de
   estructura. Son análisis estático: se escriben una vez y no vuelven a pedir
   atención.
3. **VER-02, VER-20, VER-27** — los contratos de datos. Baratos y cazan mucho.
4. **VER-05, VER-06, VER-07, VER-09** — el presupuesto de contexto y los
   deltas, con pruebas basadas en propiedades. Es donde vive el riesgo real de
   que el sistema no escale.
5. **VER-24, VER-03, VER-04** — trazas y trabajos asíncronos.
6. **VER-22, VER-26, VER-30** — mutación, evals y red-teaming. Los más caros, y
   los que no tienen sentido hasta que haya código que probar.

## Decisiones abiertas

- [ ] **Qué comprobador de importaciones** se usa para VER-13, VER-14 y VER-15.
- [ ] **Qué herramienta de FSD** cierra VER-17.
- [ ] **Qué conjunto de escenas** sirve de corpus para los evals de VER-26.
- [ ] **Quién revisa** el red-teaming de VER-30 y cada cuánto.
- [ ] **Dónde viven las trazas** de VER-24 y quién las mira.
- [ ] **Umbrales de `INV-15` e `INV-16`** (`VER-32`, `VER-33`). Es la misma
      decisión "Umbrales" abierta en `Docs/definitions.md`: se cierran las tres a la
      vez o ninguna.
- [ ] **Coste por escena** (`VER-36`). Decisión nueva, abierta también en
      `Docs/architecture.md`.
- [ ] **Suficiencia del reparto por niveles** (`VER-37`). Decisión nueva,
      abierta también en `Docs/architecture.md`.
- [ ] Las seis filas `U`: cinco necesitan su medición y una una decisión antes
      de poder pasar a `T`.
