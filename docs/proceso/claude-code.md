# Uso de Claude Code en el proyecto

Lo que `EXAMEN.md` § "Claude Code" pide que el repositorio refleje: skills, subagentes,
comandos, hooks, memoria y el browser MCP. Cada apartado dice qué hay y qué falta.

## `CLAUDE.md` y `AGENTS.md`

`CLAUDE.md`, en la raíz, importa `AGENTS.md` entero y añade lo técnico: stack, límite de
contexto, persistencia, reglas de trabajo y comandos. `AGENTS.md` es el mapa de contexto que
leen todos los agentes: dónde está cada cosa, en qué orden cargarla y qué manda sobre qué,
con `EXAMEN.md` por encima de todo en lo que se entrega.

## Skills

El contenido real está versionado en `.agents/skills/`, con su tabla de uso y procedencia en
`.agents/skills/README.md`. Nueve: ocho de desarrollo y una del pipeline.

| Skill | Para qué | Procedencia |
| --- | --- | --- |
| **`novela-regalo`** | **La del pipeline**, la que pide el enunciado como skill reutilizable: lanzar una generación e inspeccionar lo que hizo de verdad —base, hooks, tools y Langfuse—, sin fiarse del código de salida. **Resultado:** salió de la primera ejecución real aceptada, en la que un código 0 escondía un Editor sin veredicto y un Resumidor que no resumía (`F-76`, `F-77`) | Propia |
| `spec-and-plan` | Ejecutar las tres puertas: spec, plan y código | Propia |
| `coherencia-docs` | Revisar la coherencia entre documentos: citas rotas, contradicciones, literales que derivan | Propia |
| `backend-feature` | Decidir dónde va un fichero del backend y de qué puede depender | Propia |
| `harness-invariantes` | Implementar o revisar una comprobación `INV-xx` | Propia |
| `verification-plan` | Escribir o revisar `docs/verification.md` | Propia |
| `fastapi` | Los idiomas del framework | Oficial de FastAPI |
| `feature-sliced-design` | La estructura del frontend | Oficial de FSD v2.1 |
| `sqlite-vec` | Tablas `vec0` y consultas KNN | Vendorizada: su autor la borró del repositorio original |

**Por qué se versiona el contenido y no un lockfile**: un lockfile fija una versión pero no
garantiza que siga existiendo, y es exactamente lo que pasó con `sqlite-vec`.

## Subagentes

Definidos en `.claude/agents/`. El Escritor y el Editor tienen las tres tools de lectura de la
story bible (`SPEC-28`); el resto, `tools: []`. Cada uno se lanza en su propia sesión (`A-03`, `SPEC-14`).

| Subagente | Propósito | Resultado conocido |
| --- | --- | --- |
| `entrevistador` | Rellena la ficha del destinatario, un turno cada vez | Probado con dobles (`SPEC-25`) |
| `planificador` | Convierte la ficha en el plan de los 10 capítulos | En la primera ejecución real devolvió **dos planes fuera de esquema** antes del bueno (`F-62`, cerrado) |
| `revisor_plan` | Aprueba el plan o lo devuelve con objeciones, comparándolo con la ficha | Probado con dobles |
| `escritor` | Escribe el capítulo y devuelve texto y delta en la misma respuesta | En la primera ejecución real, el capítulo 1 no se aceptó por un fallo del guardrail, no del texto (`F-59`) |
| `editor` | Nota de 1 a 5 y justificación por criterio; no reescribe | Construido (`SPEC-26` `RF-09`); sin juicio sobre una novela completa todavía |
| `juez` | Juicio de calidad de una escena, aislado del Escritor | Usado en la obra de diez capítulos anterior (`A-06`, `F-20`) |
| `resumidor` | Condensa cada escena consolidada y extrae sus hechos clave | Usado en la obra de diez capítulos anterior |

## Hooks

Dos, declarados en `.claude/settings.json` y con el código en `backend/hooks/`
(`SPEC-26` `RF-17`..`RF-19`):

