# ADENDA — Runtime sobre OpenRouter y montaje en VS Code

**Complementa:** `SPEC-generador-novelas-v3.md`
**Reemplaza de la v3:** secciones 1.1 (componentes de Claude Code), 9 (subagentes), 10 (hooks), 11.1 (plugin.json) y los nombres de modelo de 4.4.
**Se mantiene intacto de la v3:** secciones 2 (gestión de contexto), 4 (carpeta config/), 6 (escalado y puntuación), 7 (contratos de datos), 12 (criterios de aceptación).

---

## 1. Los dos planos

| | Plano de desarrollo | Plano de ejecución |
|---|---|---|
| **Quién trabaja** | Claude Code en VS Code | Tu programa Python |
| **Qué hace** | Escribe y depura el código del harness | Genera las novelas |
| **Qué modelo usa** | Tu suscripción de Claude | Modelos vía OpenRouter |
| **Cuándo ocurre** | Mientras construyes | Cuando ejecutas `python -m src.orquestador` |
| **Componentes** | CLAUDE.md, extensión de VS Code | `src/`, `prompts/`, `config/` |

**El harness no depende de Claude Code para funcionar.** Una vez construido, se ejecuta solo, en cualquier máquina con Python y una clave de OpenRouter. Claude Code es el andamio, no parte del edificio.

## 2. Qué desaparece y qué lo sustituye

| Concepto v3 | Qué pasa ahora |
|---|---|
| Subagentes de Claude Code | **Desaparecen.** Cada llamada HTTP a OpenRouter ya es una ventana de contexto aislada. El aislamiento sale gratis |
| `skills/<n>/SKILL.md` | Se convierten en **plantillas de prompt** en `prompts/`. Mismo contenido, otro consumidor: los lee Python, no Claude Code |
| `hooks/hooks.json` | Se convierten en **funciones normales** del orquestador: validar entorno al arrancar, escribir checkpoints, registrar el log |
| `.claude-plugin/plugin.json` | **Desaparece.** Ya no es un plugin, es un proyecto Python |
| `agents/*.md` (frontmatter) | Se convierte en `config/agentes.json`: qué modelo, qué temperatura y qué prompt usa cada rol |
| Paralelismo por subagentes | `asyncio.gather()` sobre los tres validadores |

**Lo que gana importancia:** la gestión de contexto de la sección 2 de la v3. Antes Claude Code te ayudaba a contenerla; ahora la controlas tú a mano, línea por línea. Esa sección pasa a ser el corazón del proyecto.

## 3. Capa de modelos: OpenRouter

### 3.1 Endpoint

OpenRouter expone una API de completado compatible con OpenAI, así que puedes llamarla directamente o usar el SDK de OpenAI. El endpoint es `https://openrouter.ai/api/v1/chat/completions` y la autenticación va en la cabecera `Authorization: Bearer <token>`.

Los identificadores de modelo llevan prefijo de proveedor: `anthropic/claude-sonnet-4`, `openai/gpt-4o`, `google/gemini-2.5-pro`.

**Verifica los slugs exactos y vigentes en https://openrouter.ai/models antes de escribirlos en la config.** Cambian con frecuencia y un slug inválido falla en tiempo de ejecución, no al arrancar.

### 3.2 Cliente

Usa el SDK de OpenAI apuntando a OpenRouter. Evita escribir un cliente HTTP a mano: el SDK ya trae reintentos, timeouts y streaming.

```python
from openai import OpenAI
import os

cliente = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

respuesta = cliente.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[
        {"role": "system", "content": prompt_sistema},
        {"role": "user", "content": prompt_usuario},
    ],
    temperature=0.8,
    max_tokens=4000,
)
texto = respuesta.choices[0].message.content
```

### 3.3 Ventaja nueva: escalera multiproveedor

En la v3 la escalera era Haiku → Sonnet → Opus, tres modelos de la misma familia. Con OpenRouter puedes **cruzar proveedores**, y eso funciona mejor: cuando un modelo se atasca en un error, otro de la misma familia tiende a repetirlo, porque comparte datos de entrenamiento y sesgos. Un modelo de otro proveedor rompe el patrón de verdad.

Escalera sugerida para el escritor: un modelo barato de un proveedor, luego uno medio de otro, luego uno potente de un tercero.

**Contrapartida:** cada proveedor escribe con una voz distinta. Si el capítulo 7 lo resuelve un modelo y el 8 otro, se nota en la prosa. Dos mitigaciones, elige una:

- **Voz fija:** una vez que un modelo resuelve un capítulo, los siguientes empiezan por ese mismo modelo en vez de volver al primero de la escalera. Registra el modelo ganador en `estado.json`.
- **Pasada de homogeneización:** al ensamblar, un agente extra reescribe solo las transiciones. Más caro y añade un punto de fallo. No lo recomiendo para la primera versión.

