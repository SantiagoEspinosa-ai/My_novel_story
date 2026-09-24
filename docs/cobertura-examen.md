# Cobertura del enunciado — `EXAMEN.md` contra los documentos

Registro de los huecos entre lo que exige `EXAMEN.md` y lo que recogen los documentos del
proyecto. **No introduce requisitos**: cada fila cita el enunciado por un lado y el
documento o el código por el otro. Lo que decide cómo cerrar un hueco va en una spec, no
aquí.

## Cómo se lee

**Qué es un hueco**, en las dos direcciones:

- **De documentación**: el enunciado lo exige y ningún documento lo recoge, o un documento
  da por decidido algo que lo contradice. Se cierran corrigiendo el documento; si cerrarlo
  exige decidir algo, espera a esa decisión.
- **De sistema**: está documentado y el código no lo hace. Se registra aquí y va a plan.

**Un mínimo del enunciado no es un techo.** Pedir tres roles y tener diez no es un hueco;
tampoco lo es tener más invariantes de Lean de las que pide, ni que `L-4` no pueda disparar
(`F-46`) mientras otras dos sí puedan.

**Bloqueante** quiere decir que, tal como está documentado, un requisito del enunciado no se
puede cumplir, o que el hueco cae en la frase final del enunciado: *«un proyecto sin evals
con resultados medibles, o sin documentación de proceso en `/docs`, no aprueba»*.

Las líneas citadas de `EXAMEN.md` y del resto son las del 2026-09-23. Las citas por
identificador (`SPEC-22` `RF-53`) no caducan; las de línea sí.

## Vueltas

| Vuelta | Fecha | Huecos encontrados | Cerrados en la vuelta | Esperan decisión | De sistema |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-23 | 15 | 3 (`EX-08`, `EX-10`, `EX-12`) | 9, todos bloqueantes | 3 |
| 2 | 2026-09-23 | 2 nuevos (`EX-16`, `EX-17`) | 0; 6 pasan a sistema al aprobarse sus specs (`EX-01`, `02`, `03`, `05`, `06`, `09`) | 2 (`EX-16`, `EX-17`) | 3 + 6 |
| 3 | 2026-09-24 | **0 nuevos** | 1 (`EX-11`), y una corrección de este registro (`EX-15`) | 2 (`EX-16`, `EX-17`), las mismas de la vuelta 2 | 3 + 6 |

Cada vuelta se detiene en lo que haya que decidir. La 1 se paró en nueve decisiones; la 2, en dos.

**Bloqueantes al cerrar la vuelta 3, que es la última según el procedimiento**: `EX-04`
(espera a la lectura web), `EX-07` (de la sesión de TLA+), `EX-16` y `EX-17` (esperan
decisión). La 3 no encontró ninguno nuevo, pero **la condición de parada no se cumple**: pide
cero bloqueantes.

**Después de la vuelta 3** (2026-09-24): el autor decide `EX-16` y `EX-17`, que recoge
`SPEC-32`. Quedan bloqueantes **`EX-04`** y **`EX-07`**, y ninguno espera una decisión: el
primero, a la lectura web; el segundo, a la sesión de TLA+.

## Identificadores reservados

Reservados el 2026-09-23 antes de escribir, según `docs/sesiones-concurrentes.md`. El más alto publicado en todas las ramas era `SPEC-26`.

| Spec | Para | Estado |
| --- | --- | --- |
| `SPEC-27` | Exportar a PDF, y corregir la fila de `SPEC-22` §1.2 (`EX-09`) | `aprobada` el 2026-09-23; `PLAN-27` `aprobada`, **sin código** |
| `SPEC-28` | Las tools de los agentes, con schema (`EX-01`) | `aplicada`; `PLAN-28` aplicado salvo E10, la ejecución real |
| `SPEC-29` | Observabilidad en Langfuse (`EX-02`) | `aprobada` el 2026-09-23; `PLAN-29` `aprobada`, con E1–E11 commiteados y E12–E14 sin cerrar. **Nada ha llegado nunca a una instancia real** |
| `SPEC-30` | La puerta de publicación, con Lean (`EX-03`) | `aplicada`; `PLAN-30` `aplicada`. La puerta **no se ha alcanzado nunca** en una generación real |
| `SPEC-31` | Evaluación: cinco briefs, tabla, tuning, revisión humana y red-team (`EX-05`, `EX-06`) | `aprobada` el 2026-09-23; `PLAN-31` `aprobada`: **E1–E14 con dobles hechos, sin ninguna ejecución real** (R0–R7, H1 y T1 pendientes, y gastan) |
| `SPEC-32` | La dedicatoria en `Obra` y la extensión preguntada (`EX-16`, `EX-17`) | `aplicada`; `PLAN-32` `aplicada` |

