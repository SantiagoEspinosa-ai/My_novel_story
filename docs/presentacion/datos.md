# Datos para la presentación

Foto del 2026-09-25 08:28, sobre el commit `f8d52e5`. Cada dato lleva su fuente. «No existe» quiere decir que se buscó y no está; nada de lo que sigue es una estimación.

Las cifras de `backend/web.db` se mueven: cuando se tomaron, había una generación en curso (`obra-9df1eb4deb`). Todas las consultas se hicieron en modo solo lectura (`sqlite3.connect('file:web.db?mode=ro', uri=True)`). Los nombres de personas y personajes se sustituyen por `[NOMBRE]`.

Bases que existen en disco: `backend/web.db` (esquema v20), `backend/regalo-semilla.db` (v18, datos inventados) y `backend/salida/web-antes-de-generar.db` (copia previa de `web.db`). Las bases de R0–R5, de B4 y el libro de gasto de la evaluación (`backend/evaluacion.db`, 55,9066 USD en 126 delegaciones) vivían en worktrees que ya no existen (`docs/estado-al-cerrar-backend.md:382`; `git worktree list`). Sus cifras solo se pueden citar desde los documentos.

---

## 1 · Costes reales

### Cómo se mide y cuándo es suelo

- **Dónde se anota.** Cada delegación deja una fila en `gasto_de_delegacion (id, obra, agente, generacion, coste_usd, cuando)`. La crea la migración 18 (`backend/app/commons/db/migraciones.py:353-370`).
- **Coste no medido.** Se guarda como `NULL`, nunca como 0 (`VER-129`, `docs/verification.md:828`).
- **Cuándo una cifra es suelo.** Cuando alguna de sus delegaciones no trae coste: `es_suelo = sin_coste > 0` (`backend/app/features/regalo/service.py:11-13`).
- **El total de la web es suelo siempre.** `POR_QUE_ES_SUELO` (`service.py:7-8`) lo explica: «lo gastado antes de la migracion 18 no tiene coste guardado en la base, y una delegacion sin coste medido no suma».
- **Qué guarda la traza.** `traza_de_delegacion` guarda el modelo pero no el coste (`F-144`), y solo del Escritor, el Editor y el Resumidor.
- **Modelos sin registro.** El del Planificador, el Revisor y el Entrevistador no queda en ninguna base: sale solo de `sistema.json`.

### Las dos configuraciones de modelo

La orden de delegación pasa `--model` desde `backend/config/sistema.json` (`backend/app/commons/modelo/proveedor.py:293`). La historia está en `git log -p backend/config/sistema.json`.

| Rol | Configuración A (commits `331e5c3` a `23835c7`, excluido) | Configuración B (desde `23835c7`) |
| --- | --- | --- |
| Entrevistador | sonnet | sonnet |
| Planificador | opus | sonnet |
| Revisor del plan | opus | sonnet |
| Escritor | **fable** | sonnet; **opus** desde que el conductor lo subió tras dos fallos (cambio sin commitear en `sistema.json`) |
| Editor | opus | sonnet |
| Resumidor | haiku | haiku |
| Juez | opus | sonnet |

### Serie A · configuración A (R0–R5, B4, antes-2)

Las bases de estas ejecuciones ya no están en disco; las cifras salen de los documentos.

| Ejecución | Qué es | USD | Deleg. | ¿Suelo? | Fuente |
| --- | --- | --- | --- | --- | --- |
| **R1 · brief-base** | **novela completa, publicada**, Lean 0 | **16,8905** | **36** | No | `harness/evals/medidas.md:138` |
| **R5 · vetadas** | **novela completa, publicada** | **20,5556** | **39** | No | `medidas.md:213` |
| B4 · demo de la cascada | 7 capítulos regenerados, publicada | 19,5379 | 42 | No | `medidas.md:254` |
| antes-2 (tuning) | no terminó: paró 3 veces por INV-03 | 8,7712 | 14 | No | `medidas.md:269-272` |
| R3 · temporal | sin novela: plan no aprobado | 4,9492 | 7 | No | `medidas.md:200` |
| R4 · contradicciones | sin novela: plan rechazado (F-146) | 3,1154 | 16 | No | `medidas.md:222` |
| R0 | un capítulo | 2,1650 | 5 | No | `medidas.md:97-98` |
| R2 · injection | sin novela: la entrevista no cerró (F-140) | 1,6246 | 14 | No | `medidas.md:189` |
| INV-30 | inspección visual | 0,6959 | — | — | `medidas.md:182` |
| **Total de la fase** | | **77,2132** | | **Sí** | `docs/estado-al-cerrar-backend.md:284-287` |

- **Antes de la configuración A**, con otra forma del pipeline (la novela de terror): 26,0372 USD en 169 delegaciones. Es suelo porque 10 delegaciones no dieron coste; llegó a 55 de 60 escenas (`medidas.md:19,26`).
- **La novela completa más cara medida es R5 (20,5556 USD), no R1.** R1 es «la novela de ejemplo», la referencia que enseña la web (`backend/app/commons/config.py:94-100`). Corregido en `medidas.md:144`, que la llamaba «mayor coste medido».
- **Desglose por agente de R1 y de R5: no existe** en ningún documento, y sus bases no están en disco.

### Serie B · configuración B (hoy, `backend/web.db`)

Consulta: `SELECT obra, count(*), sum(coste_usd), sum(coste_usd IS NULL) FROM gasto_de_delegacion GROUP BY obra`.

