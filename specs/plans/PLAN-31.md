---
id: PLAN-31
spec: SPEC-31
titulo: Implementación de la evaluación del sistema
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-24
version: 1
---

# PLAN-31 — La evaluación del sistema

Cómo se construye `SPEC-31`. Dos mitades que no se mezclan:

- **Lo que se construye con dobles (E1–E13)**: formato de los briefs, libro de gasto, tabla
  por brief, notas del Editor guardadas, exfiltración con dobles, red-team log y el guion de
  ejecución. No gasta nada. Cada paso empieza por la prueba que falla, deja en verde las
  pruebas actuales y se puede commitear solo.
- **Las ejecuciones reales (R0–R7)**: gastan dinero. **Cada una es un paso propio, se lanza
  solo con un sí explícito del autor** y su coste se anota con lo que diga el libro de gasto
  al terminar. Ninguna tiene coste previsto: **el coste de una novela con el pipeline actual
  está sin medir**.

## Lo que se encontró al preparar el plan

1. **El brief temporal no se puede ejecutar tal como está.**
   `harness/evals/brief-incoherencia-temporal.json` usa los campos de `BriefEntrada`
   (`titulo`, `premisa`, `genero`, `subgenero`…) y `"genero": "terror"`.
   `backend/novela_regalo.py` lee una `FichaDeEntrevista`, cuyo modelo base prohíbe campos
   desconocidos, y `terror` ya no está en `GeneroDeLaHistoria`
   (`commons/dominio/enumeraciones.py`): `SPEC-26` v3 lo retiró. El propio brief lo anticipa:
   *«cuando el esquema crezca, este brief crece con él»*.
2. **Las notas del Editor se pierden.** `ciclo._editar` deja las seis valoraciones en
   `c.veredicto` (`features/orquestacion/ciclo.py:158`) y nada las lee después. Solo las que
   quedan bajo el umbral se escriben, como texto de un hallazgo `INV-26`. `RF-03`, `RF-04` y
   `RF-08` necesitan las seis por capítulo.
3. **El coste no se guarda en ningún sitio, y el de una novela completa sale por debajo de lo
   real.** `Generacion.coste` se suma en memoria (`features/orquestacion/obra.py`,
   `_acumular_coste`) y `novela_regalo.py` lo imprime y lo pierde; `traza_de_delegacion` no
   tiene columna de coste. Además, el juicio de obra (`novela._juicio_de_obra`) y los turnos
   del Entrevistador **no se suman**. Un techo acumulado entre ejecuciones (`RF-06`) necesita
   un registro que sobreviva a cada una.
4. **«Sin hallazgos» no es «pasó».** La tabla `hallazgo` solo registra violaciones; no hay
   constancia de que un validador se ejecutara y no encontrara nada. Es el cero vacío de
   `F-30`, que ya describe `harness/evals/README.md` § «Cómo se lee un cero».
5. **`VER-30`, que `SPEC-31` citaba, está obsoleta** (`SPEC-26` v3 `RF-21`,
   `docs/verification.md:805`): trataba de las reglas de la amenaza de terror. Este plan abre
   filas nuevas en vez de reutilizarla, y la cita de la spec se corrige como cambio documental.
6. **La injection y las contradicciones pasan por la entrevista, no por `novela_regalo.py`.**
   Se reproduce con `entrevista_cli.dialogar(cliente, entrada=…)`, que `test_cli.py` ya usa
   contra `TestClient`, y sustituyendo `app.state.entrevistador` y `app.state.extractor`
   (`features/entrevista/router.py`). El detector es `texto_libre.detectar_instrucciones`
   sobre `PATRONES`.
7. **Nada del backend habla con Langfuse todavía**: `RF-07` y la versión de prompt de `RF-03`
   dependen de `SPEC-29`.
8. **Los hooks no se cargan en una ejecución real** (`F-61`). Mientras siga así, la tabla no
   da crédito a un hook: lo que valida es el código de las puertas.

