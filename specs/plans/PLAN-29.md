---
id: PLAN-29
spec: SPEC-29
titulo: Implementación de la observabilidad en Langfuse, y qué sube y qué no
estado: aprobada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 1
---

# PLAN-29 — La observabilidad en Langfuse

Cómo se construye `SPEC-29`. Cada paso empieza por la prueba que falla, deja la suite en
verde y se puede commitear solo. **Ningún paso llama a Langfuse ni al modelo real**: todo va
contra un exportador doble, salvo E13, que **necesita la instancia y un sí explícito**.

**La instancia no existe.** Crearla es un paso manual del autor, dentro de E13: un proyecto en
Langfuse Cloud, con sus claves en `backend/.env` (`RF-08`, `RF-10`). Hasta entonces el código
funciona sin claves: no envía nada y lo dice.

## Lo que se encontró al preparar el plan

1. **El valor de la sesión ya nace con la entrevista, pero no viaja.**
   `entrevista/repository.py` (`crear`) genera `obra-<10 hex>` al abrir la entrevista, que es
   lo que pide `RF-12`. Pero cerrar la entrevista devuelve solo la ficha, y `novela_regalo.py`
   usa `--obra` con `obra-regalo` por defecto. `RF-12` no pide un valor nuevo: pide que este
   llegue a la generación.
2. **Los identificadores de capítulo los decide el modelo.** `CapituloDelPlan.id` solo exige
   `min_length=1`, así que un plan podría meter un nombre en el identificador. A Langfuse va
   **el número de capítulo**, nunca el id del plan; y la sesión es una huella del id de la obra,
   no el id.
3. **`tokens_estimados` guarda los tokens del sobre en las delegaciones reales**, con `or 0`
   (`bucle.py`, `ciclo.py`), así que un dato ausente acaba en cero. Y `VER-41`, que
   `docs/architecture.md` § "La traza de una llamada al modelo" sigue citando, está **retirado**
   por `SPEC-14` y lo sustituye `VER-61`. Consecuencia: **lo que sube lee `medidas` campo a
   campo, y lo que falta se queda ausente** (`RF-03`). Renombrar los campos de la traza no es
   de esta spec; queda anotado en E12.
4. **Una respuesta ilegible pierde el coste que sí se pagó**: `proveedor.py` interpreta el
   resultado antes de leer las medidas del sobre.
5. **Las notas del Editor solo viven en memoria** (`ciclo._editar`); los scores por criterio se
   sacan donde el `Ciclo` todavía existe, en `obra._intentar`.
6. **`INV-22` no deja hallazgo**: su score sale del `Ciclo`.
7. **El nivel de una vetada se pierde antes de la puerta** (`novela.py` pasa solo las formas),
   y el audit log guarda la vetada en claro, así que su detalle no se puede reutilizar para
   Langfuse cuando es de la novela (`RF-06`).
8. **Las claves llegarían al subproceso**: `_ejecutar_proceso` copia todo el entorno.
9. **No hay SDK, ni `.env`, ni `.env.example`.** `.gitignore` ya ignora `backend/.env` y deja
   pasar `backend/.env.example`.
10. **La API de ingestión de Langfuse está en desuso y se retira el 2026-11-16**, según su
    documentación pública. El plan usa el SDK de Python v4, encerrado en un solo módulo.
11. **Ni tools ni Lean existen en el backend todavía**: el plan deja preparados el span de tool
    y el score «sin veredicto», y conectarlos es de `PLAN-28` y `PLAN-30`.
12. **Las regeneraciones todavía no se ejecutan** (`SPEC-23` en revisión). `RF-01` se cumple
    por construcción: toda generación de una obra cae en la sesión de esa obra.

## Decisiones que la spec no toma y el plan necesita

**Aprobar este plan es aprobar estas cinco:**

- **La sesión es `ses-` más los 16 primeros caracteres hexadecimales del sha256 del id de la
  obra**: determinista, así que entrevista y generación caen en la misma sin guardar nada, y
  opaca aunque alguien pase un `--obra` con un nombre.