### 3.4 Temperatura por rol

Algo que en la v3 no aplicaba y ahora sí, porque controlas los parámetros de muestreo:

| Rol | Temperatura | Por qué |
|---|---|---|
| Arquitecto | 0.9 | Quieres variedad en la premisa |
| Escritor | 0.8 | Prosa con textura |
| Validadores | 0.1 | Quieres veredictos **reproducibles**. Un validador creativo es un validador inútil |

La temperatura baja en los validadores es la que hace que la regla de mejor versión (v3 §6.4) tenga sentido: si el mismo capítulo puntúa distinto en dos evaluaciones, no puedes comparar intentos.

### 3.5 Salida en JSON

Los validadores deben devolver JSON parseable. No todos los modelos de OpenRouter respetan bien el modo JSON estructurado, así que el orquestador debe defenderse siempre:

1. Pedir JSON explícitamente en el prompt de sistema, sin preámbulo ni backticks.
2. Al recibir, intentar `json.loads` directo.
3. Si falla, extraer el primer bloque `{...}` equilibrado y reintentar el parseo.
4. Si vuelve a fallar, repetir la llamada **una vez** con un mensaje que incluya el error de parseo.
5. Si falla la segunda, registrar el validador como `INDETERMINADO` y tratarlo como `FALLO`.

El paso 5 importa: un validador que no parsea no puede aprobar un capítulo por defecto, o la validación se vuelve decorativa.

## 4. `config/modelos.json` actualizado

```json
{
  "proveedor": "openrouter",
  "base_url": "https://openrouter.ai/api/v1",
  "escalera_escritor": [
    { "modelo": "PROVEEDOR/MODELO-BARATO", "temperatura": 0.8 },
    { "modelo": "PROVEEDOR/MODELO-MEDIO", "temperatura": 0.8 },
    { "modelo": "PROVEEDOR/MODELO-POTENTE", "temperatura": 0.8 }
  ],
  "intentos_por_modelo": 2,
  "mantener_voz_ganadora": true,
  "arquitecto": { "modelo": "PROVEEDOR/MODELO-MEDIO", "temperatura": 0.9 },
  "validadores": { "modelo": "PROVEEDOR/MODELO-MEDIO", "temperatura": 0.1 },
  "timeout_segundos": 120,
  "reintentos_red": 3
}
```

Rellena los slugs desde la página de modelos de OpenRouter.

## 5. Paralelismo sin subagentes

Los tres validadores corren con `asyncio.gather()`. Un validador que revienta no debe tumbar a los otros dos:

```python
resultados = await asyncio.gather(
    validar("continuidad", capitulo),
    validar("genero", capitulo),
    validar("estilo", capitulo),
    return_exceptions=True,
)
```

Con `return_exceptions=True`, una excepción vuelve como valor en la lista en vez de propagarse. Cada excepción se convierte en un veredicto `INDETERMINADO`, que cuenta como `FALLO` (§3.5).

---

# GUÍA DE MONTAJE EN VS CODE

## Paso 1 — Node.js y VS Code

La extensión necesita el CLI de Claude Code por debajo: la extensión es una capa gráfica sobre el mismo motor que corre en la terminal, con diffs visuales, checkpoints y @-menciones encima.

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

Si `npm` no existe, instala Node.js primero desde nodejs.org.

## Paso 2 — Extensión

En VS Code, `Ctrl+Shift+X` (o `Cmd+Shift+X` en Mac), busca "Claude Code" e instala la del publisher **anthropic**. Requiere VS Code 1.98.0 o superior. Si no aparece tras instalar, reinicia VS Code o ejecuta "Developer: Reload Window" desde la paleta de comandos.

## Paso 3 — Iniciar sesión

Abre el panel de Claude Code y entra con tu cuenta. **Una suscripción Pro o Max sirve; no necesitas clave de API de Anthropic.** La clave de OpenRouter es otra cosa distinta y va en el proyecto, no aquí.

## Paso 4 — Carpeta nueva

`File → Open Folder` y crea una carpeta **vacía y nueva**. VS Code se organiza alrededor de una carpeta y Claude lee todo lo que hay dentro. No apuntes un agente a una carpeta con cosas que te importen mientras aprendes.

```
novela-harness/
```

## Paso 5 — Meter el spec dentro

Copia `SPEC-generador-novelas-v3.md` y esta adenda a `docs/` dentro de la carpeta. Claude necesita leerlos, y solo ve lo que está dentro de la carpeta abierta.

## Paso 6 — `CLAUDE.md`

En la raíz. Es el contexto que Claude ve en cada sesión:

