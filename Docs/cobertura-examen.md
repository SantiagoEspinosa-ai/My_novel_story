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

La vuelta 1 se detuvo en las decisiones, como pide el procedimiento: no hay vuelta 2 hasta
que se tomen.

## Huecos de documentación

| ID | Enunciado | Documento o código | Tipo | Estado |
| --- | --- | --- | --- | --- |
| **EX-01** | §3, `EXAMEN.md:36`: *«Tools con schema validado»*; §6, `:99`: *«cada llamada a tool aparece como span»* | Todos los agentes del pipeline declaran `tools: []` y el hook de policy niega cualquier herramienta (`Docs/architecture.md` § "Los hooks de Claude Code"; `PLAN-26` E11, `:229`–`:242`). El sistema no tiene tools | Contradicción | **Bloqueante. Espera decisión**: qué tools tiene el sistema y quién las llama |
| **EX-02** | §3 `:38` coste por novela vía Langfuse; §5 `:48` cada validador envía un score; §6 `:98`–`:102` entero; §7 `:111` cada coincidencia en Langfuse | Solo aparece para excluirlo: `SPEC-26` *«Langfuse… Es la spec de observabilidad»* (`:178`), `SPEC-25` (`:211`), `PLAN-25` (`:249`), `PLAN-26` (`:270`). Esa spec no existe. La traza propia (`Docs/architecture.md` § "La traza de una llamada al modelo") guarda tokens, no los envía. Código: ninguna mención | Ausencia | **Bloqueante. Necesita spec** |
| **EX-03** | §5 `:48` *«gate antes de publicar una versión»*; §5c `:72` Lean automático, *«si falla, la versión no se publica y el fallo vuelve al editor»* | `SPEC-26` lo aplaza a *«la spec de la puerta de publicación»* (`:108`, `:181`), que no existe. `specs/lean/` devuelve 0/1/2, pero **nada del backend lo llama**: `lean`, `lake` y `generar_lean` solo aparecen en comentarios | Ausencia | **Bloqueante. Necesita spec**: qué bloquea una versión y cómo vuelve el fallo al Editor |
| **EX-04** | §5a `:57` validación visual vía browser MCP; § "Claude Code" `:159` un servidor MCP de browser en la configuración; `:160` su uso real documentado en `/docs` | `SPEC-26` lo deja fuera (`:185`). Ningún documento menciona MCP, y no hay fichero de configuración MCP en el repositorio | Ausencia | **Bloqueante. Espera decisión**: qué servidor (el enunciado admite Chrome MCP, Playwright MCP o similar). Depende de `EX-13`: sin lectura web no hay qué inspeccionar |
| **EX-05** | §5b `:62` revisión humana de una novela completa con la misma rúbrica | Solo como medida del umbral de `SPEC-26` `RF-10` (`:96`), y fuera de su alcance (`:183`). Ningún documento dice quién la hace, sobre qué novela ni dónde queda | Ausencia | **Bloqueante.** Queda recogida aquí; el procedimiento va con `EX-06` |
| **EX-06** | § "Evaluación del sistema" `:92`–`:94`: cinco briefs (uno de injection, uno temporal), tabla por brief, una iteración de tuning con antes y después; § `/docs`: red-team log | `harness/evals/README.md` tiene **uno de cinco** (`brief-incoherencia-temporal.json`, sin ejecutar). `harness/adversarial/` está declarada en `Docs/architecture.md` § "El harness" y no existe; `VER-30` sin implementar. `SPEC-26` lo deja fuera (`:183`) | Ausencia | **Bloqueante** (*«sin evals… no aprueba»*). **Necesita spec** |
| **EX-07** | §5d `:87` *«La especificación debe corresponder al código: el README explica qué estado o transición del código implementa cada acción»* | `specs/tla/README.md` § "Qué implementa cada acción" (`:83`) modela *«el flujo por capítulos de `main`»* y cita `src/config.py`, `src/servidor.py` y `EJECUCION.md`, que **no están en este árbol**. El pipeline de la novela regalo vive en `backend/` | Contradicción | **Bloqueante. Espera decisión**: qué código es el entregable. Si es `backend/`, la tabla se rehace y el modelo puede cambiar (la escalera `haiku → sonnet → opus` de `Reintentar` no es la de `backend/`) |
| **EX-08** | §5d, la regeneración por cambio del lector forma parte del flujo | `specs/tla/README.md` `D-2` decía que no existía en ningún documento; ya la describían `SPEC-22` `RF-50`..`RF-55` y `SPEC-23` | Obsoleto | **Cerrado** en la vuelta 1: `D-2` dice ahora qué specs la describen |
| **EX-09** | § "Novela de ejemplo" `:132`: *«Si el formato de lectura elegido es web, se incluye igualmente el PDF exportado»* | `SPEC-22` §1.2, fila *«Publicar la obra a un formato de libro»* en **No entra** (`:85`). `SPEC-22` está `aprobada` | Contradicción | **Bloqueante. Espera decisión**: reabrir `SPEC-22` o una spec nueva para la exportación |
| **EX-10** | § "Los repositorios deben incluir también": README con brief reproducible, `.env.example`, `ejemplos/novela-ejemplo.pdf`, vídeo en `presentacion/`, `.claude/` con memoria y comandos, configuración MCP | Ningún documento los recogía | Ausencia | **Cerrado** en la vuelta 1 como rutas reservadas en `AGENTS.md` § "Todavía no existe". Crearlos es trabajo, no documentación. Qué memoria se commitea (hoy vive fuera del repositorio) se decide al crearla |
| **EX-11** | § `/docs` `:134`: carpeta `/docs` con seis documentos de proceso —spec inicial, trade-offs, explainers, diagramas, registro de iteraciones y red-team log—, más skills y subagentes referenciados desde allí | `Docs/` es **normativa**, no de proceso, y en git se llama `Docs`: en Windows `docs/` y `Docs/` son la misma carpeta, así que no pueden convivir. Ningún documento recoge los seis | Contradicción de nombre y ausencia | **Bloqueante** (*«sin documentación de proceso en `/docs`… no aprueba»*). **Espera decisión**: renombrar `Docs/` —con todas sus referencias en el mismo commit— o meter lo de proceso dentro de `Docs/` |
| **EX-12** | Todo el enunciado: novela para regalar, diez capítulos | `AGENTS.md` describía el proyecto como *«novelas largas (caso base: terror, una sola obra)»* | Obsoleto | **Cerrado** en la vuelta 1 |

