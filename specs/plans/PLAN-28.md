---
id: PLAN-28
spec: SPEC-28
titulo: Implementación de las tools de lectura de la story bible
estado: aplicada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 1
fecha_aplicacion: 2026-09-24
commit_de_aplicacion: d8c9477
---

# PLAN-28 — Las tools de lectura de la story bible

Cómo se construye `SPEC-28`. Cada paso empieza por la prueba que falla, deja la suite en
verde y se puede commitear solo. **Ningún paso llama al modelo real**: todo va contra dobles,
contra procesos locales o contra el servidor lanzado como proceso, salvo E10, que gasta
dinero y necesita un sí explícito.

## Lo que se encontró al preparar el plan

1. **Hoy no hay ni una línea de MCP ni de tools en el código.** Los siete agentes de
   `.claude/agents/` declaran `tools: []`, y
   `test_agentes.py::test_cada_agente_del_pipeline_existe_y_no_tiene_herramientas` lo exige.
2. **Cómo se exponen tools a `claude -p`, comprobado con `claude --help` (2.1.274).** El CLI
   admite `--mcp-config`, `--strict-mcp-config`, `--allowedTools`, `--disallowedTools`,
   `--tools` (*«Use "" to disable all tools»*, del conjunto integrado) y `--settings`. **Sin
   una sesión real no se pudo comprobar, y lo mira E10**: que una tool MCP se llame
   `mcp__<servidor>__<tool>`; que `--tools ""` deje vivas las tools MCP; que el hook
   `PreToolUse` se dispare con ellas; que Claude Code pase su entorno al servidor stdio; y
   que un `tools:` del frontmatter se aplique con `--agent`. Esto último importa porque
   `omitClaudeMd` ya se ignoró en silencio una vez (`F-20`): el plan pone las barreras en la
   orden y no confía en el frontmatter.
3. **La orden se pasa como lista a un `.CMD`** (`commons/modelo/proveedor.py`), así que un
   JSON con comillas como argumento de `--mcp-config` corre el riesgo de pasar por
   `cmd.exe`. La configuración MCP va **en un fichero**, nunca como cadena.
4. **`F-61` sigue abierto**: Claude Code solo carga `.claude/settings.json` si la sesión
   arranca en la raíz del repositorio. `SesionDelegada` hereda el `cwd` del guion
   (`backend/`), así que el hook de policy **no actúa sobre el Escritor** en una ejecución
   real, y `RF-07` sería papel. El Editor sí lo recibe: `ciclo.preparar_directorio_aislado`
   escribe su propio `settings.json` con la ruta absoluta de `policy.py`.
5. **Nada guarda de qué obra es una fila, y los identificadores se repiten entre novelas.**
   `uso_de_hecho` no tiene columna `obra`; `escena.id`, `entidad.id` y el `id` de
   `evento_cronologico` son claves primarias globales; la novela regalo numera las escenas
   `"{capitulo}-e1"` y los imprescindibles `imp-01`, `imp-02`… en todas las novelas
   (`orquestacion/novela.py`, `_id_imprescindible`). **Dos obras en la misma base se pisan
   antes de que exista ninguna tool.** Es un defecto activo, no de este plan: queda
   registrado aparte (ver § "Fuera de este plan").
6. **Tres campos de la ficha de `SPEC-22` `RF-43` no tienen fuente.** El nombre solo vive en
   el plan aprobado (`plan_de_obra`) y el `estado_vital` vigente en `entidad.vital`, pero
   `alias`, `rol_dramatico` y `atmosfera` no los guarda ninguna tabla ni el plan.
7. **La cronología y los usos solo existen para lo consolidado**: el Escritor del capítulo 1
   recibirá listas vacías. Y `evento_cronologico.descripcion` no es atributo de
   `EventoCronologico` en `docs/definitions.md`, así que por `RF-02` no entra en la salida.

## Decisiones que se aprueban con este plan

La spec deja fuera *cómo se exponen las tools*. **Aprobar el plan es aprobar esto:**

- **D-1. Un servidor MCP stdio propio, sin SDK.** Solo hace falta `initialize`,
  `tools/list` y `tools/call` sobre JSON-RPC por líneas; el esquema de entrada lo da
  `model_json_schema()` de Pydantic, y el paquete `mcp` no está instalado. **Riesgo**: una
  versión del protocolo que Claude Code no acepte, y solo lo descubre E10. Si pasa, se cambia
  al SDK oficial con el mismo módulo de tools detrás.