| Obra | Resultado | USD | Deleg. | Sin coste | ¿Suelo? |
| --- | --- | --- | --- | --- | --- |
| **`obra-6845dbb0d0`** «La furgoneta de [NOMBRE]» | **novela completa, publicada**, Lean 0 | **5,4454** | **43** | 1 | **Sí** (fila 83, escritor) |
| `obra-9df1eb4deb` | en curso | 4,4684 (parcial) | 28 | 0 | — |
| `obra-cda02192ef` | retirada: capítulo 1 rendido (INV-17, F-209) | 2,5199 | 19 | 0 | No |
| `obra-4f77219871` | retirada: capítulo 2 rendido (INV-23, F-211) | 2,2321 | 17 | 0 | No |
| `obra-en-curso` | retirada: plan no aprobado; ficha de la semilla | 0,8343 | 3 | 0 | No |
| **Total** | | **15,5002** | **110** | 1 | **Sí** |

- `obra-cda02192ef` lleva además 1,0087 USD de entrevista, en 8 delegaciones sin generación.
- **Modelo del Escritor en la novela publicada: mixto.**
  - Borradores: opus 12, sonnet 4 (`SELECT modelo, count(*) FROM borrador WHERE escena LIKE 'obra-6845dbb0d0%' GROUP BY modelo`).
  - Trazas: opus 12, sonnet 2.
  - El resto de roles, en sonnet; el Resumidor, en haiku.
- **Desglose por agente de `obra-6845dbb0d0`** (`… WHERE obra='obra-6845dbb0d0' GROUP BY agente`):

| Agente | USD | Deleg. |
| --- | --- | --- |
| escritor | 3,9119 | 19 (1 sin coste) |
| editor | 0,7842 | 12 |
| resumidor | 0,4348 | 10 |
| planificador | 0,1958 | 1 |
| revisor_plan | 0,1188 | 1 |

- **Juez:** no tiene ninguna fila de gasto en ninguna base local.

### El rango: el coste depende del reparto de modelos

| | Configuración A | Configuración B |
| --- | --- | --- |
| Novelas completas medidas | R1 16,8905 · R5 20,5556 | `obra-6845dbb0d0` 5,4454 (suelo) |
| Delegaciones | 36 · 39 | 43 |
| Coste por delegación (USD / delegaciones) | 0,469 · 0,527 | 0,127 |

- **Rango medido de una novela completa y publicada: de 5,45 a 20,56 USD, unas 3,8 veces.**
- **El factor es el modelo, no el volumen.** La configuración B hizo más delegaciones (43 frente a 36–39) y aun así costó entre 3 y 4 veces menos. Es lo mismo que dice `F-25` (`docs/verification.md:1245`): «el precio del modelo pesa más que la cantidad».
- **Límites del dato:**
  - La serie B tiene una sola novela completa, y su Escritor fue mixto.
  - No existe ninguna medida de una novela entera con el Escritor solo en sonnet ni solo en opus.
  - Las dos series se escribieron con fichas distintas.

---

## 2 · Tabla de evals

- **Fuente:** `harness/evals/resultados.md`. La genera `backend/evaluar.py` y no se edita a mano (`:3`).
- **Pasada «antes»:** ejecutada contra el modelo en los cinco briefs.
- **Pasada «después»:** sin ejecutar en los cinco; su coste figura como «sin medir» (`resultados.md:29-41`; `medidas.md:270-271`).
- **Columnas iguales en todos los briefs:**
  - INV-06: «no ejecutado».
  - INV-10, 11, 12 y 16: «no aplica». Son obsoletas desde `SPEC-26` v3.

**Por qué la fila de brief-base de `resultados.md` enseña antes-2 y no R1.**

- `evaluar.py` pinta, por brief, la última ejecución del libro. antes-2 (el tuning, que no terminó) es posterior a R1, así que al regenerar la tabla en `4f2fae6` la sustituyó.
- La fila de R1 está en la versión anterior del fichero, generada por el mismo `evaluar.py`: `git show 3717f25:harness/evals/resultados.md`, líneas 11 y 19.
- `resultados.md` no se puede regenerar con R1 hoy: el libro de gasto (`backend/evaluacion.db`) estaba en un worktree que ya no existe.
- Por eso van abajo las dos filas, cada una con su commit.

| Brief (ejecución) | USD / deleg. | Pasaron | Fallaron | Sin veredicto (no se ejecutaron) |
| --- | --- | --- | --- | --- |
| **brief-base · R1** (`3717f25`) | **16,8905 / 36** | INV-01, 02 (1 disparo), 03, 04, 17 (2 disparos), 18, 21, 22, 23, 24, 26, 27, 28 (Lean), 29, INV-26.× (6 criterios), schema.plan, **publicacion** | **INV-25 (7 disparos)**: `menor`, no bloquea | INV-05, 07, 08, 09, 13, 14, 15, 30 |
| brief-base · antes-2 (`4f2fae6`) | 8,7712 / 14 | INV-01, 02, 04, 17 (1 disparo), 18, 21, 22, 23, 26, INV-26.×, schema.plan, revisor.plan | **INV-03 (5 disparos)** | INV-05, 07, 08, 09, 13, 14, 15, 24, 25, 27, 28, 29, 30, publicacion |
| brief-injection | 1,6246 / 14 | entrevista.instrucciones (1 disparo) | — | todo lo demás: no hubo novela |
| brief-incoherencia-temporal | 4,9492 / 7 | — | **schema.plan (2 disparos), revisor.plan (2 disparos)** | todo lo demás: no hubo novela |
| brief-contradicciones | 3,1154 / 16 | entrevista.contradicciones (3 disparos) | **schema.plan** | todo lo demás: no hubo novela |
| brief-vetadas-por-variantes · R5 | 20,5556 / 39 | INV-01, 02, 03 (1 disparo), 04, 17 (2 disparos), 18, 21, 22, 23, 24, 26 (2 disparos), 27, 28, 29, INV-26.×, schema.plan, revisor.plan, **publicacion** | **INV-25 (5 disparos)** | INV-05, 07, 08, 09, 13, 14, 15, 30 |