- **Una traza por generación y otra por turno de entrevista.** Dentro de la de generación, un
  span `planificacion`, uno por capítulo con su número, y de ellos un span por cada llamada a un
  rol; el juicio de obra va bajo `cierre`.
- **La versión de un prompt es la huella de su texto**: los 12 primeros caracteres del sha256
  de la definición del agente y las plantillas que usa. Nace del repositorio (`RF-13`) y cambia
  si cambia una coma.
- **Una vetada que no es global sube como `vetada-<nivel>-<rowid>`.** No un hash de la forma:
  el hash de un nombre corto se revierte con un diccionario de nombres.
- **Nunca se envía el campo `model`; los modelos van en metadata.** Si se envía el modelo sin
  coste, Langfuse puede calcular un coste propio por su tabla de precios: sería una estimación
  presentada como dato. Que Langfuse lo haga **no está comprobado**: lo mira E13.

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `commons/observabilidad/` (nuevo) | `envio.py` (el límite como tipos), `exportador.py` (interfaz, nulo y doble), `observacion.py` (`SesionObservada`), `perdidas.py` (tabla `envio_perdido`), `credenciales.py` (lee `backend/.env`), `langfuse.py` (el adaptador del SDK). Lo usan dos features |
| `features/orquestacion/prompts.py` (nuevo) | El registro de plantillas con su huella |
| `features/orquestacion/observar.py` (nuevo) | De los resultados salen los scores |
| `features/orquestacion/novela.py`, `obra.py` | Abrir la traza y los spans, envolver los agentes |
| `features/entrevista/service.py`, `router.py` | Una traza por turno, en la sesión de su obra |
| `features/politica/repository.py` | `Vetada` gana `id` |
| `features/verificacion/puertas.py` | `INVARIANTES_DE_LA_PUERTA`: para enviar «pasa» hay que saber qué se miró |
| `commons/modelo/proveedor.py` | Medidas de una respuesta ilegible; entorno del subproceso sin claves ni telemetría |
| `backend/.env.example`, `requirements.txt` | Nombres de variables; `langfuse` con versión mayor fijada |
| `backend/novela_regalo.py`, `backend/entrevista_cli.py` | El exportador real si hay claves; el id de la obra al cerrar la entrevista |

Sin migraciones de tablas existentes ni cambios en `docs/definitions.md`: dos tablas nuevas,
`envio_perdido` y `version_de_prompt_enviada`. **Choque posible con `PLAN-32`**, que también
toca `novela.py`: van en serie.

## Pasos

### E1 · El transporte: el coste de lo ilegible y un entorno limpio

`RespuestaIlegible` gana `medidas`, calculadas antes de interpretar. `_ejecutar_proceso` quita
del entorno todo lo que empiece por `LANGFUSE_` y `CLAUDE_CODE_ENABLE_TELEMETRY` (`RF-11`).

**Prueba que falla primero:** `test_una_respuesta_ilegible_conserva_las_medidas_del_sobre`.
Además `test_la_delegacion_no_hereda_las_claves_de_langfuse`,
`test_la_telemetria_de_claude_code_queda_apagada_en_la_delegacion`,
`test_settings_no_enciende_la_telemetria` y
`test_una_delegacion_ilegible_deja_su_coste_en_la_traza`.

### E2 · El límite, escrito como tipos

`TrazaEnviada`, `SpanEnviado`, `ScoreEnviado`, `VersionDePrompt`: sus campos son **la columna
izquierda de la tabla de la spec y nada más**. `None` se queda ausente, nunca 0. Un score lleva
`valor` **o** `categoria` (`pasa | falla | sin_veredicto | no_aplica`).

