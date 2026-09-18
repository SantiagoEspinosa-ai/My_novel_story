# Proyecto: My_novel_story

Harness generador de novelas de romance, drama y terror, con validación automática.

## Qué es

Un harness que genera novelas completas usando **Claude Code como orquestador**.
Un arquitecto diseña la estructura, un escritor redacta cada capítulo, tres
validadores en paralelo lo auditan antes de aprobarlo y un resumidor comprime
cada capítulo aprobado para los siguientes. Los seis son **subagentes de
proyecto** definidos en `.claude/agents/`.

No hay ningún programa Python que llame a una API de modelos. El Python que
queda es infraestructura de apoyo: carga la configuración, valida contratos de
datos, monta las ventanas de contexto y guarda el estado en disco. Quien habla
con los modelos es Claude Code, mediante delegación a subagentes.

## Documentos de referencia

- `SPEC-generador-novelas-v3.md` — especificación principal.
- `EJECUCION.md` — contrato de ejecución. Ver la sección siguiente.
- `DECISIONES.md` — por qué la arquitectura es como es. Cada entrada recoge algo
  que se comprobó ejecutándolo. Léelo antes de "arreglar" algo que parezca raro.
- `config.json` — toda la configuración ajustable.
- `Harness_novela.drawio.png` — diagrama del flujo.
- `ADENDA-openrouter-vscode.md` — **deprecada**. Describe la arquitectura
  anterior, basada en OpenRouter. Se conserva como historia; no la sigas.

## Contrato de ejecución

`EJECUCION.md` es el manual de ejecución del harness y manda sobre el
comportamiento en tiempo de ejecución: el flujo principal paso a paso, las seis
reglas inviolables, los archivos de `salida/`, la reanudación y los comandos
exactos.

- Léelo antes de implementar cualquier etapa. No hace falta que yo te lo repita
  en cada sesión.
- Si el código que vas a escribir contradice `EJECUCION.md`, el código está mal.
  Si crees que el documento es el equivocado, dímelo antes de tocar nada.
- Cuando una etapa cambie el comportamiento en ejecución o añada un comando,
  actualiza `EJECUCION.md` en el mismo commit, incluida su tabla de estado de
  implementación.

## Reglas del proyecto

- **La capa de modelos son los subagentes de Claude Code.** Nunca OpenRouter,
  nunca la API de Anthropic directamente, nunca un SDK dentro del código.
  **Ningún módulo de Python de este proyecto habla con un modelo.** Hay una
  cosa que sí hace uno y conviene decirla con precisión, porque es fácil
  leerla como una excepción y no lo es: `src/servidor.py` puede **arrancar el
  CLI de Claude Code** (`claude -p`) como subproceso, cuando se pulsa «generar»
  en el panel. Arrancar el programa que habla con los modelos no es hablar con
  los modelos: ahí no hay credenciales, ni cliente HTTP, ni endpoint, ni nada
  que configurar. Es un `subprocess`. Quien delega sigue siendo la sesión de
  Claude Code, igual que cuando la lanzas tú a mano. El porqué está en
  `DECISIONES.md`, decisión 12.
- **Ningún módulo de Python sale a la red.** Si un módulo necesita importar un
  cliente HTTP para *pedir* algo, el diseño está mal. `src/servidor.py`
  **escucha** en `127.0.0.1`, que es lo contrario: no pide nada a nadie, y no
  acepta conexiones de fuera de la máquina.
- **FastAPI es del panel, no del harness.** `src/servidor.py` es el único
  módulo que puede importar FastAPI, uvicorn o httpx. El harness tiene que
  seguir generando novelas en una máquina donde no estén instaladas, y
  `tests/test_harness_sin_servidor.py` lo comprueba lanzando un intérprete con
  esas librerías bloqueadas.
- **No hay claves de API en este proyecto.** Ni en el código, ni en
  `config.json`, ni en variables de entorno. Las credenciales son de Claude
  Code, no del harness.
- Los prompts de sistema viven en `prompts/` y se leen en tiempo de ejecución.
  Nunca escribas texto de prompt dentro del código Python ni dentro del cuerpo
  de un subagente: el cuerpo del subagente solo apunta a su skill puente.
  **Una excepción, y solo una:** el prompt con el que `src/servidor.py` arranca
  una generación (`PROMPT_GENERACION`) vive en el código, a propósito. Es
  seguridad, no descuido: ese texto es lo único que separa «el navegador puede
  decir empieza» de «el navegador puede decir qué se ejecuta». Si viviera en un
  archivo editable o pudiera componerse con algo que llega de fuera, dejaría de
  ser una constante. No es un prompt de sistema de ningún subagente: es la
  orden de arranque del orquestador.
- Cada subagente lleva `omitClaudeMd: true`. Ese aislamiento es lo que da
  sentido a tener validadores separados; no lo quites.
- Los validadores devuelven JSON. Si no parsea tras un reintento, es FALLO,
  nunca PASA.
- Los valores concretos (género, número de capítulos, rango de palabras) llegan
  desde `config.json` al mensaje de delegación. Los prompts no llevan valores
  fijos.
- El modelo de cada delegación se pasa en la llamada (`haiku`, `sonnet`, `opus`,
  `fable`) y pisa al `model` del frontmatter. Por eso hay un solo escritor y no
  tres.

## Estructura

```
.claude/agents/    los seis subagentes (no tocar sin pedírmelo)
.claude/skills/    skills puente que inyectan cada prompt de sistema
.claude/settings.json  telemetría OTEL del CLI (sin secretos)
prompts/           prompts de sistema (no tocar sin pedírmelo)
  referencias/     convenciones por género
src/               código de apoyo del harness
herramientas/      scripts de PowerShell de diagnóstico, fuera del harness
archivo/           código de la arquitectura anterior, fuera de uso
salida/            resultados (ignorado por git)
config.json        configuración
```

`herramientas/` es el único sitio donde puede haber una llamada de red, y solo
para diagnosticar la telemetría. No lo importa nadie de `src/` y no participa en
generar ninguna novela. El montaje está en `EJECUCION.md` sección 9.

## Orden de implementación

Sigue la sección 13 del spec, adaptada a la arquitectura de subagentes. Una
etapa por sesión, y ejecuta antes de pasar a la siguiente. No implementes el
proyecto entero de una vez.

## Git

- Haz commit al terminar cada etapa, no antes.
- Mensajes en español, imperativo, una línea.
- Nunca hagas commit de `salida/`.
- Antes de empezar una etapa nueva, verifica que el árbol está limpio.

## Comandos

- Tests: `python -m pytest`
- El resto de comandos de ejecución están en `EJECUCION.md` sección 2.

## Para generar o continuar una novela

Si te pido que genere una novela, o que continúe una a medias, empieza siempre
por aquí:

```powershell
python -m src.orquestacion estado
```

Ese comando dice en qué punto está la generación y cuál es el siguiente paso,
con el subagente y el modelo exactos. Sigue lo que diga, delega, registra el
resultado y vuelve a preguntar. No lleves la cuenta de cabeza: el estado vive en
`salida/`, no en la conversación, y por eso una sesión nueva puede continuar una
novela que empezó otra.