- **Columna `revisor.plan`:** en `3717f25` todavía no existía. El plan de R1 se aprobó en una ronda (`medidas.md:132`).
- **Versión del prompt del Escritor:** `8f9a1478e71a` en todas las filas.
- **Suma de las cinco pasadas «antes»:** 47,1353 USD con R1 (`docs/cobertura-examen.md:72`); 39,016 USD con antes-2 en su lugar.

---

## 3 · Lean

Lo pide `EXAMEN.md:73`: «Debe mostrarse al menos un caso real en el que el validador formal detecta una incoherencia que los otros validadores no detectaron, o justificar por qué no se encontró ninguno».

### El caso real: `obra-9df1eb4deb` (2026-09-25)

La ficha y el caso completos, con la salida literal, están en `specs/lean/casos/obra-9df1eb4deb/` (commit `0cbf4a2`).

- **La novela.**
  - Diez capítulos, los diez `consolidada`.
  - 6,5627 USD en 44 delegaciones, todas medidas.
  - Modelos: Escritor opus; Planificador, Revisor y Editor sonnet.
  - Consulta: `SELECT sum(coste_usd), count(*) FROM gasto_de_delegacion WHERE obra='obra-9df1eb4deb'`.
- **Lean: código 1, 52 violaciones.** 8 de `L-1` (orden de la fábula) y 44 de `L-3` (un personaje en dos lugares a la vez).
  - Salida literal: `specs/lean/casos/obra-9df1eb4deb/salida-verificar-real.txt`.
  - Cronología que Lean recibió: `Generado.lean`.
- **La puerta no la publicó.**
  - `veredicto_de_publicacion`, rondas 1 y 2: `publica = 0`, `codigo_lean = 1`.
  - Hallazgo `INV-28` `bloqueante` abierto, id 46.
- **Ningún otro validador vio nada.** En la obra solo hay hallazgos `INV-17` (2), `INV-25` (11) e `INV-28` (1).
  - Consulta: `SELECT invariante, count(*) FROM hallazgo WHERE escena LIKE 'obra-9df1eb4deb%' GROUP BY 1`.
  - Revisor del plan, `INV-02`, `INV-03`, `INV-26` e `INV-27`: sin hallazgos.
  - **`INV-08`, que debía cazar las 8 `L-1`, no dejó nada.** Se evalúa en cada capítulo y nadie lee su resultado (`F-214`, abierto; `orquestacion/obra.py:359`, `novela.py:522`).
  - Las 44 `L-3` no las cubre ninguna otra regla: `INV-02` mira escena a escena.

Líneas literales:

```
== obra-9df1eb4deb ==
cobertura: eventos: 10 · sin fecha legible: 0 · sin nacimiento: 3 · con exclusion: 0 · capitulos no ordenables: 0
violaciones: 52 · sin datos: 13
  [L-1] evt-obra-9df1eb4deb-cap-02-e1 se lee despues de evt-obra-9df1eb4deb-cap-01-e1 (discurso 1 -> 2) pero ocurre antes en la fabula (2012-9-25 0:0 < 2026-9-25 0:0) y no declara analepsis
  [L-3] obra-9df1eb4deb-per-ana esta presente en evt-obra-9df1eb4deb-cap-02-e1 (obra-9df1eb4deb-lug-vagon) y en evt-obra-9df1eb4deb-cap-04-e1 (obra-9df1eb4deb-lug-locomotora) a la vez
Hay incoherencias temporales: la version NO se publica.
```

**Qué pasaba en la novela.**

| Capítulos | `t_fabula` | Efecto |
| --- | --- | --- |
| 1 y 10 | `2026-09-25` | — |
| 2 a 9 | `2012-09-25` en los ocho, sin hora, en lugares distintos | `L-1`: un recuerdo sin analepsis declarada, que hoy no se puede declarar (`SPEC-24` sin plan)<br>`L-3`: ocho escenas en el mismo instante |

**Qué cambió.** `F-213`, commit `a40bffd`:
- El plan vuelve al Planificador, sin pagar al Revisor, si la `t_fabula` no avanza estrictamente de una escena a la siguiente.
- El prompt pide fecha y hora distintas por escena.
- La novela se relanzó con la misma ficha como `obra-b113c7dd8c`. La obra del caso se conserva tal cual, como prueba.

### Antes de este caso

- **Todas las ejecuciones reales dieron Lean 0:**

  | Ejecución | Fuente |
  | --- | --- |
  | R1 | `medidas.md:134` |
  | R5 | `medidas.md:210-212` |
  | B4, versiones 1 y 3 | `medidas.md:246-251` |
  | `obra-6845dbb0d0` | `veredicto_de_publicacion` |

- **R3, el brief pensado para provocarlo, lo paró antes el Revisor del plan** (`medidas.md:190-200`).
- **F-47: Lean destapó que `INV-08` no se ejecutaba** (`docs/verification.md:1226`). Fue sobre una base sembrada, no sobre una generación.
- **Caso demostrativo sobre esa base sembrada:** `specs/lean/README.md:130-145`. Hoy lo deja atrás el caso real.

### Dónde está

- **Proyecto:** Lean 4.34.0 en `specs/lean/`.
- **Invariantes** (`README.md:114-119`):
  - `L-1`: orden de la fábula salvo analepsis.
  - `L-2`: nadie aparece antes de nacer.
  - `L-3`: nadie está en dos lugares a la vez.
  - `L-4`: nadie aparece después de un evento que lo excluye.
- **En el harness:** `INV-28`, nivel obra, `bloqueante` (`docs/definitions.md:410`).
- **Quién lo ejecuta:** la puerta de publicación (`backend/app/features/auditoria/lean.py`).

---

## 4 · TLA+

- Modelo vigente: `specs/tla/HarnessBackend.tla` (765 líneas).
  - `HarnessNovela.tla` es el modelo obsoleto de la rama `main` y solo se conserva por su historia.
  - TLC 2.19 (rev. `5a47802`), según la cabecera de los `tlc-*.txt`.
  - **Hoy no se puede volver a ejecutar en esta máquina:** no hay `java` ni `tla2tools.jar` (`specs/tla/README.md:66-67`).