## Huecos de sistema

Documentados y sin código. Van a plan; ninguno se cierra aquí.

| ID | Enunciado | Qué dice el documento | Qué hace el código | Va a |
| --- | --- | --- | --- | --- |
| **EX-13** | §2 lectura interactiva: índice, fichas con enlaces, portada con dedicatoria, cambio del lector | `SPEC-22`, `aprobada` | `frontend/` no existe; `backend/app/features/lectura/` cubre una parte | Un `PLAN-22`, que no existe. `SPEC-22` ya lo permite |
| **EX-14** | §2 `:30` *«se conserva la versión anterior»*; §5d invariante de versiones | `SPEC-22` `RF-53` y `SPEC-23` `D-2`: versión nueva con identidad propia (`F-43`, `CE-5`) | Ninguna versión de obra en el código | Espera a que `SPEC-23` se apruebe; está `en_revision` con `S-1` frente a `S-2` pendiente de medida |
| **EX-15** | §5c `:73` un caso **real** en que Lean detecta lo que los otros no | `specs/lean/README.md` § "El caso real" ejecuta Lean sobre *«una base… sembrada con una obra de cuatro eventos»* | Nada falla: falta una generación. `L-1` lo caza también `INV-08` desde `b2f097c`; `L-2` y `L-3` siguen siendo solo de Lean, porque `edades()` y `ubicuidades()` no tienen llamadas fuera de sus pruebas | Ejecutar `harness/evals/brief-incoherencia-temporal.json` cuando exista `EX-03` |