## Huecos de documentación

| ID | Enunciado | Documento o código | Tipo | Estado |
| --- | --- | --- | --- | --- |
| **EX-01** | §3, `EXAMEN.md:36`: *«Tools con schema validado»*; §6, `:99`: *«cada llamada a tool aparece como span»* | Todos los agentes del pipeline declaran `tools: []` y el hook de policy niega cualquier herramienta (`docs/architecture.md` § "Los hooks de Claude Code"; `PLAN-26` E11, `:229`–`:242`). El sistema no tiene tools | Contradicción | **Documentado en vuelta 2**: lo recoge `SPEC-28`, `aprobada` el 2026-09-23. **Cerrado en código** por `PLAN-28` E1–E9: tres tools de lectura con schema de entrada y salida, servidor MCP propio, allowlist por agente y cada llamada como span enlazado a su delegación (`VER-88`..`VER-93`). Falta verlas en una ejecución real (`PLAN-28` E10, gasta dinero) |
| **EX-02** | §3 `:38` coste por novela vía Langfuse; §5 `:48` cada validador envía un score; §6 `:98`–`:102` entero; §7 `:111` cada coincidencia en Langfuse | Solo aparece para excluirlo: `SPEC-26` *«Langfuse… Es la spec de observabilidad»* (`:178`), `SPEC-25` (`:211`), `PLAN-25` (`:249`), `PLAN-26` (`:270`). Esa spec no existe. La traza propia (`docs/architecture.md` § "La traza de una llamada al modelo") guarda tokens, no los envía. Código: ninguna mención | Ausencia | **Documentado en vuelta 2**: lo recoge `SPEC-29`, `aprobada` el 2026-09-23. Deja de ser hueco de documentación y **pasa a hueco de sistema**: va a su plan |
| **EX-03** | §5 `:48` *«gate antes de publicar una versión»*; §5c `:72` Lean automático, *«si falla, la versión no se publica y el fallo vuelve al editor»* | `SPEC-26` lo aplaza a *«la spec de la puerta de publicación»* (`:108`, `:181`), que no existe. `specs/lean/` devuelve 0/1/2, pero **nada del backend lo llama**: `lean`, `lake` y `generar_lean` solo aparecen en comentarios | Ausencia | **Cerrado en código (2026-09-24)**: `PLAN-30` E1–E12. La puerta corre sola al acabar la novela, con Lean dentro; lo sostienen `VER-81` a `VER-87`. Queda la ejecución real de E14, que gasta dinero |
| **EX-04** | §5a `:57` validación visual vía browser MCP; § "Claude Code" `:159` un servidor MCP de browser en la configuración; `:160` su uso real documentado en `/docs` | `SPEC-26` lo deja fuera (`:185`). Ningún documento menciona MCP, y no hay fichero de configuración MCP en el repositorio | Ausencia | **Bloqueante, sin decisión pendiente**: Playwright MCP (decidido el 2026-09-23). Ningún documento normativo lo recoge todavía, y no puede recogerlo con sentido antes que la lectura web: **espera a `EX-13`** **Medio cerrado por `PLAN-22` E12–E13 (2026-09-24):** `.mcp.json` con un solo servidor, Playwright MCP (`:159`), y su uso real sobre la lectura web documentado en `docs/proceso/claude-code.md` § Browser MCP, con lo que detectó y lo que cambió (`:160`, `VER-109`). La otra mitad de §5a, el validador con nombre, punto del harness y score, **existe desde `PLAN-22` E13b**: `INV-30`, el agente `inspector_visual`, en la puerta de publicación tras publicar, con un score `INV-30.<pieza>` por comprobación (`VER-119`). ❌ **Lo que sigue sin hacer** es que el error visual *«vuelva al writer»*: el hallazgo queda abierto para una persona (`SPEC-22` `RF-58`, fuera) |
| **EX-05** | §5b `:62` revisión humana de una novela completa con la misma rúbrica | Solo como medida del umbral de `SPEC-26` `RF-10` (`:96`), y fuera de su alcance (`:183`). Ningún documento dice quién la hace, sobre qué novela ni dónde queda | Ausencia | **Documentado en vuelta 2**: lo recoge `SPEC-31`, `aprobada` el 2026-09-23. Deja de ser hueco de documentación y **pasa a hueco de sistema**: va a su plan **Vuelta de `PLAN-31`**: las seis notas del Editor ya se guardan por versión de borrador (E4, `VER-123`); la comparación con el autor (`comparar.py`, H1) y la revisión misma siguen sin hacer |
| **EX-06** | § "Evaluación del sistema" `:92`–`:94`: cinco briefs (uno de injection, uno temporal), tabla por brief, una iteración de tuning con antes y después; § `/docs`: red-team log | `harness/evals/README.md` tiene **uno de cinco** (`brief-incoherencia-temporal.json`, sin ejecutar). `harness/adversarial/` está declarada en `docs/architecture.md` § "El harness" y no existe; `VER-30` está obsoleta. `SPEC-26` lo deja fuera (`:183`) | Ausencia | **Documentado en vuelta 2**: lo recoge `SPEC-31`, `aprobada` el 2026-09-23. Deja de ser hueco de documentación y **pasa a hueco de sistema**: va a su plan **Vuelta de `PLAN-31`**: los cinco briefs existen y cargan (`VER-120`), la tabla se genera en `harness/evals/resultados.md` y hoy dice «sin ejecutar» en todo (`VER-121`), el red-team vive en `harness/adversarial/` (`VER-126`) y encontró una fuga entre novelas (`F-100`). **Hueco de sistema abierto**: no hay ninguna ejecución, ni el tuning |
| **EX-07** | §5d `:87` *«La especificación debe corresponder al código: el README explica qué estado o transición del código implementa cada acción»* | `specs/tla/README.md` § "Qué implementa cada acción" (`:83`) modela *«el flujo por capítulos de `main`»* y cita `src/config.py`, `src/servidor.py` y `EJECUCION.md`, que **no están en este árbol**. El pipeline de la novela regalo vive en `backend/` | Contradicción | **Bloqueante. Decidido (2026-09-23)**: el entregable es `backend/`. Hay que rehacer la tabla de acción a código y el modelo, y la escalera `haiku → sonnet → opus` de `Reintentar` desaparece porque `backend/` usa un modelo por agente (`backend/config/sistema.json`). **Va a plan y es de la sesión de TLA+**, no de este registro |
| **EX-08** | §5d, la regeneración por cambio del lector forma parte del flujo | `specs/tla/README.md` `D-2` decía que no existía en ningún documento; ya la describían `SPEC-22` `RF-50`..`RF-55` y `SPEC-23` | Obsoleto | **Cerrado** en la vuelta 1: `D-2` dice ahora qué specs la describen |
| **EX-09** | § "Novela de ejemplo" `:132`: *«Si el formato de lectura elegido es web, se incluye igualmente el PDF exportado»* | `SPEC-22` §1.2, fila *«Publicar la obra a un formato de libro»* en **No entra** (`:85`). `SPEC-22` está `aprobada` | Contradicción | **Documentado en vuelta 2**: lo recoge `SPEC-27`, `aprobada` el 2026-09-23. Deja de ser hueco de documentación y **pasa a hueco de sistema**: va a su plan |
| **EX-10** | § "Los repositorios deben incluir también": README con brief reproducible, `.env.example`, `ejemplos/novela-ejemplo.pdf`, vídeo en `presentacion/`, `.claude/` con memoria y comandos, configuración MCP | Ningún documento los recogía | Ausencia | **Cerrado** en la vuelta 1 como rutas reservadas en `AGENTS.md` § "Todavía no existe". Crearlos es trabajo, no documentación. Qué memoria se commitea (hoy vive fuera del repositorio) se decide al crearla |
| **EX-11** | § `/docs` `:134`: carpeta `/docs` con seis documentos de proceso —spec inicial, trade-offs, explainers, diagramas, registro de iteraciones y red-team log—, más skills y subagentes referenciados desde allí | `Docs/` era **normativa**, no de proceso, y en git se llamaba `Docs`: en Windows `Docs/` y `docs/` son la misma carpeta, así que no podían convivir. Ningún documento recoge los seis | Contradicción de nombre y ausencia | **Cerrado en la vuelta 3**: nombre, 2026-09-23; los seis documentos más el de Claude Code, en `docs/proceso/`. Lo que esos documentos no pueden contar todavía —resultados de evaluación, tuning, red-team contra el modelo real— dice *sin ejecutar* y va con `SPEC-31`, que es hueco de sistema |
| **EX-12** | Todo el enunciado: novela para regalar, diez capítulos | `AGENTS.md` describía el proyecto como *«novelas largas (caso base: terror, una sola obra)»* | Obsoleto | **Cerrado** en la vuelta 1 |
| **EX-16** | §2 `:24` *«Una portada con dedicatoria personalizada»* | `docs/definitions.md` pone `dedicatoria` en `FichaDeEntrevista`, y `SPEC-25` `RF-21` **borra la ficha al entregar**. `SPEC-22` `RF-46` dice que es atributo de `Obra` —todavía no está en `docs/definitions.md`— y que *«la escribe una persona»*. Ningún documento dice que la de la entrevista pase a `Obra` antes del borrado: después de entregar, la portada se quedaría sin ella | Contradicción entre dos specs aprobadas | **Cerrado en código (2026-09-24)**: `PLAN-32` E1–E7. Lo sostienen `VER-78`, `VER-79` y `VER-80` |
| **EX-17** | §1 `:13`: el entrevistador *«recoge los datos del destinatario: nombre, edad, rasgos, recuerdos, género, tono y extensión»* | `SPEC-25` `RF-03`: *«La extensión no se pregunta: son 10 capítulos de entre 1.000 y 1.500 palabras… La ficha la registra»*. Y el código contradice a su spec: `backend/app/commons/dominio/destinatario.py:24`, *«la extension no se pregunta ni se guarda en la ficha»* | Contradicción | **Cerrado en código (2026-09-24)**: `PLAN-32` E1–E7. Lo sostienen `VER-78`, `VER-79` y `VER-80` |

