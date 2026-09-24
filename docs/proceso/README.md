# Documentación de proceso

Lo que `EXAMEN.md` § "`/docs` en storyMaker" pide: no el resultado, sino **el razonamiento
que llevó a él**. Lo normativo —qué es verdad del sistema— sigue en `docs/` (`definitions.md`,
`architecture.md`, `verification.md`); esta carpeta cuenta **cómo se llegó ahí** y enlaza a
la fuente en vez de copiarla, para que no haya dos versiones que diverjan.

| El enunciado pide | Documento |
| --- | --- |
| Spec inicial | [`spec-inicial.md`](spec-inicial.md) |
| Trade-offs | [`trade-offs.md`](trade-offs.md) |
| Explainers | [`explainers.md`](explainers.md) |
| Diagramas | [`diagramas.md`](diagramas.md) |
| Registro de iteraciones | [`registro-de-iteraciones.md`](registro-de-iteraciones.md) |
| Red-team log | [`red-team-log.md`](red-team-log.md) |
| Skills, subagentes, hooks y browser MCP | [`claude-code.md`](claude-code.md) |

**Regla de estos documentos:** lo que no se ha medido o no se ha ejecutado dice *sin medir* o
*sin ejecutar*. Ninguna fila se rellena para que la tabla parezca completa.

Estado al 2026-09-24: la novela regalo **no ha completado todavía una generación** —la
primera ejecución real no pasó del capítulo 1 (`F-59`…`F-62`)—, así que los resultados de
evaluación, el tuning y el red-team contra el modelo real están pendientes de `SPEC-31`.