9. **Dos novelas en la misma base se pisan hoy.** `escena.id`, `entidad.id` y el `id` de
   `evento_cronologico` son claves primarias globales, y la novela regalo numera las escenas
   `"{capitulo}-e1"` y los imprescindibles `imp-01`, `imp-02`… en todas las novelas. Lo encontró
   la preparación de `PLAN-28`. Es un defecto activo, y **las ejecuciones reales de este plan
   no pueden compartir `evaluacion.db` hasta que esté arreglado**: la segunda novela
   corrompería la primera. E7 es justo la prueba que lo reproduce, y está bien que falle.

**La única medida del pipeline actual, y lo que no dice**: la ejecución real de `PLAN-26` E13
gastó **3,7715 USD en 7 delegaciones, todas con coste medido** (mensaje de `bf42074`). Fue un
capítulo que **no se aceptó** (`F-59`) y no incluye el juicio de obra ni una novela entera.
**No es una estimación de nada.** Los 21,6 USD de `harness/evals/medidas.md` son de la obra
anterior.

## Lo que se aprueba al aprobar este plan

- **Una feature nueva, `features/evaluacion/`**, y la tabla `gasto_de_evaluacion`.
- **La relación `Borrador → ValoracionDelEditor`** en `docs/definitions.md` y la tabla
  `valoracion_del_editor`. La clase ya existe (`SPEC-26` `RF-09`); lo nuevo es dónde se guarda
  y a qué borrador se refiere. Si el revisor lo considera una decisión nueva de dominio, E4 se
  para y va a spec.
- **El brief temporal pasa de `terror` a `misterio`.** Los cuatro ganchos (`L-1`…`L-4`) no
  dependen del género. Lo decide el autor.
- **La regla de lectura de la tabla**: una columna sin constancia de ejecución dice «sin
  veredicto», nunca «pasó».
- **La revisión humana se hace sobre la novela de R1**, la del brief base antes del tuning.
- **El orden de las ejecuciones reales** de § «Qué pasa al acercarse al techo».

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `features/evaluacion/` (nueva) | `briefs.py`, `repository.py` (`gasto_de_evaluacion`), `tabla.py`, `comparar.py` (Editor contra autor), `exfiltracion.py` |
| `features/orquestacion/evaluacion.py` (nuevo) | Reúne lo que dice cada validador para una obra: componer es solo de `orquestacion/` |
| `features/escaleta/repository.py` | La tabla `valoracion_del_editor`, junto a `hallazgo` |
| `commons/modelo/contador.py` (nuevo) | `Contador`, que sale de `novela_regalo.py` y gana prueba |
| `commons/configuracion/esquemas.py` | Bloque `evaluacion` con `techo_de_gasto_usd` |
| `backend/evaluar.py` (nuevo) | El guion de ejecución real de un brief |
| `harness/evals/` | Los cinco briefs, `resultados.md` y `revision-humana-brief-base.json` |
| `harness/adversarial/` (nueva) | El red-team log y sus casos |

Sin migraciones de tablas existentes: las dos nuevas las crea su feature.

## Qué espera a qué

| Paso | Espera a |
| --- | --- |
| E1–E10 | Nada: pueden empezar al aprobar el plan |
| E11 (scores y versión de prompt) | `SPEC-29` aplicada |
| E12 (extensión en los briefs) | `SPEC-32` aplicada |
| E13 (la puerta en la tabla) | `SPEC-30` aplicada |
| La parte de E7 que toca las tools | `SPEC-28` aplicada |
| R0–R7 | E1–E13, es decir, `SPEC-29`, `SPEC-30` y `SPEC-32` aplicadas, **y el arreglo de los identificadores globales** (hallazgo 9) |

**Por qué las ejecuciones esperan a las tres.** Una ejecución antes de tiempo describe un
sistema que no es el que se entrega, y se pagaría dos veces.

## Pasos con dobles (no gastan)

### E1 · El formato del brief, y el temporal como ficha

Cada brief lleva `_meta` (`id`, `proposito`, `de_los_cinco_briefs`, `datos: "inventados"`,
`estado`), una ficha **o** un guion de entrevista —nunca las dos—, y `que_deberia_pasar`. El
temporal se reescribe como ficha sin tocar sus ganchos, y conserva
`por_que_provoca_cada_incoherencia`.