- **D-2. Cuatro barreras, porque ninguna está probada en real.** Toda delegación del pipeline
  lleva `--tools ""`, que apaga las integradas en **todos** los agentes; el Escritor y el
  Editor, además, `--strict-mcp-config --mcp-config <fichero>` y `--allowedTools` con sus tres
  nombres; el hook de policy como allowlist; y el frontmatter. El día que exista el browser
  MCP de `EX-04`, no entrará en ninguna delegación.
- **D-3. El Escritor arranca en la raíz del repositorio.** Es el arreglo de `F-61`, limitado
  al único agente no aislado que lo necesita. **Si el arreglo general de `F-61` que propone
  la otra sesión se aprueba y se aplica antes, D-3 queda cubierta por él** y E7 solo
  comprueba que el Escritor la hereda.
- **D-4. La obra no es argumento de ninguna tool.** La fija el harness en la configuración
  del servidor (`HARNESS_OBRA`), y un argumento `obra` se rechaza por esquema. Es `RF-06`
  hecho cumplir.
- **D-5. `alias`, `rol_dramatico` y `atmosfera` salen vacíos** (`[]`, `null`, `null`), y la
  documentación dice por qué.
- **D-6. Ninguna invariante nueva.** Solo lectura, sin texto de escena y solo la obra propia
  son propiedades del sistema: se verifican con filas `VER`, no en la puerta de escena.

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `commons/dominio/story_bible.py` (nuevo) | Esquemas Pydantic de entrada y salida de las tres tools |
| `commons/politica/herramientas.py` (nuevo) | La allowlist: qué tool puede llamar cada agente |
| `features/orquestacion/story_bible.py` (nuevo) | Las tres lecturas y `atender()`: valida, lee, mide y registra. Cruza features, y cruzar es de `orquestacion/` (`A-02`) |
| `features/observabilidad/repository.py` | Tabla `llamada_a_herramienta` y el enganche del span para `SPEC-29` |
| `commons/modelo/mcp.py` (nuevo) | El bucle JSON-RPC stdio, genérico |
| `commons/modelo/proveedor.py` | `SesionDelegada.herramientas`, `--tools ""` y el fichero MCP por delegación |
| `backend/herramientas/story_bible.py` (nuevo) | El script que lanza Claude Code como servidor |
| `backend/hooks/policy.py` | De negarlo todo a allowlist por agente |
| `.claude/agents/escritor.md`, `editor.md` | Declaran sus tres tools y cuándo usarlas |
| `features/orquestacion/novela.py`, `ciclo.py`; `backend/novela_regalo.py` | Dar las tools al Escritor y al Editor; el Escritor en la raíz |
| `commons/db/migraciones.py` | La migración de `traza_de_delegacion.delegacion` |

Ningún cambio en `docs/definitions.md`.

## Pasos

### E1 · Los esquemas de las tools

Sobre `_DelDominio` (`extra="forbid"`):

- **`hechos`**: entrada `{hecho?}`; salida `{hechos: [{id, enunciado, usos: [{capitulo,
  tipo}]}]}`, con **todos** los tipos (`SPEC-21` `C-2`).
- **`ficha`**: entrada `{id}`; salida, una ficha de personaje `{id, nombre_canonico, alias[],
  rol_dramatico | null, estado_vital}` o una de lugar `{id, nombre, atmosfera | null}`.
- **`cronologia`**: entrada `{capitulo?}`; salida `{eventos: [{id, t_fabula, duracion_min,
  lugar, capitulo, personajes_presentes[]}]}`.

**Prueba que falla primero:** `test_pedir_otra_obra_por_argumento_se_rechaza`. Además
`test_ningun_esquema_de_salida_tiene_campo_de_texto_de_escena` (`RF-05`),
`test_la_ficha_de_personaje_tiene_los_campos_de_rf43`,
`test_un_rol_dramatico_fuera_del_vocabulario_es_error` y
`test_un_tipo_de_uso_fuera_del_vocabulario_es_error`.

### E2 · Las tres lecturas, filtradas por obra

`leer_hechos`, `leer_ficha` y `leer_cronologia`, con los usos **filtrados por las escenas de
la obra**, la ficha solo si la entidad está en el plan aprobado de esa obra, y la cronología
de `eventos_de(con, obra)`. Ninguna llama a `presupuesto`.

**Prueba que falla primero:** `test_hechos_trae_cada_uso_con_su_capitulo_y_su_tipo`. Además
`test_hechos_no_cuenta_usos_de_escenas_de_otra_obra`,
`test_la_ficha_de_personaje_sale_del_plan_aprobado_y_del_estado_vigente`,
`test_la_ficha_de_una_entidad_de_otra_obra_no_existe`,
`test_alias_rol_y_atmosfera_salen_vacios_porque_no_tienen_fuente`,
`test_la_cronologia_va_en_orden_de_fabula_con_presentes_y_lugar`,
`test_la_cronologia_no_trae_eventos_de_otra_obra`,
`test_ninguna_lectura_devuelve_el_texto_de_una_escena` (un borrador con un marcador que no
aparece en ninguna salida) y `test_las_lecturas_funcionan_con_una_conexion_de_solo_lectura`.
Esta última caza un riesgo sin comprobar: `hechos_declarados` llama a `asegurar_tablas`, y un
`CREATE TABLE IF NOT EXISTS` sobre una base de solo lectura puede reventar.