- **Tamaño del modelo** (`HarnessBackend.cfg`): `NumCapitulos=5`, `ReescriturasDelEditor=2`, `ReescriturasPorVetada=1`, `ReintentosDeTransporte=1`, `RevisionesDePlan=2`, `ReintentosDePublicacion=1`, `TopeDelegaciones=8`, `MaxCaidas=1`, `MaxRegeneraciones=1`. La justificación está en `README.md:89-101`.
- **Invariantes de seguridad** (`HarnessBackend.tla:142,695-749`), doce:
  - `TypeOK`
  - `NuncaPublicaSinValidar`
  - `NuncaPierdeCapitulos`
  - `NoReescribeCerrados`
  - `NoSaltaCapitulos`
  - `SoloSobreConsolidadas` (INV-05)
  - `MemoriaCompleta`
  - `ReintentosAcotados`
  - `RondasDePlanConservadas`
  - `DelegacionesAcotadas`
  - `CadaVersionTieneSuTope`
  - `LectorVeLoPublicado`
- **Propiedad de acción:** `VersionesSoloCrecen` (`:754`).
- **Liveness:** `Terminacion == <>[](fase \in {"publicada","detenido"})`, con `WF_vars(Avanza)` (`:686,763`).

| Ejecución | Resultado | Generados | Distintos | Prof. | Fuente |
| --- | --- | --- | --- | --- | --- |
| Corregido, 5 capítulos | No error has been found | 1.226.620 | 756.394 | 41 | `tlc-backend-corregido.txt` |
| Código de hoy, vivacidad, 3 capítulos | sin error | 8.921.820 | 5.482.194 | 63 | `tlc-backend-de-hoy-vivacidad.txt` |
| Código de hoy, vivacidad, 5 capítulos | **interrumpida, sin resultado** | 55.829.166 | 37.643.441 | — | `tlc-backend-de-hoy-vivacidad-5-capitulos-interrumpida.txt` |
| Mutante de `Terminacion` | propiedad temporal violada | 1.090.188 | 607.146 | — | `tlc-mutante-terminacion.txt` |

**Contraejemplos y el cambio que provocó cada uno** (`specs/tla/README.md:217-397`; `docs/verification.md`):

| CE | Propiedad violada | Estados distintos | Qué mostró | Cambio |
| --- | --- | --- | --- | --- |
| CE-6 | `TypeOK` | 22.522 | `numero = 4 con tope 3` tras reanudar | Corrigió el propio arreglo de F-110: `Montar` manda a `rindiendo` un capítulo con los intentos agotados |
| CE-7 | `ReintentosAcotados` | 144 | 3 rondas de plan con tope 2, tras reanudar | F-110, **abierto** |
| CE-8 | `RondasDePlanConservadas` | 68 | la reanudación pisa filas del plan | F-111, cerrado en `ff8041f` |
| CE-9 | `NoReescribeCerrados` | 3.077 | reescribe una escena ya consolidada | F-112 (a), **abierto** |
| CE-10 | `SoloSobreConsolidadas` | 14.761 | monta sobre una escena rendida sin delta | F-112 (b), **abierto** |
| CE-11 | `NuncaPublicaSinValidar` | 411.005 | publica con un capítulo sin juzgar | F-113, cerrado en `8ed4680` (un `sin_veredicto` no publica) |
| CE-12 | `DelegacionesAcotadas` | 117.772 | 9 ciclos con tope 8 | F-114, cerrado en `ce9dc2e` (el tope cuenta toda la obra) |
| CE-13 | `MemoriaCompleta` | 682.954 | un capítulo sin memoria | F-116, **abierto** |
| CE-14 | `LectorVeLoPublicado` | 589.510 | el lector ve una versión no publicada | F-121, cerrado en `aa403a6`; **sin volver a pasar por TLC** |
| CE-15 | `CadaVersionTieneSuTope` | 2.582.281 | las rondas de la puerta se contaban por obra | F-122, cerrado en `25fc89c` (migración 16); **sin volver a pasar por TLC** |

- Del modelo obsoleto (`README.md:523-639`):
  - CE-1: publicaba una novela vacía.
  - CE-2: publicaba sin validar.
  - CE-3: el defecto estaba en un documento.
  - CE-4: stuttering.
  - CE-5: dio origen a F-43.
- Incoherencia: `BackendDeHoy.cfg` cita `tlc-backend-de-hoy.txt`, **que no existe**; `-continue` se descartó por una excepción (`README.md:84-87`).

---

## 5 · Los cuatro tipos de validadores

Fuente: `backend/app/commons/invariantes/registro.py:82-170`.

- **Invariantes:**
  - 29 identificadores, de INV-01 a INV-31; INV-19 e INV-20 están reservadas.
  - 4 obsoletas: INV-10, 11, 12 y 16.
  - **25 activas: 22 de tipo `regla` y 3 de tipo `juez_llm`.**
  - `TipoDeVerificador` no tiene un valor «formal»: Lean (INV-28) figura como `regla`.

