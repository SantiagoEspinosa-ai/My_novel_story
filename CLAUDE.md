# Proyecto: My_novel_story

Harness generador de novelas de romance, drama y terror, con validación automática.

## Qué es

Un programa Python que genera novelas completas llamando a modelos vía OpenRouter.
Un arquitecto diseña la estructura, un escritor redacta cada capítulo, y tres
validadores en paralelo lo auditan antes de aprobarlo.

## Documentos de referencia

- `SPEC-generador-novelas-v3.md` — especificación principal.
- `ADENDA-openrouter-vscode.md` — capa de modelos y setup. **Pisa a la v3 donde se
  contradigan.** En concreto: no hay subagentes ni plugins de Claude Code en el
  runtime, y los modelos van por OpenRouter.
- `config.json` — toda la configuración ajustable.
- `Harness_novela.drawio.png` — diagrama del flujo.

## Reglas del proyecto

- La capa de modelos es OpenRouter, nunca la API de Anthropic directamente.
- El runtime es Python puro. Sin subagentes de Claude Code, sin plugin, sin hooks.
- Ninguna clave de API en el código ni en `config.json`. Solo desde la variable
  de entorno `OPENROUTER_API_KEY`.
- Toda llamada a modelo pasa por `src/agentes.py`. Ningún otro módulo toca la red.
- Los prompts de sistema viven en `prompts/` y se leen en tiempo de ejecución.
  Nunca escribas texto de prompt dentro del código Python.
- Los validadores devuelven JSON. Si no parsea tras un reintento, es FALLO,
  nunca PASA.
- Los valores concretos (género, número de capítulos, rango de palabras) llegan
  desde `config.json` al mensaje de usuario. Los prompts no llevan valores fijos.

## Estructura

```
prompts/           prompts de sistema (no tocar sin pedírmelo)
  referencias/     convenciones por género
src/               código del harness
salida/            resultados (ignorado por git)
config.json        configuración
```

## Orden de implementación

Sigue la sección 13 del spec. Una etapa por sesión, y ejecuta antes de pasar a
la siguiente. No implementes el proyecto entero de una vez.

## Git

- Haz commit al terminar cada etapa, no antes.
- Mensajes en español, imperativo, una línea.
- Nunca hagas commit de `.env` ni de `salida/`.
- Antes de empezar una etapa nueva, verifica que el árbol está limpio.

## Comandos

- Ejecutar: `python -m src.orquestador`
- Tests: `pytest`