```markdown
# Proyecto: harness generador de novelas

## Qué es
Programa Python que genera novelas completas llamando a modelos vía OpenRouter,
con validación automática por tres validadores en paralelo.

## Documentos de referencia
- `docs/SPEC-generador-novelas-v3.md` — especificación principal
- `docs/ADENDA-openrouter-vscode.md` — capa de modelos y setup. **Pisa a la v3
  donde se contradigan.**

## Reglas
- La capa de modelos es OpenRouter, nunca la API de Anthropic directamente.
- No hay subagentes ni plugins de Claude Code en el runtime: es Python puro.
- Ninguna clave de API en el código ni en `config/`. Solo desde entorno.
- Toda llamada a modelo pasa por `src/agentes.py`. Ningún otro módulo
  llama a la red.
- Los validadores devuelven JSON. Si no parsea, es FALLO, nunca PASA.

## Comandos
- Ejecutar: `python -m src.orquestador`
- Tests: `pytest`
```

La regla del punto único de red es la que te salvará al depurar: cuando algo falle, hay un solo sitio donde poner un `print`.

## Paso 7 — Entorno y seguridad

`.env` en la raíz:

```
OPENROUTER_API_KEY=tu_clave_aqui
```

`.gitignore`:

```
.env
salida/
__pycache__/
.venv/
```

`.claudeignore`:

```
.env
salida/
```

`.claudeignore` cumple dos funciones: reduce el riesgo de que Claude lea datos sensibles como variables de entorno y claves, y mantiene el contexto ligero excluyendo archivos grandes e irrelevantes. Sin él, Claude puede leer tu `.env` al explorar el proyecto.

## Paso 8 — Construir por etapas, no de golpe

El spec es capaz de one-shot, pero **para aprender conviene ir por etapas.** Si pides todo de una y algo falla, no sabrás dónde. Usa el orden de implementación de la v3 §13, una etapa por sesión.

Prompts sugeridos, uno por sesión:

| Sesión | Prompt |
|---|---|
| 1 | "Lee `docs/SPEC-...v3.md` y `docs/ADENDA-...md`. Implementa solo el paso 1 del orden de implementación: estructura de carpetas, `config/` y `src/config.py` con la precedencia de fusión. Añade un test que verifique que `NOVELA_NUM_CAPITULOS=5` pisa el archivo." |
| 2 | "Paso 2: contratos de datos, `biblia.py` y `estado.py`. Tests de serialización ida y vuelta." |
| 3 | "Paso 3: `src/agentes.py` con el cliente de OpenRouter, el parseo defensivo de JSON de la adenda §3.5, y el prompt del arquitecto. Pruébalo con `num_capitulos: 2`." |
| 4 | "Paso 4: el escritor, sin validación todavía. Quiero un pipeline mínimo que produzca dos capítulos de extremo a extremo." |

Después de cada sesión: **ejecuta y mira el resultado antes de seguir.** Esa es la parte que la gente se salta y por la que acaba con un proyecto de mil líneas que no arranca.

## Paso 9 — Control de costes mientras depuras

Estás iterando, así que vas a ejecutar el pipeline docenas de veces. Tres medidas:

- Depura con `num_capitulos: 2` e `intentos_por_modelo: 1`. Suben al final, no antes.
- Usa los modelos más baratos de la escalera mientras el bug es de código y no de calidad literaria. Comprueba en OpenRouter si hay variantes gratuitas o de bajo coste para las primeras corridas.
- Pon un límite de gasto en el panel de OpenRouter antes de la primera ejecución larga. Un bucle de reintentos mal cerrado quema crédito muy rápido, y la v3 §6.2 permite hasta seis intentos por capítulo.

## Paso 10 — Primera verificación real

Cuando tengas el pipeline completo, valida contra los criterios de aceptación de la v3 §12, adaptados:

- Los criterios 1 y 2 (plugin validate / plugin details) **ya no aplican**: no hay plugin.
- El criterio 9 sigue siendo el más importante: **la ventana del escritor en el capítulo 12 no puede ser mayor que en el capítulo 3.** Instrumenta `src/contexto.py` para que registre el tamaño de cada ventana en el log. Si crece con N, la compactación no funciona y el proyecto no escala.
- El criterio 10 (matar el proceso y reanudar) pruébalo pronto. Es barato de implementar al principio y carísimo de añadir después.

---

## Resumen de lo que cambia en el spec

Si le pasas ambos documentos a Claude Code, el CLAUDE.md del paso 6 ya le dice que esta adenda manda donde haya contradicción. No hace falta que reescribas la v3.

## Fuentes

- Referencia de la API de OpenRouter: https://openrouter.ai/docs/api/api-reference/chat/create-a-chat-completion
- Catálogo de modelos y slugs: https://openrouter.ai/models
- Claude Code en VS Code: https://code.claude.com/docs/en/vs-code