| Tipo | Cuántos | Dónde actúa | Implementados de verdad |
| --- | --- | --- | --- |
| **Programáticos** | 22 reglas y además schema de ficha, contradicciones, schema de salida, cobertura del plan y detector de inyección (`docs/proceso/diagramas.md:162-166`) | **Hook `Stop`**: longitud, INV-21, INV-22 (`backend/hooks/validar_capitulo.py:61-72`)<br>**Hook `PreToolUse`**: allowlist de tools por agente (`backend/hooks/policy.py`)<br>**Antes del Editor**: INV-21, 22, 23, 31 (`orquestacion/ciclo.py:278-326`)<br>**Puerta de escena**: INV-01, 02, 03, 04, 17, 18 (`verificacion/puertas.py:20`)<br>**Puerta de capítulo**: INV-08 (`auditoria/capitulo.py:76-100`)<br>**Obra**: INV-24, 25 (`orquestacion/novela.py:199-240`)<br>**Puerta de publicación**: INV-29 (`auditoria/publicacion.py:89-93`) | Con código y prueba: INV-01, 02, 03, 04, 08, 17, 18, 21, 22, 23, 24, 25, 29, 31 y los dos hooks<br>**Sin comprobación ejecutable**: INV-06 (no ejecutada a propósito), INV-07 (solo sobre el plan), INV-09, 13, 14, 15<br>INV-05 se cumple por estructura, sin comprobación propia (`consolidacion/aplicar.py:5`) |
| **Semánticos** | Revisor del plan, INV-26 (Editor por capítulo, 6 criterios), INV-27 (juicio de obra), INV-30 (inspector visual) | **Editor**: INV-26 (`ciclo.py:163`)<br>**Obra y puerta**: INV-27 (`novela.py:174-195`)<br>**Plan**: Revisor, hasta 3 rondas<br>**A mano**: INV-30 (`backend/inspeccion_visual.py`) | Los cuatro ejercidos en real (`diagramas.md:160-181`). INV-30 **no vuelve al Escritor** (`EX-04`) |
| **Lean 4** | 1 validador (INV-28) con 4 invariantes | **Puerta de publicación** (`auditoria/lean.py`), automático | Sí; código 0 en R1, R5, B4 y `obra-6845dbb0d0` |
| **TLA+** | 1 modelo con 12 invariantes, 1 propiedad de acción y 1 de liveness | **Fuera del pipeline**: TLC a mano sobre el diseño (`EXAMEN.md:101`) | Sí, con salidas guardadas; hoy no se puede volver a ejecutar aquí (sin `java`) |

- Revisión humana: no existe (`diagramas.md:181`).
- `docs/verification.md:698-700` dice «Validadores implementados 0». **Es un recuento caducado** y contradice `diagramas.md:160-181`.

---

## 6 · Guardrails

### Los tres niveles de palabras vetadas

| Nivel | Contenido | Fuente |
| --- | --- | --- |
| Global | 20 formas | `backend/config/vetadas.json`, clave `global` |
| Franja de edad | `infantil` (0–11 años), 7 formas; `juvenil` (12–17), 2 formas | `vetadas.json`, clave `franjas`; los rangos en `sistema.json`, clave `franjas_de_edad` |
| Novela | las de la ficha y los nombres vetados, completos y por su nombre de pila | `features/politica/repository.py:64-77`; `commons/politica/vetadas.py:44-49` |

- **Cómo se juntan:** `vetadas_para` (`repository.py:87-96`).
- **Normalización:** mayúsculas, acentos (conservando la ñ), plurales y género. No lematiza (`commons/politica/normalizar.py:6-8,36-49`).
- **Qué pasa al detectar una:**
  1. Se anota `coincidencia_vetada` en el audit log.
  2. El Escritor reescribe con el problema: «escribiste «X», que no puede aparecer (vetada: Y)».
  3. Hay 2 reescrituras de tope; al agotarlas, `parada_por_vetada` (`orquestacion/obra.py:519-540`).

### Ejemplo real de detección y reescritura

**No existe en ninguna base actual.**
- Hay 0 hallazgos INV-21 y 0 filas en `decision_de_politica` en las tres bases.
- Consultas: `SELECT invariante, count(*) FROM hallazgo GROUP BY invariante` y `SELECT tipo, count(*) FROM decision_de_politica GROUP BY tipo`.
- **La única detección real documentada fue un falso positivo del propio guardrail: F-59** (`docs/verification.md:1137`, commit `bf42074`, arreglo en `b18b286`).
  - Una vetada malsonante con ñ se normalizaba quitando la tilde de la ñ y acababa vetando la preposición «con».
  - Resultado: el capítulo 1 se reescribió dos veces, se paró por `parada_por_vetada` y dejó 47 coincidencias en el audit log.
  - **El texto del borrador no existe**: su base no está en el repositorio.
- **R5 (brief de vetadas por variantes):** INV-21 no disparó. El Escritor esquivó todas las variantes porque el prompt le da la lista (`docs/proceso/red-team-log.md:18`).
- **Detección con texto:** solo con dobles, en `test_vetadas.py`, `test_repository.py` y RT-03.
- **RT-04** (derivadas como «hospitalario» o «tormentoso»): sin detector (`harness/adversarial/casos.json`).

### El caso de injection del red-team

- **RT-01**, instrucción que coincide con un patrón:
  - Lo detecta `entrevista.instrucciones`, la lista `PATRONES` (`features/entrevista/texto_libre.py:50-62`).
  - Anota `instruccion_en_texto_libre` y descarta los hechos del texto (`:104-111`).
  - Lo que de verdad la contiene es la estructura: el texto libre nunca llega al Escritor y solo entran hechos confirmados (`casos.json`, RT-01).
- **Contra el modelo real (R2):**
  - El detector disparó una vez y descartó el texto.
  - La entrevista no cerró por F-140, así que no hubo novela.
  - Coste: 1,6246 USD en 14 delegaciones (`medidas.md:186-189`).
- **RT-02**, instrucción que no coincide con ningún patrón:
  - Detector: **ninguno**.
  - La contiene que nadie confirme el hecho propuesto; un comprador que confirma a ciegas la mete en la ficha (`casos.json`).

---

## 7 · Arquitectura

### Roles y modelo

La orden de delegación pasa siempre `--model` desde `sistema.json` (`backend/app/commons/modelo/proveedor.py:293`). Por eso el `model` del frontmatter de `.claude/agents/*.md` no se usa en el pipeline.