### E3 · Atender una llamada: validar, medir y registrar

Tabla `llamada_a_herramienta (id, delegacion, obra, agente, herramienta, validacion,
latencia_ms, tokens_estimados, cuando)`, **sin argumentos ni resultado**, porque llevan datos
de la story bible y la story bible lleva al destinatario (`SPEC-29`, `VER-69`). `atender`
valida la entrada, lee, valida la salida, estima los tokens de lo devuelto, guarda la fila y
devuelve `{content, isError}`; un error de entrada devuelve `isError: true` con el mensaje de
Pydantic. `spans_de_herramientas(con, delegacion)` es el enganche de `SPEC-29`.

**Prueba que falla primero:**
`test_una_entrada_fuera_de_esquema_devuelve_error_visible_y_queda_registrada`. Además
`test_una_salida_fuera_de_esquema_no_se_devuelve`,
`test_una_herramienta_desconocida_se_rechaza_y_se_registra`,
`test_los_tokens_de_lo_devuelto_se_estiman_y_se_guardan`, `test_atender_no_toca_el_presupuesto`
(`RF-08`), `test_una_llamada_a_herramienta_se_guarda_sin_argumentos_ni_resultado` y
`test_el_span_de_una_herramienta_lleva_solo_lo_que_sube` (`RF-09`).

### E4 · El servidor MCP por stdio

`commons/modelo/mcp.py:servir` atiende `initialize`, `tools/list` y `tools/call`, e ignora las
notificaciones. `backend/herramientas/story_bible.py` lee `HARNESS_DB`, `HARNESS_OBRA`,
`HARNESS_AGENTE` y `HARNESS_DELEGACION`, y abre **dos conexiones**: una de solo lectura para la
story bible (`RF-04` hecho cumplir por SQLite) y otra de escritura solo para
`llamada_a_herramienta`. Sin `HARNESS_OBRA` no arranca.

**Prueba que falla primero:** `test_initialize_tools_list_y_tools_call_en_memoria`. Además
`test_tools_list_publica_el_esquema_de_entrada_de_pydantic`,
`test_una_notificacion_no_recibe_respuesta`, y lanzando el script como proceso:
`test_el_servidor_como_proceso_atiende_las_tres_tools`,
`test_sin_harness_obra_el_servidor_no_arranca`,
`test_el_servidor_no_puede_escribir_en_la_story_bible` y
`test_cada_llamada_deja_su_fila_con_la_delegacion`. Lo que no prueban —que Claude Code acepte
este `initialize`— lo comprueba E10.

### E5 · El hook de policy como allowlist

`commons/politica/herramientas.py` con las tres tools del Escritor y del Editor. `policy.py`:
sin `HARNESS_AGENTE` sale con 0 como hoy (`RF-19`); con la tool en la lista del agente, sale
con 0; si no, niega y apunta `herramienta_denegada`.

**Prueba que falla primero:** `test_policy_deja_al_escritor_usar_sus_tools_de_story_bible`.
Además `test_policy_deja_al_editor_usar_sus_tools_de_story_bible`,
`test_policy_niega_al_planificador_las_tools_de_story_bible`,
`test_policy_niega_al_editor_una_tool_de_otro_servidor_mcp` y
`test_el_catalogo_del_servidor_y_la_allowlist_nombran_las_mismas_tools`.

### E6 · La delegación ofrece las tools

`SesionDelegada` gana `herramientas`; toda delegación del pipeline lleva `--tools ""`; con
herramientas, un fichero MCP temporal por delegación con un `HARNESS_DELEGACION` nuevo en cada
llamada, y `--mcp-config <fichero> --strict-mcp-config --allowedTools <las del agente>`. Los
argumentos nuevos solo viajan si están puestos, para que los ejecutores inyectables de las
pruebas sigan valiendo.

**Prueba que falla primero:**
`test_con_herramientas_la_orden_lleva_mcp_estricto_y_solo_las_permitidas`. Además
`test_sin_herramientas_la_orden_no_lleva_mcp`,
`test_cada_delegacion_del_pipeline_apaga_las_herramientas_integradas`,
`test_la_configuracion_mcp_va_en_un_fichero_con_obra_base_agente_y_delegacion` y
`test_la_delegacion_devuelve_su_identificador_en_las_medidas`.