- `validar_capitulo.py` (`Stop`): longitud, nombres y vetadas del último mensaje del
  Escritor; si falla, se le devuelve en la misma sesión.
- `policy.py` (`PreToolUse`): una allowlist por agente (`SPEC-28`): el Escritor y el Editor pueden llamar a sus tres tools de lectura de la story bible; cualquier otra herramienta se niega y queda en el audit log.

Solo actúan sobre las delegaciones del pipeline, nunca sobre una sesión interactiva. En la
primera ejecución real no dejaron constancia, porque Claude Code solo los carga desde la raíz
del repositorio; **`F-61` está cerrado** (`1ad5691`): las delegaciones arrancan en la raíz y los hooks se
cargan. En la segunda ejecución real `validar_capitulo.py` dejó 4 filas en el registro de hooks, las 4 con el Planificador o el Revisor y en la rama que sale sin comprobar nada (solo actúa con el Escritor, `validar_capitulo.py:76`); `policy.py` no dejó ninguna. **Ninguno de los dos ha validado todavía un capítulo ni interceptado una herramienta**, porque el Escritor no llegó a ejecutarse (`F-68`).

## Comandos propios

**`/inspeccionar-novela <base.db> <obra>`** (`.claude/commands/inspeccionar-novela.md`). **Propósito:**
aplicar la skill `novela-regalo` a una generación y devolver, en una tabla, lo que la base, los
hooks y Langfuse dicen que pasó, separando lo que terminó de lo que funcionó. **Resultado:** es el
recorrido con el que se encontraron `F-76`, `F-77` y `F-78` en la ejecución `R0`
(`harness/evals/medidas.md`).

## Memoria

La memoria de las sesiones vive en el perfil del usuario y **se copia al repositorio** en
`.claude/memory/`, como pide el enunciado (decisión del autor, 2026-09-24): son las lecciones que el
autor fue corrigiendo sesión a sesión —no rellenar un número sin medir, una carpeta por sesión,
spec → plan → código— y que cambian cómo se trabaja aquí. Antes de copiarla se comprobó que no lleva
datos de las ejecuciones reales: ninguna de las 17 palabras de nombre de la ficha real aparece en
ella. **Es una copia, no la fuente**: se actualiza copiando otra vez.

## Browser MCP

**Configurado en `.mcp.json`** (`PLAN-22` E12): un solo servidor, Playwright MCP
(`npx -y @playwright/mcp@0.0.82 --browser msedge --headless --isolated`). Es para la sesión que
inspecciona la web; **ninguna delegación del pipeline lo carga** (toda lleva
`--strict-mcp-config`) y el hook de policy niega sus tools a los agentes (`VER-108`).

### La primera inspección real (`PLAN-22` E13, 2026-09-24)

**Sobre qué.** La web de verdad: `uvicorn` con `HARNESS_BASE` apuntando a la base de
`backend/semilla_lectura.py` (una obra **inventada** de cuatro capítulos, sin modelo) y el
frontend con Vite, que manda `/api` al backend. Ninguna base real.

**Cómo.** Una sesión de Claude Code lanzada con
`claude -p --model sonnet --mcp-config .mcp.json --strict-mcp-config --tools ""` y solo las tools
del browser permitidas, con un prompt que le pedía recorrer portada, índice, cada capítulo, una
escena y las fichas, seguir cada enlace de las fichas, hacer capturas y devolver un JSON. **Coste
leído del sobre de la delegación: 0,5766 USD** (`total_cost_usd`), 37 turnos, 115,5 s.

**Qué inspeccionó.** Ocho páginas: la portada, el índice, los cuatro capítulos, la escena
`cap-02-e1` y las fichas; y los cuatro enlaces de las fichas de lugar, que llegaron cada uno al
capítulo que nombran.

**Qué detectó el agente.** Nada que llamara error: un solo apunte de gravedad «baja» —que la
ficha del personaje no enlaza ningún capítulo y dice «no declarado»—, que **es lo correcto**,
porque la novela regalo todavía no declara los presentes. Su propia valoración dice que juzgó
«en la inspección del árbol de accesibilidad».