| Rol | `sistema.json` en HEAD (`23835c7`) | Copia de trabajo | Antes de `23835c7` (R0–R5, B4) |
| --- | --- | --- | --- |
| Entrevistador | sonnet | sonnet | sonnet |
| Planificador | sonnet | sonnet | opus |
| Revisor del plan | sonnet | sonnet | opus |
| Escritor | sonnet | **opus** (el conductor, tras dos fallos) | fable |
| Editor | sonnet | sonnet | opus |
| Resumidor | haiku | haiku | haiku |
| Juez (solo con `es_editor=False`) | sonnet | sonnet | opus |
| Inspector visual | — | — | sonnet (`inspeccion_visual.py:89`) |

### El bucle

- `novela.escribir` (`orquestacion/novela.py:397-430`): planifica o reanuda el plan (Planificador y Revisor, hasta 3 rondas), monta la obra y escribe capítulo a capítulo.
- Por escena, `ciclo.ejecutar` (`orquestacion/ciclo.py:257-362`), en este orden:
  1. El Escritor genera texto y delta a la vez.
  2. Puertas deterministas.
  3. INV-21, INV-22, INV-31 e INV-23.
  4. El Editor, aislado. Solo se paga si no hay hallazgos.
  5. Bloqueantes.
  6. Se consolida el delta.
  7. El Resumidor.
- La siguiente escena solo empieza con la anterior consolidada (INV-05, `obra.py:4`).
- Después vienen la puerta de capítulo (INV-08), el nivel obra (INV-24, 25 y 27) y la puerta de publicación con Lean.
- El Editor y el Juez se lanzan en un directorio aislado sin `CLAUDE.md`, porque se midió que `omitClaudeMd` se ignora (F-20, `ciclo.py:15-32`).

### Contexto

- Presupuesto de 100.000 tokens por niveles (`CLAUDE.md`, § Límite de contexto):

| Nivel | Tokens |
| --- | --- |
| Inmutable | 15.000 |
| Estado | 10.000 |
| Local | 25.000 |
| Recuperado | 20.000 |
| Resúmenes | 10.000 |
| Salida | 20.000 |

- **Orden de recorte:** siete bloques (`features/contexto/bloques.py:40-61`):
  1. `condensaciones`
  2. `fichas_y_setups`
  3. `escena_anterior`
  4. `estado_y_conocimiento`, que no se elimina porque lo leen INV-02 e INV-03
  5. `problemas_del_intento_anterior`
  6. `reserva_de_salida`
  7. `inmutable`
- **Cómo se recorta:** en dos vueltas, primero reducir (un bloque se queda en el 40%, `FRACCION_REDUCIDA`, sin medir) y luego eliminar. Si aun así no cabe, falla. Nunca trunca (`recorte.py:1-13`).
- **Medido en `web.db`:**
  - **0 recortes** (`SELECT count(*) FROM traza_de_delegacion WHERE recortes NOT IN ('[]','')`).
  - El Escritor envía como máximo 8.139 tokens estimados y 5.031 de media, en 36 trazas.

### Story bible, tools y hooks

- **Story bible:** tablas en `docs/proceso/diagramas.md:103-145`.
  - `obra`, `capitulo`, `escena`, `borrador`, `delta_de_escena`, `hallazgo`, `hecho_canonico`, `uso_de_hecho`, `evento_cronologico`, `participacion_en_evento`, `entidad`, `ficha`, `resumen`, `palabra_vetada`, `plan_de_obra`, `entrevista`.
  - Además `traza_de_delegacion`, `decision_de_politica`, `pseudonimo`, `version_de_obra`, etc.
  - El estado del mundo se reconstruye acumulando los deltas.
- **Tools (SPEC-28):** un servidor MCP por stdio (`backend/herramientas/story_bible.py`).
  - Abre la base en solo lectura, acotada a una obra.
  - Tres tools: `hechos`, `ficha` y `cronologia`. Ninguna devuelve el texto de una escena y todas responden pseudonimizadas.
  - Solo las tienen el Escritor y el Editor.
  - **Uso real en `web.db`: 169 llamadas.**
    - Editor: `cronologia` 40, `ficha` 76, `hechos` 21.
    - Escritor: `ficha` 28, `hechos` 4.
- **Hooks** (`.claude/settings.json`):
  - `Stop` → `backend/hooks/validar_capitulo.py`.
    - Comprueba longitud, vetadas y nombres.
    - Con código 2 devuelve el capítulo al Escritor **en la misma sesión**, más barato que una delegación nueva.
  - `PreToolUse` → `backend/hooks/policy.py`.
    - Allowlist de tools por agente.
    - Lo que niega queda en `decision_de_politica`.
  - **F-212:** en Windows el hook `Stop` no se había ejecutado nunca hasta el commit `3db83c8`.

### Decisiones que más se notan

- **SPEC-14 · Delegación en sesiones de Claude Code en vez de la API** (commit `d0d849e`).
  - No había clave de API, solo suscripción.
  - Consecuencia: el techo de 100k tokens es «sobre lo que se manda», no sobre la ventana del otro lado (`CLAUDE.md`).
- **A-03 · Un agente es una llamada con su propio contexto** (`docs/architecture.md:876-925`).
  - Coste medido: 0,2508 USD por escena, dominado por la creación de caché (9.476 tokens).
- **A-06 y F-20 · Editor y Juez aislados.** Un juez que ve las mismas reglas que la regla no desempata: confirma (`generacion/prompt.py`, docstring).
- **SPEC-34 · Pseudonimización** (`eaf79c8`).
  - Los agentes ven nombres inventados y estables.
  - Los nombres reales se restituyen antes de los validadores; un residuo es INV-31.
  - Responde a F-146: las sesiones anonimizaban al destinatario.