**Prueba que falla primero:** `test_un_span_no_acepta_campos_fuera_de_la_lista`. Además
`test_un_dato_ausente_se_queda_ausente_y_no_en_cero`,
`test_la_sesion_es_una_huella_opaca_y_estable_de_la_obra`,
`test_un_score_sin_veredicto_no_es_un_aprobado` y
`test_un_score_no_lleva_valor_y_categoria_a_la_vez`.

### E3 · La interfaz, su doble y la sesión observada

`ExportadorNulo` y `ExportadorEnMemoria` (que puede portarse mal a petición).
`SesionObservada` envuelve cualquier agente, mide y emite un span **sin guardar prompt ni
respuesta**, y deja pasar `nombre`, `agente`, `reglas` y `entorno` en lectura y escritura. Si
el exportador revienta, se guarda una fila en `envio_perdido` con **la clase del error, no su
mensaje**, y la llamada devuelve lo mismo (`RF-09`).

**Prueba que falla primero:** `test_la_sesion_observada_devuelve_lo_mismo_que_la_sesion`.
Además `test_la_sesion_observada_no_guarda_el_prompt_ni_la_respuesta`,
`test_la_sesion_observada_deja_pasar_reglas_entorno_y_nombre`,
`test_una_excepcion_del_modelo_sale_igual_y_deja_span_con_su_clase`,
`test_si_el_exportador_revienta_la_llamada_devuelve_igual_y_queda_una_perdida` y
`test_la_perdida_guarda_la_clase_del_error_y_no_su_mensaje`.

### E4 · Los prompts: del repositorio a Langfuse

`prompts.registro()` asigna a cada rol su `.claude/agents/<rol>.md` y sus plantillas sin
rellenar; solo se envían las huellas nuevas (`RF-05`, `RF-13`).

**Prueba que falla primero:** `test_cada_agente_del_pipeline_tiene_su_version_de_prompt`.
Además `test_cada_fichero_de_claude_agents_esta_en_el_registro`,
`test_la_version_cambia_si_cambia_una_coma_y_no_si_no_cambia`,
`test_lo_que_sube_es_la_plantilla_sin_rellenar` y `test_una_version_ya_enviada_no_se_reenvia`.

### E5 · La generación como traza

`novela.escribir` y `obra.generar_obra` ganan `observacion=None`; **sin observación, nada
cambia**. Con ella: la traza en su sesión, los agentes envueltos, los spans de planificación,
capítulo y cierre, y los agregados por capítulo y novela —un agregado con alguna llamada sin
coste se marca como suelo; sin ninguna, se envía ausente (`RF-03`)—.

**Prueba que falla primero:** `test_una_generacion_es_una_traza_con_un_span_por_rol`. Además
`test_los_spans_de_rol_cuelgan_de_su_capitulo`, `test_el_coste_de_cada_llamada_es_el_del_sobre`,
`test_el_agregado_del_capitulo_con_una_llamada_sin_coste_es_suelo_y_lo_dice`,
`test_cada_span_dice_su_version_de_prompt`,
`test_dos_generaciones_de_la_misma_obra_comparten_sesion` (`RF-01`) y
`test_con_el_exportador_caido_la_novela_termina_igual_y_deja_perdidas` (`RF-09`).

### E6 · Los scores de los validadores

Del `Ciclo`: cada invariante de la puerta (`pasa`, `falla`, `sin_veredicto`), `INV-22` con el
número de nombres mal escritos —nunca los nombres—, `INV-23` por imprescindible, `schema`, y
`INV-26.<criterio>` con la nota. Del cierre: `INV-24`, `INV-25` e `INV-27`. De las rondas del
plan: `schema.plan`, `cobertura.plan` y `revisor.plan`. **Nada de `Hallazgo.descripcion` sube**,
porque cita el texto.