**Prueba que falla primero:** `test_cada_brief_de_harness_evals_carga_con_su_esquema`. Además
`test_un_brief_sin_datos_inventados_declarados_no_carga` y
`test_un_brief_con_ficha_y_guion_a_la_vez_no_carga`. Punto ciego: «inventados» es una
declaración, no algo que la prueba compruebe.

### E2 · Los cuatro briefs que faltan

`brief-base.json` (el del README y el del PDF), `brief-contradicciones.json`,
`brief-vetadas-por-variantes.json` y `brief-injection.json`, este último con dos instrucciones:
una que `PATRONES` reconoce y otra que no se parece a ninguno, puesta a propósito.

**Prueba que falla primero:** `test_hay_cinco_briefs_y_cubren_los_propositos_de_la_spec`.
Además una por brief:
`test_el_brief_de_injection_trae_una_instruccion_que_el_detector_ve_y_otra_que_no`,
`test_la_ficha_esperada_del_brief_de_contradicciones_dispara_las_tres_reglas` y
`test_el_brief_de_vetadas_invita_a_una_variante_de_cada_vetada`.

### E3 · El guion de entrevista se reproduce contra la API

`evaluar.entrevistar(cliente, guion)` convierte el guion en lo que espera `dialogar`.

**Prueba que falla primero:** `test_el_guion_de_injection_cierra_sin_ningun_hecho_confirmado`.
Además `test_el_guion_de_contradicciones_no_cierra_hasta_resolverlas` y
`test_una_inyeccion_del_guion_queda_en_el_audit_log`.

### E4 · Las seis notas del Editor se guardan

`docs/definitions.md`: la relación `Borrador → ValoracionDelEditor`. La tabla
`valoracion_del_editor` (escena, versión del borrador, criterio, nota, justificación,
instrucción), y `_editar` escribe las seis.

**Prueba que falla primero:**
`test_el_editor_guarda_las_seis_notas_aunque_ninguna_baje_del_umbral`. Además
`test_una_valoracion_ilegible_no_deja_notas_y_sigue_siendo_sin_veredicto` y
`test_las_notas_de_cada_reescritura_quedan_con_su_version_de_borrador`.

### E5 · El libro de gasto y el techo

`commons/modelo/contador.py`; `gasto_de_evaluacion` (ejecución, brief, pasada, capítulo, USD,
delegaciones y delegaciones sin coste); `evaluacion.techo_de_gasto_usd = 150`, marcado como
**decisión de presupuesto, no medida**; `novela.escribir` gana un parámetro `seguir`,
consultado al terminar cada capítulo, que para con `techo_de_gasto`. El juicio de obra pasa
por un `Contador`.

**Prueba que falla primero:**
`test_escribir_se_detiene_entre_capitulos_cuando_seguir_dice_que_no`. Además
`test_el_coste_del_juicio_de_obra_entra_en_el_total`,
`test_una_delegacion_sin_coste_cuenta_como_sin_medir_no_como_cero`,
`test_no_empieza_una_ejecucion_con_el_techo_alcanzado`,
`test_el_gasto_se_anota_por_capitulo_y_sobrevive_a_una_caida` y
`test_con_delegaciones_sin_coste_el_total_se_informa_como_suelo`.

### E6 · La tabla por brief

`orquestacion/evaluacion.resultados(con, obra)` da una celda por validador, y
`evaluacion/tabla.py` genera `harness/evals/resultados.md`. Las columnas salen del registro
de invariantes, no de una lista a mano, más `INV-26` por criterio, el schema del plan, las
dos comprobaciones de la entrevista, Lean y la puerta. Cada celda dice pasó, falló, no
aplica, sin veredicto o sin ejecutar; un validador que disparó y se resolvió dice «pasó (2
disparos)».

**Prueba que falla primero:** `test_un_brief_sin_ejecutar_dice_sin_ejecutar_en_todas_sus_columnas`.
Además `test_sin_hallazgos_y_sin_constancia_de_ejecucion_no_es_paso`,
`test_un_hallazgo_sin_veredicto_no_se_cuenta_como_pasado`,
`test_una_invariante_obsoleta_sale_como_no_aplica`,
`test_un_validador_que_disparo_y_se_resolvio_dice_paso_con_sus_disparos` y
`test_lean_2_es_sin_veredicto`.