- **SPEC-40 · Ante los agentes, el destinatario es «el protagonista»** (`c5c7120`).
  - Ningún prompt menciona regalo, comprador ni dedicatoria.
  - Con pseudónimo, el Planificador aún escribía `[NOMBRE_ANONIMIZADO]`.
- **Bloqueante frente a mayor/menor** (`CLAUDE.md`, § Reglas de trabajo). Un bloqueante para la escena; un mayor o menor deja hallazgo y deja seguir.
- **Consolidar antes de seguir (INV-05).** Es lo que corta la propagación del error.

---

## 8 · La demo (cambio del lector, SPEC-23 / PLAN-23 B4)

- **Qué se pidió:** renombrar a un personaje secundario, «el dueño de la venta del cruce» (datos inventados) (`harness/evals/medidas.md:226-227`).
- **Qué se regeneró:** cascada desde el capítulo 4, el primero donde está presente. Los capítulos 1 a 3 se comparten con la versión anterior (`medidas.md:227-228`).
  - La salida `cascada` se eligió por el arrastre medido (`harness/evals/arrastre-SPEC-23.json`, commit `97574aa`).

| Tramo | Qué pasó | USD / deleg. |
| --- | --- | --- |
| Versión 2 (`5f99d89`) | caps. 4–7 consolidados; el 8 paró por INV-02 (F-148, defecto nuestro) | 7,6566 / 14 |
| Versión 2 relanzada (`b6053f1`) | el 8 pasó; el 9 paró por F-149 | 2,3491 / 4 |
| Versión 3 | 7 capítulos sin paradas; Lean sin veredicto por F-151 | 9,4238 / 23 |
| Puerta relanzada | **publicada en la ronda 2** | 0,1084 / 1 |
| **Total** | | **19,5379 / 42**, todo medido (`medidas.md:254-257`, commit `d64416b`) |

- **Qué se conservó:**
  - Los capítulos 1–3.
  - La versión 1 siguió siendo la vigente para el lector hasta que se publicó la nueva (`docs/proceso/registro-de-iteraciones.md:78-80`).
  - En la web no se respetó: enseñaba como vigente la versión en escritura (F-150).
- **No existe:**
  - La comprobación «versión 1 idéntica byte a byte» que pedía B4 (`specs/plans/PLAN-23.md:475-485`).
  - La base de la demo, que no está en disco.
  - La demo desde la web: `POST /obras/{id}/cambios` falla porque el worker no tiene agentes (F-126); el cambio solo se lanza con `backend/pedir_cambio.py`.

---

## 9 · Los hallazgos que mejor cuentan el proyecto

1. **F-58 · El Escritor nunca vio su contexto** (`docs/verification.md:1136`).
   - Se creía: recibía premisa y memoria, 1.339 tokens.
   - Pasaba: «recibe los tamaños de los bloques, no su texto, y en todas las escenas». La novela de diez capítulos se escribió sin premisa ni memoria.
   - Cómo se encontró: al escribir la prueba del encadenado (commit `9633415`, cerrado en `b8410c0`).
2. **F-47 · El validador declarado que no ejecutaba nadie** (`verification.md:1226`).
   - Se creía: `INV-08` vigilaba el orden temporal.
   - Pasaba: «tiene su consulta escrita y no la ejecuta nadie».
   - Cómo se encontró: **Lean** cazaba una inversión que `INV-08` debía haber cazado (`b2f097c`).
3. **F-121 y F-150 · La versión vigente, primero en TLA+ y después en la web** (`verification.md:1181,1203`).
   - Se creía: la vigente es la última creada.
   - Pasaba: «el lector veía una versión que nadie había escrito ni validado».
   - Cómo se encontró:
     - F-121: **TLC** (CE-14, `LectorVeLoPublicado`), antes de existir la rama.
     - F-150: la web real en Edge sin cabeza durante la demo. La lectura web tenía su propia copia de la regla.
4. **F-113 · Se publicaba un capítulo que el Editor no juzgó** (`verification.md:1173`).
   - Pasaba: un `INV-26 sin_veredicto` no bloqueaba la puerta; ya había ocurrido en R0 (F-76).
   - Cómo se encontró: **TLC** (CE-11, `NuncaPublicaSinValidar`). Cerrado en `8ed4680`.
5. **F-146 y SPEC-40 · La privacidad contra la personalización** (`verification.md:1198`).
   - Pasaba: las sesiones delegadas anonimizaban el nombre del destinatario por la política de la organización, y el plan de R4 se rechazó.
   - Primero se pseudonimizó (SPEC-34). Aun así, el Planificador escribía `[NOMBRE_ANONIMIZADO]` en las tres rondas.
   - Al final, ante los agentes, el destinatario pasó a ser «el protagonista» (SPEC-40).
6. **F-212 · El hook que nunca se ejecutó** (`verification.md`, fila F-212).
   - Se creía: el hook `Stop` devolvía los capítulos cortos dentro de la sesión.
   - Pasaba: en Windows, PowerShell dejaba `$CLAUDE_PROJECT_DIR` vacía; el hook fallaba sin bloquear, y los capítulos cortos llegaban a INV-17 y gastaban reescrituras enteras.
   - Cómo se encontró: una delegación mínima con `--debug-file` aceptó un texto de dos palabras en un turno.
   - Enlaza con F-61: los hooks no se cargaban al arrancar fuera de la raíz (`:1139`).
- Encontrados por el propio sistema:
  - **F-17** (`:1253`): el comprobador de importaciones cazó que el bucle violaba A-02: «falló, contra su propio autor».
  - **F-24** (`:1244`): con el modelo real, INV-03 cazó a un personaje que revelaba algo que solo sabía otro, la primera vez que el sistema detectó el fallo para el que se construyó.
  - **F-205** (`:1213`): lo cazó una prueba que buscaba otra cosa.

---

## 10 · Langfuse

