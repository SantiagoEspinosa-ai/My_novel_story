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
`.agents/skills/README.md`. Ocho:

| Skill | Para qué | Procedencia |
| --- | --- | --- |
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
del repositorio; **`F-61` está cerrado** (`1ad5691`): las delegaciones arrancan en la raíz, y en
la segunda ejecución real los hooks ya se ejecutan, según la sesión que la lanzó.

## Comandos propios

**No hay ninguno.** `.claude/commands/` está reservada en `AGENTS.md` § "Todavía no existe"
(`EX-10`).

## Memoria

La memoria de las sesiones vive hoy **fuera del repositorio**, en el perfil del usuario. El
enunciado pide que `.claude/` la incluya commiteada; qué memoria entra se decide al crearla
(`EX-10`).

## Browser MCP

**Ni configurado ni usado todavía.** Decidido Playwright MCP; espera a que exista la lectura
web, porque sin ella no hay nada que inspeccionar (`EX-04`, `EX-13`). Cuando se use, aquí irá
qué inspeccionó el agente, qué detectó y qué cambio provocó.