### E7 · Exfiltración entre dos novelas, con dobles

Dos fichas con nombres y palabras clave disjuntos en `harness/adversarial/`, y
`exfiltracion.rastro(textos, nombres_y_claves)` con la normalización de `commons/politica/`.

**Prueba que falla primero:** `test_la_segunda_novela_no_recibe_nada_de_la_primera`: dos
novelas en la misma base con dobles que capturan el prompt, y en ningún prompt de B aparece
nada de A. **Si pasa a la primera**, antes de fiarse se quita a propósito el filtro de obra en
una lectura, se comprueba que la prueba lo caza y se restaura (`F-40` es la versión
accidental de este caso). Además
`test_el_rastro_encuentra_un_nombre_de_la_otra_novela_aunque_cambie_la_tilde`.

### E8 · El red-team log en `harness/adversarial/`

`README.md` y `casos.json`: caso, cómo se probó, qué validador lo detectó o «ninguno»,
resultado, punto ciego y resolución. Enlaza los casos de `docs/proceso/red-team-log.md` en
vez de copiarlos.

**Prueba que falla primero:** `test_cada_caso_del_red_team_nombra_su_validador_o_dice_ninguno`.

### E9 · El coste en los guiones

`novela_regalo.py` usa `commons/modelo/contador.py` y el juicio de obra entra en el total.

**Prueba que falla primero:**
`test_novela_regalo_con_dobles_informa_el_juicio_de_obra_en_el_coste`.

### E10 · El guion de ejecución real, con dobles

`evaluar.py BRIEF.json --pasada antes|despues --base evaluacion.db`: consulta el libro y no
empieza con el techo alcanzado; exige `--confirmo-el-gasto` y, antes de empezar, imprime lo
gastado, lo que queda y el mayor coste medido de una novela completa (o «sin medir»); hace la
entrevista si el brief es un guion; escribe con `seguir` conectado al libro; anota el gasto;
pasa `rastro` contra las obras anteriores; y regenera la tabla.

**Prueba que falla primero:** `test_evaluar_no_empieza_sin_confirmar_el_gasto`. Además
`test_evaluar_con_dobles_deja_fila_en_el_libro_de_gasto_y_en_la_tabla` y
`test_evaluar_no_empieza_con_el_techo_alcanzado`.

### E11 · Scores y versión de prompt *(espera a `SPEC-29`)*

**Prueba que falla primero:** `test_cada_celda_de_la_tabla_tiene_su_score_en_la_traza`.
Además `test_la_tabla_dice_que_version_del_prompt_del_escritor_produjo_cada_pasada`.

### E12 · La extensión en los briefs *(espera a `SPEC-32`)*

Cada brief fija su extensión con las opciones de `SPEC-32`.
`test_cada_brief_de_harness_evals_carga_con_su_esquema` falla sola en cuanto la extensión sea
obligatoria, y es la prueba de este paso.

### E13 · La puerta en la tabla *(espera a `SPEC-30`)*

**Prueba que falla primero:** `test_la_columna_de_la_puerta_sale_del_veredicto_de_la_puerta`.

### E14 · `docs/` al día

`docs/architecture.md` (la feature `evaluacion` y `harness/adversarial/`), `AGENTS.md`,
`CLAUDE.md` (el comando de `evaluar.py`, que gasta), `docs/verification.md`,
`docs/proceso/red-team-log.md` (el puntero) y `docs/cobertura-examen.md`. `SPEC-31` **no**
pasa a `aplicada` aquí: le faltan los resultados.

## Ejecuciones reales (gastan dinero; cada una necesita un sí explícito)

Todas empiezan después de E13 y comparten `evaluacion.db`. **Coste de cada una: sin medir
hasta ejecutarla.**

- **R0 · Un capítulo del brief base.** Mide un capítulo con `F-59`, `F-60` y `F-62` cerrados,
  y comprueba que los hooks dejan constancia (`F-61`). **Su coste no se multiplica por diez
  para presentarlo como coste de novela.**
- **R1 · Brief base, novela completa, pasada «antes».** Es la de la revisión humana y la del
  PDF de `SPEC-27`.