- **Qué sube** (`specs/SPEC - Observabilidad en Langfuse.md`, SPEC-29 v2, tabla `:40-47`):
  - Las plantillas de prompt sin rellenar, con su versión.
  - Los nombres de rol, tool y validador.
  - Tokens, coste, latencia y modelo.
  - Identificadores opacos; la sesión es un hash de la obra.
  - Los resultados de los validadores como scores.
  - Para una vetada, su nivel y un identificador.
- **Qué no sube:**
  - El prompt tal como se envió.
  - Capítulos, planes, deltas, resúmenes y justificaciones del Editor.
  - Los turnos de la entrevista.
  - Ningún dato del destinatario.
  - Las vetadas por novela.
  - Los argumentos y la salida de las tools.
- **Por qué** (`:49-54`): la ficha se borra al entregar (SPEC-25 RF-21), y lo que ya está en Langfuse no lo borra nadie.
- **Cómo se hace cumplir:**
  - `_sin_observabilidad` quita las claves de Langfuse y la telemetría del entorno de cada sesión delegada (`proveedor.py:339-344`).
  - Los tipos de envío llevan `extra="forbid"` (`commons/observabilidad/envio.py:1-17`).
  - Sin claves se usa `ExportadorNulo` (`langfuse.py:177-189`).
- **¿Cuadra el libro de gasto con Langfuse?**
  - **R0:** libro 2,1650 USD, Langfuse 2,165 (`medidas.md:98`).
  - **R1:** 16,8905 USD en 36 delegaciones en los dos (`medidas.md:138,151`; `verification.md:1179`).
    - Antes de reparar F-117 y F-119 no cuadraban: el libro decía 12,9389 USD en 28 delegaciones y Langfuse 14,0463 en 29 (`verification.md:1177`).
  - **R2–R5, B4, antes-2 y las generaciones de hoy:** no existe cotejo.
    - En este árbol no hay `backend/.env`, así que **las generaciones de `web.db` no se han enviado a Langfuse**.

---

## 11 · Lo que falta o quedó abierto

- **Tuning:**
  - `PLAN-31 T1` está commiteado sin medir (`6deefe5`).
  - La pasada «antes» repetida (antes-2) paró 3 veces por INV-03.
  - **La pasada «después» no se lanzó** (`medidas.md:259-278`; `EX-06`).
- **Presupuesto de contexto sin ejercitar:**
  - 0 recortes en todas las ejecuciones.
  - El envío medido está en 419 tokens (capítulo 1) y 8.139 de máximo en `web.db`, contra 100.000 (`CLAUDE.md`).
  - `VER-34` y `VER-37`: «No verificable hoy».
- **Revisión humana (H1):** no hecha (`EX-05`).
- **Puntos ciegos asumidos:** 14 activos (`verification.md:706`, tabla desde `:948`). Por ejemplo:
  - PC-3: la fiabilidad del Juez sin medir.
  - PC-5: VER-39 compara léxico, no sentido.
  - PC-9: invención de lo que el recorte dejó fuera.
  - Además, la cascada reescribe más de lo necesario, a propósito (VER-118).
- **Limitaciones del producto:**
  - **Una novela entregada no se puede regenerar desde la web** (F-91, abierto). Al entregar se borra la ficha (SPEC-25 RF-21), y sin ficha no hay con qué montar el contexto del Escritor. La terminal lo sortea con `--ficha` (F-147) (`docs/proceso/trade-offs.md:94`, T-11).
  - Pedir un cambio desde la web falla (F-126).
  - Cambiar un imprescindible no cambia sus palabras clave (F-125).
  - El inspector visual no devuelve nada al Escritor (EX-04, el único bloqueante que queda contra el enunciado, `cobertura-examen.md:44-48,70`).
- **Hallazgos F abiertos:** F-28, 48, 55, 57, 66, 91, 101, 110, 112, 116, 120, 125, 126, 130, 134, 135, 142, 145, 154 y 155 (`grep -n "\*\*Abierto" docs/verification.md`).
  - F-110, F-112 y F-116 son contraejemplos de TLC sin arreglo en el código.
- **Specs sin aplicar:**
  - `SPEC-09`: `en_revision`.
  - `SPEC-01`, 21, 22, 23, 24, 29, 31 y 33: `aprobada`.
  - `SPEC-23` dice que pasa a `aplicada` con B4, que ya está hecho: está desfasada.
- **Documentos desfasados:**
  - `verification.md:698-700` («0 implementados»).
  - `cobertura-examen.md` EX-13 («`frontend/` no existe»).
  - `AGENTS.md` («`ejemplos/novela-ejemplo.pdf` no existe»; sí existe, commit `a991278`).
  - `diagramas.md:41` (la puerta de publicación «sin construir»).

---

## Lo que no existe hoy y no se puede enseñar

- **Ejemplo real de palabra vetada detectada y reescrita, con su texto.** El único caso real, F-59, fue un falso positivo, y su base no está en disco.
- **Pasada «después» del tuning.** No se lanzó.
- **Desglose por agente de R1, R5 y B4, y sus bases.** Los worktrees ya no existen.
- **Una novela entera con el Escritor solo en sonnet o solo en opus.**
- **Cotejo libro de gasto contra Langfuse** fuera de R0 y R1. Las generaciones de hoy no subieron a Langfuse: no hay `backend/.env` en este árbol.
- **La comprobación «versión 1 idéntica byte a byte»** de la demo.
- **Un cambio del lector lanzado desde la web** (F-126).
- **Regenerar una novela ya entregada** (F-91).
- **`presentacion/` con el vídeo de demo** (`README.md:90`: «Pendiente»).
- **Volver a ejecutar TLC en esta máquina:** falta `java`. Tampoco se ha vuelto a pasar TLC tras los arreglos de CE-14 y CE-15.
- **Revisión humana (H1).**
- **Recuento de validadores implementados al día en `docs/verification.md`.** Dice 0, y está caducado.