**Qué detectó la revisión de sus artefactos, y el agente no.** Mirando capturas de las mismas
páginas —hechas aparte, con Edge sin cabeza— y los registros de consola que deja el MCP en
`.playwright-mcp/`. El agente sí hizo capturas (cinco), pero el MCP las dejó en la raíz del
repositorio porque no tenía `--output-dir`; desde E13b lo tiene:

| Hallazgo | Qué se veía | A quién se devolvió | Cambio |
| --- | --- | --- | --- |
| `F-81` | En las fichas, «(sin nombre guardado)» iba dentro del título y lo partía en dos líneas | Frontend (error de pintado) | El aviso sale en su propia línea, fuera del `h3`. Prueba roja: `Fichas › un nombre nulo pinta el id y lo dice` |
| `F-82` | En un capítulo, la etiqueta de estado quedaba pegada a la primera tarjeta | Frontend | Margen en `estilos.css`. **Sin prueba roja**: es CSS y jsdom no calcula el layout; lo comprobó una segunda captura |
| `F-83` | La consola daba `404` en `/favicon.ico` en cada página | Frontend | Icono declarado en `index.html`. Prueba roja: `documento › index.html declara su icono` |
| `F-84` | El agente dio por buena la web con los tres defectos de arriba | Proceso | Queda como punto ciego de `VER-109` y de `INV-30` (`VER-119`) |

**Ningún error de texto**: el texto es inventado y no lo cubre ninguna `INV-xx`, así que no hubo
nada que devolver al Escritor. El cambio va en el commit `PLAN-22 E13`.

### El validador visual `INV-30`, en real (`PLAN-22` E13b.2, 2026-09-24)

Sobre la misma web y la misma semilla, después de los arreglos de E13:
`python -X utf8 inspeccion_visual.py lectura-semilla.db obra-semilla-inventada http://localhost:5199/obras/obra-semilla-inventada --modelo sonnet`. Una delegación en el agente
`inspector_visual`, con `.mcp.json`, `--strict-mcp-config` y solo sus ocho tools del browser.

- **Resultado: `INV-30` `pasa`**, las cinco piezas `pasa`, cada una con su motivo; ningún
  hallazgo `INV-30` en la base. Esta vez el agente hizo **siete capturas** (en `.playwright-mcp/`)
  y pidió la consola en cada carga, y dijo que no había errores: con el icono de `F-83` puesto,
  ya no los hay.
- **Coste leído de la delegación: 0,4872 USD** (`coste_usd` de sus medidas).
- **Los scores no llegaron a Langfuse.** El worktree no tiene `backend/.env` —lo ignorado no
  viaja— y el guion lo dijo (*«no se envia a Langfuse: sin claves»*): los seis scores
  (`INV-30` e `INV-30.<pieza>`) se emitieron a un exportador en memoria. Que suban a una
  instancia real está **sin ejercer**.
- **Un `pasa` sobre una web que ya se había arreglado a mano no dice cuánto caza.** El único
  caso en que el agente tuvo defectos delante (E13) no vio ninguno (`F-84`). Sesga hacia lo
  cómodo: este verde es compatible con un validador que no mira.
- ❌ **No vuelve al Escritor.** Si hubiera fallado, el hallazgo habría quedado abierto para
  una persona; que el fallo vuelva solo al rol que toca está fuera de `RF-58` y sin hacer.

### La inspección de la petición de cambio (`PLAN-22` E18, 2026-09-24)

**Sobre qué.** La misma semilla inventada, que desde E18 tiene **dos versiones**: la 2 sale de
una petición de hecho inventada sobre `hec-faro` y sustituye el capítulo 1; los otros tres se
comparten. Sembrada con el repositorio de `PLAN-23` y **sin modelo** (`semilla_lectura.py`); la
1 se reverifica y la 2 no. `uvicorn` en el puerto 8791 sobre una base del scratchpad y Vite en
el 5291: con varias sesiones a la vez, el 8765 ya lo usaba otra y sus peticiones llegaban al
backend equivocado.