### E7 · El Escritor y el Editor, con sus tools

`escritor.md` y `editor.md` declaran sus tres tools y dicen que son de solo lectura y que
**el delta sigue en el JSON de la respuesta** (`RF-04`). `novela.escribir` fija
`herramientas` en los dos. El Escritor arranca en la raíz (D-3).

**Prueba que falla primero:**
`test_solo_el_escritor_y_el_editor_declaran_herramientas_y_son_las_permitidas`, que sustituye
a la de hoy y exige `tools: []` en los otros cinco. Además
`test_el_escritor_sabe_que_el_delta_sigue_en_su_respuesta`,
`test_escribir_da_las_tools_al_escritor_y_al_editor_y_a_nadie_mas`,
`test_el_escritor_se_lanza_desde_la_raiz_del_repositorio` y
`test_el_editor_aislado_recibe_sus_tools`.

### E8 · Cada delegación enlazada con sus llamadas

Una migración (el número se comprueba al commitear; `PLAN-27` y `PLAN-32` también piden una):
`traza_de_delegacion.delegacion`, en el `CREATE TABLE` y con `anadir_columnas`. La traza suma,
por delegación, cuántas llamadas a tools hubo y sus tokens estimados, sin presupuestarlos.

**Prueba que falla primero:** `test_la_migracion_anade_delegacion_a_una_base_anterior`.
Además `test_la_traza_de_una_delegacion_suma_los_tokens_de_sus_herramientas` y
`test_delegar_guarda_el_identificador_de_la_delegacion`. `test_entrega.py`, que recorre toda
la base buscando datos de la ficha, sigue en verde.

### E9 · `docs/` y spec al día

`docs/architecture.md` § "Los hooks de Claude Code" con la allowlist, las tres tools, el
servidor, las cuatro barreras y el punto ciego del límite de contexto; `docs/verification.md`;
`docs/cobertura-examen.md` (`EX-01`); `AGENTS.md` (`backend/herramientas/`); y
`docs/proceso/` (`claude-code.md`, `diagramas.md`). `SPEC-28` pasa a `aplicada` con su commit
propio.

### E10 · Ejecución real mínima (gasta dinero; necesita un sí explícito)

1. **Una delegación mínima**, con modelo pequeño, desde la raíz, con una base de datos
   inventados, pidiendo llamar a `cronologia`. Comprueba el nombre MCP, que `--tools ""` deja
   viva la tool, que el servidor recibe su entorno, que el hook se dispara y la deja pasar,
   que queda la fila, y que una llamada a `Read` se niega.
2. **`novela_regalo.py FICHA.json --capitulos 1`** con una ficha inventada: cuántas llamadas
   hace el Escritor, cuántos tokens estimados devuelven, si el Editor las usa, y si el hook
   `Stop` deja constancia desde la raíz.

El coste se informa con lo que dé la medida. Si la versión del protocolo falla, se para y se
aplica D-1.

## Qué filas `VER-xx` abre

- **`VER-nueva-A`**: tres tools con esquema de entrada y de salida; una entrada fuera de
  esquema se rechaza con un error visible y queda registrada (`RF-01`, `RF-02`).
- **`VER-nueva-B`**: la conexión de la story bible es de solo lectura (`RF-04`).
- **`VER-nueva-C`**: ninguna tool devuelve texto de escena, ni por esquema ni por contenido
  (`RF-05`).
- **`VER-nueva-D`**: una tool solo lee la obra de su delegación, y la obra no es argumento
  (`RF-06`). Punto ciego: el defecto de los identificadores globales (hallazgo 5).
- **`VER-nueva-E`**: solo el Escritor y el Editor tienen tools, y el hook es una allowlist
  (`RF-03`, `RF-07`). Punto ciego: hasta E10, nada prueba que Claude Code entregue al hook el
  nombre MCP esperado.
- **`VER-nueva-F`**: cada llamada deja una fila sin argumentos ni resultado, y sus tokens no
  entran en el reparto (`RF-08`, `RF-09`). Punto ciego: los tokens son una estimación de cuatro
  caracteres por token, no una medida.

## Fuera de este plan

- **Los identificadores globales que se repiten entre novelas** (hallazgo 5). Es un defecto
  activo: se registra como hallazgo numerado y se arregla aparte, antes de las ejecuciones
  reales de `PLAN-31`.
- Enviar nada a Langfuse (`SPEC-29`), tools de escritura, un servidor MCP para clientes
  externos, que el Planificador declare `alias`, `rol_dramatico` o `atmosfera`, y presupuestar
  lo que devuelven las tools.