## Huecos de sistema

Documentados y sin código. Van a plan; ninguno se cierra aquí.

| ID | Enunciado | Qué dice el documento | Qué hace el código | Va a |
| --- | --- | --- | --- | --- |
| **EX-13** | §2 lectura interactiva: índice, fichas con enlaces, portada con dedicatoria, cambio del lector | `SPEC-22`, `aprobada` | `frontend/` no existe; `backend/app/features/lectura/` cubre una parte | Un `PLAN-22`, que no existe. `SPEC-22` ya lo permite |
| **EX-14** | §2 `:30` *«se conserva la versión anterior»*; §5d invariante de versiones | `SPEC-22` `RF-53` y `SPEC-23` `D-2`: versión nueva con identidad propia (`F-43`, `CE-5`) | Hasta `PLAN-23` A3, ninguna versión de obra en el código. Desde A3, `version_de_obra` y `capitulo_de_version` con disparadores que impiden cambiar una versión creada, y `VER-114` que lo prueba | **Cerrado en lo que exige el enunciado** (`PLAN-23` A3, A5): la versión anterior se conserva y se lee entera por `GET /obras/{id}/versiones/{numero}`. Lo que sigue abierto es **qué escribe** una regeneración, que espera a la medida (`SPEC-23` v2, `S-1` o `S-2`; `SPEC-22` `DA-1`) |
| **EX-15** | §5c `:73` un caso **real** en que Lean detecta lo que los otros no | `specs/lean/README.md` § "El caso real" ejecuta Lean sobre *«una base… sembrada con una obra de cuatro eventos»* | Nada falla: falta una generación. `L-1` lo caza también `INV-08` desde `b2f097c`. `L-2` sigue siendo solo de Lean (`edades()` no tiene llamadas fuera de sus pruebas). `L-3` solo en parte: `INV-02` cubre la accesibilidad escena a escena, y lo que queda solo en Lean es la comparación entre escenas del mismo momento (`specs/lean/README.md`). **Corregido en la vuelta 3**: la vuelta 1 decía que `L-3` era solo de Lean | Ejecutar `harness/evals/brief-incoherencia-temporal.json` cuando exista `EX-03` |