**Cómo.** `claude -p --model sonnet --mcp-config .mcp.json --strict-mcp-config --tools ""
--allowedTools mcp__playwright --output-format json --max-budget-usd 2`, con un prompt que pedía
recorrer el índice de la vigente, seleccionar un fragmento, abrir la petición, elegir el hecho,
ver los capítulos, confirmar si se podía, navegar la versión 1 entera y pedir la consola.
**Coste leído del sobre: 1,07275 USD** (`total_cost_usd`), 58 turnos, 188,5 s.

**Qué vio el agente.** Los cinco pasos «pasa»: selector de versiones, capítulo 1 «cambió» y los
demás «igual», el verde heredado en ámbar y no en verde, el fragmento citado en el panel, el
hecho ofrecido, «no declara quién está presente» en la pestaña de nombre, las dos listas de
capítulos con la promesa y su punto ciego juntos, **ningún botón de confirmar** con el motivo
*«salida sin elegir: falta la medida»*, y la versión 1 leída entera sin ofrecer cambios. La
confirmación no se pudo ejercer: el backend no tiene salida elegida hasta la Parte B de
`PLAN-23`, y la interfaz no ofrece confirmar sin ella.

**Qué detectó, y qué cambió.**

| Hallazgo | Qué se veía | A quién | Cambio |
| --- | --- | --- | --- |
| `F-133` | `500` intermitentes en `/versiones`, `/versiones/1/capitulos/…`, `/indice` y `/fichas` (12 en el registro del backend), y la pantalla de error en vez del capítulo. Causa: `sqlite3.ProgrammingError`, la conexión creada en un hilo del pool y usada en otro | Backend | `check_same_thread=False` en las cuatro dependencias `conexion`. Prueba roja: `test_la_conexion_de_una_peticion_se_puede_usar_desde_otro_hilo`. Tras el arreglo, 90 peticiones concurrentes con `curl`, 90 `200` y ningún `500` en el registro |
| `F-134` | `404` en `/progreso` en cada página, en la consola | — | **Sin cambio**: es el contrato de E13c (sin generación, `404` y no una fase inventada). Queda registrado |
| `F-135` | La pantalla de error sale sin el margen de la página, pegada a los bordes | Frontend | **Sin cambio en E18**: se vio en la captura, no lo señaló el agente |

**Lo que no prueba.** Una sola pasada, con un agente que ya dio por buena una web con defectos
(`F-84`); esta vez sí vio los `500`, que estaban en la consola. La confirmación y el seguimiento
de un trabajo real siguen sin ejercer fuera de las pruebas con dobles (`VER-111`).

### La novela regalo en la web, en un navegador real y sin agente (`PLAN-33` E15, 2026-09-24)

**Sobre qué.** Las páginas de `SPEC-33`: la estantería, la entrevista como conversación, la
confirmación antes de gastar y la generación en vivo. Una base con datos **inventados**
(`backend/semilla_regalo.py`) servida por `uvicorn` en el 8010 y Vite en el 5183: el 8000 y el
5173 los tenía otra sesión con la novela de ejemplo.

**Cómo, y por qué no con el agente.** Edge sin cabeza movido por Playwright desde un guion
(`frontend/scripts/recorrido-regalo.mjs`), **sin modelo y sin gastar**. La inspección con el
agente del browser MCP, como la de E13 o E18, lanza una sesión de Claude Code y gasta, y
`PLAN-33` no gasta fuera de E16: queda **pendiente de un sí**. El guion no pulsa «Responder»
(llamaría al Entrevistador) ni «Sí, escribir la novela» (gasta).

**Qué comprobó.** 16 comprobaciones, las 16 en verde y sin errores de consola: las cuatro
obras con un solo «Generar novela», el aviso y la contradicción dentro de su turno, la
confirmación con 14,70 de 50 USD «como mínimo» y la referencia de 16,89 USD con su fuente, las
fases, la nota 2/5 «bajo el umbral», el coste en vivo 2,40 USD «como mínimo», y ningún scroll
horizontal a 1280 ni a 390 px.

