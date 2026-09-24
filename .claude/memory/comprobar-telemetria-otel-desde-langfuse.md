---
name: comprobar-telemetria-otel-desde-langfuse
description: "En My_novel_story, la telemetría OTEL no se comprueba leyendo las variables de entorno desde un subproceso; se comprueba en Langfuse."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: e52256e3-d959-4d0f-be48-c48f62092794
  modified: 2026-09-18T15:59:54.032Z
---

# Comprobar la telemetría mirando Langfuse, no las variables de entorno

En el proyecto `My_novel_story` la telemetría de Claude Code se configura en
`.claude/settings.json` mediante variables `OTEL_*` y `CLAUDE_CODE_ENABLE_TELEMETRY`.

En una sesión anterior comprobé si la telemetría estaba activa lanzando un
comando que leía esas variables del entorno (por ejemplo, un `python -c` o un
script de PowerShell) y concluí que no estaban puestas, es decir, que la
exportación no funcionaba. El usuario corrigió esa conclusión: **era un falso
negativo, porque Claude Code borra esas variables del entorno de los
subprocesos que lanza**. Las variables sí existen en el proceso del CLI, que es
quien exporta las trazas; simplemente no se heredan a lo que se ejecuta desde
las herramientas.

La consecuencia práctica para sesiones futuras: no afirmar que la telemetría
está apagada basándose en una lectura de variables de entorno hecha desde un
subproceso. La comprobación válida es mirar el destino, es decir, si en
Langfuse aparecen las trazas (`claude_code.interaction` y sus observaciones por
modelo). El usuario ya verificó por esa vía que la exportación funciona.