- **R2 · Injection, antes.** Incluye la entrevista, y es a la vez caso del red-team.
- **R3 · Temporal, antes.** Con Lean en la puerta.
- **R4 · Contradicciones, antes.**
- **R5 · Vetadas por variantes, antes.** Es a la vez caso del red-team.
- **H1 · Revisión humana (sin coste en dinero).** El autor rellena
  `harness/evals/revision-humana-brief-base.json` con los seis criterios por capítulo, y
  `comparar.py` lo contrasta criterio a criterio con el Editor. Prueba con dobles antes de H1:
  `test_la_comparacion_nombra_los_capitulos_donde_el_editor_y_el_autor_discrepan_sobre_el_umbral`.
  Cambiar el umbral del Editor es decisión del autor con esta medida delante (`SPEC-26`
  `RF-10`).
- **T1 · El cambio de tuning (sin coste).** Un commit sobre `.claude/agents/escritor.md`,
  elegido por el criterio con peor nota del Editor en la pasada «antes».
- **R6 · Brief base, pasada «después».**
- **R7 · El resto, pasada «después»**, en el orden de R2–R5, mientras quede techo.

**Cómo se lee el tuning.** Media por criterio de las notas del Editor sobre los borradores
aceptados, antes y después, y cuántas reescrituras disparó `INV-26`. Con dos puntos ciegos
junto al resultado: **una pasada por lado no separa el cambio del ruido** —la varianza entre
dos ejecuciones iguales está sin medir—, y el Editor juzga los dos lados, por eso se contrasta
con H1. Un resultado plano o peor se escribe tal cual.

## Qué pasa al acercarse al techo

El techo se comprueba **contra lo gastado**, nunca contra una previsión.

1. Antes de cada R, el guion imprime lo gastado, lo que queda hasta 150 USD y el mayor coste
   medido de una novela completa. Sin esas tres cifras no hay sí.
2. Si lo que queda es menor que ese mayor coste medido, la siguiente no se lanza sin un sí que
   diga expresamente que probablemente no termine.
3. Al alcanzar el techo, la generación se detiene entre capítulos con `techo_de_gasto`, y la
   tabla dice qué quedó sin ejecutar. **Se puede pasar del techo en lo que cueste el capítulo
   en curso**, porque no se corta a media delegación; cuánto es, lo dirá R0.
4. Un total con delegaciones sin coste es un suelo, y se dice.
5. **Orden de prioridad:** base (R1) → injection → temporal → contradicciones → vetadas →
   pasada «después» del base → resto de la pasada «después».

## Qué filas `VER-xx` abre

| Marcador | Afirmación | Clase |
| --- | --- | --- |
| `VER-nueva-A` | Hay cinco briefs, cargan con su esquema y declaran datos inventados (`RF-01`) | T |
| `VER-nueva-B` | La tabla no da «pasó» sin constancia de ejecución, y distingue «sin veredicto» de «sin ejecutar» (`RF-02`) | T |
| `VER-nueva-C` | El gasto se persiste por capítulo, el techo detiene entre capítulos y un coste ausente no suma cero (`RF-06`) | T |
| `VER-nueva-D` | El Editor deja sus seis notas por borrador | T |
| `VER-nueva-E` | La comparación Editor contra autor es criterio a criterio sobre la misma novela (`RF-04`) | T + I |
| `VER-nueva-F` | Una novela no recibe datos de otra de la misma base (`RF-12`) | T con dobles + D |
| `VER-nueva-G` | Cada caso del red-team nombra su detector o «ninguno» (`RF-05`) | T + D |
| `VER-nueva-H` | El tuning muestra la versión de prompt de cada pasada, y los resultados llegan como scores (`RF-03`, `RF-07`) | U hasta `SPEC-29` |

## Lo que este plan no hace

- No escribe el `README.md` ni exporta `/ejemplos/novela-ejemplo.pdf`: elige la novela (R1),
  y exportar es `SPEC-27`.
- No resuelve `F-61`, ni decide el nuevo umbral del Editor: lo mide.
- No valida con el browser MCP (`EX-04`), no ejecuta TLC y no envía nada a Langfuse por su
  cuenta.