**Qué detectó la revisión de las capturas, y las comprobaciones no.**

| Hallazgo | Qué se veía | Cambio |
| --- | --- | --- |
| `F-200` | Los capítulos 1 y 2, terminados y con sus notas, decían «resumiendo»: el pipeline no cierra capítulos y no hay fase de «terminado» | **Corregido**: la fase solo en el capítulo en curso y el `estado_de_escena` en los demás, con sus dos pruebas rojas antes. Las comprobaciones pasaban porque también se escribieron sobre fases inventadas |
| — | Las notas del Editor salían desvaídas | **Sin cambio**: la captura caía a mitad de la animación de entrada; a 1,5 s la opacidad es 1 |
| — | La última pregunta de la entrevista, tapada por el formulario fijo | **Sin cambio**: artefacto de la captura de página entera; con la página desplazada al final, la pregunta queda por encima del formulario |
| — | A 390 px, la línea del coste se partía en tres columnas estrechas | **Corregido**: la línea se parte en renglones |

**Lo que no prueba.** Que el camino con el modelo real funcione: ni un turno de la entrevista ni
una generación se lanzaron desde la web. Es `PLAN-33` E16, que gasta: la referencia es la
novela de ejemplo, 16,89 USD, y lo que costaría esta está sin medir.

### Las pantallas rediseñadas, en un navegador real y sin agente (`PLAN-35` E8, 2026-09-25)

**Sobre qué.** La portada con el PDF, el índice de una versión, el capítulo cambiado con el aviso
«por tu cambio» y pedir un cambio hasta la balda. La base es la de `backend/semilla_lectura.py`,
con datos **inventados** (dos versiones, una petición y la versión 2 publicada, `SPEC-34`
`RF-09`), servida en el 8010 y el 5183. El recorrido es `frontend/scripts/recorrido-seis-pantallas.mjs`,
en Edge sin cabeza, **sin modelo y sin gastar**: proponer un cambio no llama al modelo, y
«Confirmar el cambio», que sí gastaría, no se pulsa.

**Qué comprobó.** Doce comprobaciones, las doce en verde:
- el PDF se ofrece con su enlace;
- la vigente la dice el backend (`F-150`);
- un capítulo marcado como cambiado;
- **el estado y los hallazgos de cada escena siguen en el índice y el capítulo** (`CLAUDE.md`);
- el aviso con las palabras del lector, y sin aviso en un capítulo compartido;
- la balda con los capítulos propuestos y la promesa junto a su punto ciego;
- ni el índice ni la portada se desbordan a 390 px.

**Qué detectó, y qué cambió.**

| Hallazgo | Qué se vio | Cambio |
| --- | --- | --- |
| `F-201` | Antes de abrir el navegador, con `curl`: `/pdf/disponible` decía «sí» y la descarga daba un 500, porque la semilla deja una escena sin texto en una versión publicada | **Corregido**: la consulta comprueba que el libro se pueda componer, y la descarga responde `409` con el motivo; las dos pruebas nuevas fallaron antes |
| — | En la cubierta, el filete de arriba salía apagado: una regla vieja de `estilos.css` sobre el mismo pseudo-elemento | **Corregido** en el CSS de la portada |
| — | El aviso terminaba en «….».: sobraba un punto tras las palabras del lector | **Corregido**; las palabras del lector no se tocan |
| — | El índice se salía de la pantalla a 390 px (lo vio la sesión de `PLAN-22`) | **Corregido**: las etiquetas pueden bajar de línea; 390 de ancho medido |
| — | Dos comprobaciones fallaron en un primer pase **por el orden del guion**, no de la web: el PDF y los hechos llegan después de pintar la página | Corregido en el guion, que ahora espera |

**Lo que no prueba.** Que confirmar un cambio regenere bien: gasta y es la demo `B4`, en
`harness/evals/medidas.md`. Y no es la inspección con el agente del browser MCP.
