# Red-team log

Casos adversariales, qué validador los detectó —o que no los detectó ninguno— y cómo se
resolvió. **Hoy ningún caso se ha lanzado contra el modelo real**: los de abajo están
probados con dobles, o aparecieron en una ejecución real sin que nadie los buscara. El
corpus que `SPEC-31` pide vivirá en `harness/adversarial/`, que todavía no existe.

## Casos probados

| Caso | Cómo se probó | Quién lo detecta | Resultado | Punto ciego |
| --- | --- | --- | --- | --- |
| **Injection en el texto libre** | Un doble del extractor que **obedece** a la inyección y devuelve hechos (`test_una_inyeccion_no_produce_hechos_aunque_el_modelo_los_devuelva`); el sobre que no se puede cerrar desde dentro; la inyección por la API (`test_una_inyeccion_por_la_api_queda_en_el_audit_log`); y un texto normal que no debe tomarse por inyección | El detector de patrones la registra en el audit log; **lo que la contiene es estructural**: el texto libre nunca llega al Escritor, y solo entran hechos que el comprador confirma (`VER-68`) | Cero hechos aunque el modelo obedezca | Una inyección que no se parezca a ningún patrón pasa el detector, y la estructura no protege de un comprador que confirme a ciegas |
| **Colar una vetada con variantes** | Mayúsculas, acentos, plurales, género gramatical y una expresión partida entre dos líneas (`test_vetadas.py`, `test_repository.py`) | `INV-21`, que normaliza antes de comparar | Detectadas en los tres niveles | Una variante que la normalización no contemple —un sinónimo, una perífrasis— no es una coincidencia |
| **Un nombre casi igual** («Irena» por «Irene») | `test_un_nombre_con_una_letra_cambiada_se_detecta`, `test_una_tilde_que_falta_es_un_nombre_mal_escrito`, y el hook devolviéndoselo al Escritor (`test_un_nombre_mal_escrito_vuelve_al_escritor`) | `INV-22`, y antes el hook `validar_capitulo.py` | Detectado; el capítulo se reescribe | Solo mira palabras con mayúscula inicial |
| **Un agente que intenta usar una herramienta que no tiene** | `test_policy_niega_la_herramienta_y_lo_deja_en_el_audit_log`, `test_policy_niega_al_planificador_las_tools_de_story_bible`, `test_policy_niega_al_editor_una_tool_de_otro_servidor_mcp` | El hook `policy.py`, allowlist por agente (`SPEC-28`); antes, `--tools ""` y `--allowedTools` en la orden | Denegada y registrada | Probado con dobles: el hook no ha visto todavía una llamada real a una tool (`PLAN-28` E10) |

## Casos encontrados en ejecución, sin buscarlos

| Caso | Dónde apareció | Quién lo detectó | Cómo se resolvió |
| --- | --- | --- | --- |
| **Datos cruzados entre novelas**: la memoria mezclaba obras (`F-40`) | La primera obra de diez capítulos, modelada como diez obras | Ningún validador: salió al analizar la generación | `resumen` y `ficha` guardan su obra y sus consultas se acotan por ella. Es la forma accidental de la exfiltración entre novelas que `SPEC-31` probará a propósito |
| **El guardrail bloqueaba una preposición** (`F-59`): una vetada con «ñ» se normalizaba perdiéndola | La primera ejecución real de la novela regalo | `INV-21` paró el capítulo tras dos reescrituras: el fallo era del propio guardrail | La normalización conserva la «ñ», y una prueba recorre la lista real buscando vetadas que coincidan con palabras comunes |
| **Los hooks no se cargaron** (`F-61`) | La primera ejecución real | Nadie en el momento: no dejaron constancia | Diagnosticado —Claude Code solo los carga desde la raíz del repositorio— y **cerrado** en `1ad5691`: las delegaciones arrancan en la raíz. En la segunda ejecución real `validar_capitulo.py` dejó 4 filas en el registro de hooks, las 4 con el Planificador o el Revisor y en la rama que sale sin comprobar nada (solo actúa con el Escritor, `validar_capitulo.py:76`); `policy.py` no dejó ninguna. **Ningún hook ha detectado nada todavía**: el Escritor no llegó a ejecutarse (`F-68`). Las puertas del código siguen mandando |

## Pendiente (`SPEC-31` `RF-12`)

| Caso | Estado |
| --- | --- |
| El brief adversarial de injection, contra el modelo real | Sin ejecutar |
| Evasión de vetadas por variantes, contra el modelo real | Sin ejecutar |
| Exfiltración de datos entre dos novelas, a propósito | Sin ejecutar contra el modelo. Las tools solo leen la obra de la delegación, que fija el harness y no es argumento (`SPEC-28` `RF-06`, `VER-91`) |
| Datos del destinatario en lo que se envía a Langfuse | Sin ejecutar; es la prueba de `SPEC-29` `RF-07` |