**Prueba que falla primero:** `test_la_lista_de_la_puerta_coincide_con_la_que_verificar_puede_emitir`.
Además `test_cada_invariante_de_la_puerta_da_un_score_pasa_o_falla`,
`test_una_nota_del_editor_es_un_score_numerico_por_criterio`,
`test_un_editor_ilegible_es_sin_veredicto_y_no_aprobado`,
`test_un_fallo_de_contrato_es_score_schema_falla`, `test_inv24_inv25_inv27_llegan_al_cerrar` y
`test_las_rondas_del_plan_dan_scores_de_schema_cobertura_y_revisor`.

### E7 · Las vetadas, con su nivel

`Vetada` gana `id`. Un score `INV-21` por coincidencia, siempre con su nivel, con el término
solo si es global (`RF-06`). El audit log no cambia.

**Prueba que falla primero:** `test_vetadas_para_devuelve_el_id_de_cada_forma`. Además
`test_una_coincidencia_global_sube_con_su_termino`,
`test_una_coincidencia_de_novela_sube_con_su_nivel_y_su_id_y_sin_el_termino`,
`test_una_coincidencia_de_franja_no_lleva_el_termino` y
`test_cada_coincidencia_esta_en_el_audit_log_y_en_el_envio`.

### E8 · La entrevista, en la misma sesión

Cada turno es una traza en la sesión de su obra, y cada llamada al Entrevistador un span. El
router lee una fábrica de `app.state.observabilidad`; si no hay, observación nula.

**Prueba que falla primero:** `test_un_turno_es_una_traza_en_la_sesion_de_su_obra`. Además
`test_la_entrevista_y_la_generacion_de_la_misma_obra_comparten_sesion`,
`test_un_turno_con_ficha_invalida_da_score_schema_falla` y
`test_el_router_sin_observabilidad_sigue_igual`.

### E9 · El límite, comprobado (`RF-07`)

Una entrevista con datos de destinatario **inventados y únicos** —nombre, edad, rasgo,
recuerdo, mascota, texto libre, hecho propuesto, **dedicatoria** (`SPEC-32` `RF-05`), vetada de
novela y nombre vetado—, dos turnos, un capítulo con dobles que **meten esos datos** en el plan,
el texto, el resumen y la justificación del Editor, y el cierre; todo contra
`ExportadorEnMemoria`.

**Pruebas:** `test_nada_del_destinatario_sube_a_langfuse`, que busca cada dato tal cual, en
minúsculas, sin acentos y por nombre de pila; y
`test_todo_lo_que_sube_tiene_solo_campos_de_la_lista`, para que un campo añadido en el futuro
no se cuele. **Punto ciego**, el de `VER-69`: busca cadenas concretas, y no ve lo que el SDK
añada por su cuenta; eso lo mira E13.

### E10 · El adaptador del SDK, las claves y `.env.example`

`credenciales.leer` lee `backend/.env` **sin escribir en `os.environ`**. `crear_exportador`
devuelve el nulo si faltan claves, o `ExportadorLangfuse`, que importa `langfuse` en su
constructor y acepta un SDK inyectable; **nunca `input` ni `output`, y nunca `@observe`**, que
captura argumentos. `vaciar(timeout)` con un hilo y `join`, para que `RF-09` no dependa del SDK.
`backend/.env.example` con las tres variables sin valor, y `langfuse>=4,<5`.

**Prueba que falla primero:** `test_sin_claves_no_hay_exportador_real_y_lo_dice`. Además
`test_las_claves_se_leen_de_backend_env_y_no_entran_en_os_environ`,
`test_el_adaptador_traduce_un_span_sin_input_ni_output`,
`test_el_adaptador_no_manda_el_campo_modelo`, `test_un_flush_que_no_vuelve_es_una_perdida`,
`test_env_example_lista_las_variables_y_ningun_valor` y `test_backend_env_esta_en_gitignore`.
Lo que no prueban —que el SDK real tenga esas firmas— lo comprueba E13.

### E11 · Los puntos de entrada

`novela_regalo.py` crea el exportador, pasa la observación, imprime `=== LANGFUSE ===` con
«enviado», «apagado: motivo» o las pérdidas, y envía un score por cada línea del registro de
hooks. `entrevista_cli.py` enseña el id de la obra al cerrar.

**Prueba que falla primero:** `test_al_cerrar_la_cli_ensena_el_identificador_de_la_obra`.
Además `test_el_estado_de_langfuse_se_informa_sin_claves` y
`test_los_hooks_del_registro_dan_un_score_cada_uno`.

### E12 · `docs/` y spec al día

`docs/architecture.md` (sección «Lo que sube a Langfuse», y corregir que `VER-41` está retirado
y que `tokens_estimados` guarda el sobre), `docs/verification.md`, `docs/cobertura-examen.md`
(`EX-02`), `AGENTS.md` (`commons/observabilidad/` y `backend/.env.example`) y `CLAUDE.md`.
`SPEC-29` **no** pasa a `aplicada` hasta E13.

### E13 · Contra la instancia real (necesita la instancia y un sí explícito)

**Paso manual del autor:** crear el proyecto en Langfuse Cloud y poner las tres claves en
`backend/.env`. Después: **(a) sin gastar modelo**, repetir el recorrido de E9 con el
exportador real y comprobar en la interfaz la sesión, los spans, los scores, las versiones de
prompt, que **buscando cada dato inventado no aparece nada** y que una llamada sin coste **no
muestra coste inferido**; y con un host que no responde, que termina y deja `envio_perdido`.
**(b) Gasta dinero:** `novela_regalo.py` con una ficha inventada y `--capitulos 1`, más un turno
de entrevista con la misma obra. Lo que no llegue se dice «sin medir».

## Qué filas `VER-xx` abre

- **`VER-nueva-A`**: nada del destinatario sube a Langfuse (`RF-07`). Punto ciego: datos
  transformados y lo que añada el SDK.
- **`VER-nueva-B`**: una sesión por novela, con la entrevista y las generaciones (`RF-01`,
  `RF-12`).
- **`VER-nueva-C`**: tokens, coste y latencia por llamada, con agregados; lo ausente queda
  ausente (`RF-03`).
- **`VER-nueva-D`**: cada validador da un score, y «sin veredicto» no es un aprobado (`RF-04`).
- **`VER-nueva-E`**: los prompts se versionan desde el repositorio y cada span dice su versión
  (`RF-05`, `RF-13`).
- **`VER-nueva-F`**: cada coincidencia de vetada, en el audit log y en Langfuse con su nivel
  (`RF-06`).
- **`VER-nueva-G`**: con Langfuse caído la generación sigue y la pérdida queda (`RF-09`).
- **`VER-nueva-H`**: las claves solo en `backend/.env`, fuera del subproceso, y la telemetría
  de Claude Code apagada (`RF-08`, `RF-11`).

## Lo que no se pudo comprobar

Ni `langfuse` ni `python-dotenv` están instalados. **Comprobado en la documentación pública**:
las URL de la nube (EU y US), la autenticación, la retirada de la API de ingestión, y que el SDK
v4 lee `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` y `LANGFUSE_BASE_URL` y tiene `flush()`.
**Sin comprobar**, y lo resuelve E13 o la lectura del SDK en E10: la firma exacta de los
scores, cómo se fija la sesión en v4, el enlace entre prompt y observación, los instantes
explícitos, si `flush` tiene timeout, si el SDK informa de los fallos de exportación, si
Langfuse infiere el coste por modelo, y si su OpenTelemetry exporta spans ajenos. El nombre
`CLAUDE_CODE_ENABLE_TELEMETRY` se cita de la documentación de Claude Code y no se ha probado.

## Lo que este plan no hace

- No crea la instancia: es el paso manual de E13.
- No conecta el score de Lean ni los spans de tools (`PLAN-30`, `PLAN-28`), ni implementa las
  regeneraciones (`SPEC-23`).
- No renombra `tokens_estimados` ni revive `VER-41`: lo deja anotado.
- No cambia qué guarda el audit log.
