# SPEC — Harness generador de novelas (romance · drama · terror)

**Versión:** 3.0
**Modo de ejecución:** one-shot. Contiene todas las decisiones necesarias. El agente que lo implemente construye el proyecto completo en una sola pasada. Ante ambigüedad no cubierta, aplicar la opción más simple que cumpla los criterios de aceptación y anotarla en `DECISIONES.md`.

---

## 0. Vocabulario

| Término | Qué es aquí |
|---|---|
| **Harness** | El runtime que ejecuta todo. En este proyecto es Claude Code más el orquestador propio |
| **Orquestador** | Código Python determinista. Decide, no razona |
| **Skill** | Archivo markdown con instrucciones. Es *contenido*, se carga en una ventana de contexto |
| **Subagente** | Ventana de contexto aislada con su propio bucle. Devuelve un resultado y muere. Es *aislamiento* |
| **Plugin** | Paquete que agrupa skills, subagentes, hooks y configuración para distribuirlo |
| **Hook** | Script que dispara en un evento del ciclo de vida. Control determinista fuera del modelo |
| **Memoria larga** | Archivos en disco. Sobreviven entre llamadas |
| **Memoria corta** | La ventana de contexto de una llamada concreta. Muere al terminar |

**La distinción que importa:** cada validador es *un subagente que carga su skill*. Si los validadores fueran solo skills ejecutándose en la conversación principal, el texto de los doce capítulos se acumularía en un único contexto y la generación se caería por desbordamiento hacia el capítulo siete.

---

## 1. Inventario de componentes

Todo lo que el proyecto necesita, y si lo aporta Claude Code o hay que construirlo.

### 1.1 Componentes de Claude Code

| Componente | Cantidad | Ubicación | Lo aporta |
|---|---|---|---|
| Plugin manifest | 1 | `.claude-plugin/plugin.json` | Se construye |
| Skills | 6 | `skills/<nombre>/SKILL.md` | Se construyen |
| Subagentes | 5 | `agents/<nombre>.md` | Se construyen |
| Hooks | 3 | `hooks/hooks.json` | Se construyen |
| Referencias de género | 3 | `skills/novela-genero/references/` | Se construyen |
| Servidores MCP | 0 | — | **No se necesita ninguno** |
| Servidores LSP | 0 | — | No aplica |
| Agent Teams | 0 | — | No se usa: el paralelismo lo da el orquestador |
| CLAUDE.md | 0 | — | No aplica: los plugins aportan contexto vía skills, no CLAUDE.md |

### 1.2 Componentes propios del harness

| Componente | Archivo | Responsabilidad |
|---|---|---|
| Orquestador | `src/orquestador.py` | Bucle principal, decisiones, escalado |
| Cliente de agentes | `src/agentes.py` | Llamadas al modelo, parseo y validación de JSON |
| Gestor de biblia | `src/biblia.py` | Lectura, escritura y compactación del estado |
| Gestor de contexto | `src/contexto.py` | Ensambla la ventana de cada llamada según el presupuesto |
| Puntuación | `src/puntuacion.py` | Cálculo de la mejor versión |
| Gestor de estado | `src/estado.py` | Checkpoint y reanudación |
| Cargador de config | `src/config.py` | Fusiona la carpeta `config/` según precedencia |
| Ensamblador | `src/ensamblador.py` | Manuscrito e informe |

### 1.3 Verificación del inventario

Una vez instalado el plugin, `claude plugin details novela-harness` imprime el inventario real de componentes agrupados en Skills, Agents, Hooks y servidores MCP, junto con una estimación del coste en tokens que añade a cada sesión. **Este comando es la comprobación oficial de que el inventario del spec coincide con lo implementado.**

Antes de publicar: `claude plugin validate . --strict`.

---

## 2. Gestión de contexto

Esta es la parte que decide si el harness funciona a doce capítulos o se cae en el séptimo.

### 2.1 Memoria larga (disco)

Persiste entre llamadas y entre ejecuciones.

| Archivo | Contenido | Se actualiza |
|---|---|---|
| `salida/biblia.json` | Estado canónico: personajes, outline, timeline, hechos | Tras cada capítulo aprobado |
| `salida/estado.json` | Progreso: capítulo actual, intento, modelo activo | Tras cada intento |
| `salida/resumenes/cap-NN.md` | 2–3 frases por capítulo | Tras cada capítulo aprobado |
| `salida/memoria-estilo.json` | Muletillas y frases recurrentes detectadas | Tras cada validación de estilo |
| `salida/.tmp/cap-NN-intento-M.md` | Texto de cada intento | Cada intento |
| `salida/.tmp/cap-NN-intento-M.json` | Veredictos y puntuación del intento | Cada intento |

Los `.tmp` son obligatorios: sin ellos no se puede elegir la mejor versión al agotar la escalera de modelos. Se borran al ensamblar.

`estado.json` permite reanudar una ejecución interrumpida sin regenerar los capítulos ya aprobados.

### 2.2 Memoria corta (ventana de contexto)

Cada agente recibe **solo** lo que necesita. Un contexto más pequeño no es solo más barato: es más preciso, porque el modelo no se distrae con material irrelevante.

| Agente | Qué entra en su ventana | Qué NO entra |
|---|---|---|
| **Arquitecto** | Config de novela y estructura | Nada más: es la primera llamada |
| **Escritor** | Biblia (personajes, ambientación, outline completo), hechos vigentes, resúmenes de capítulos 1…N−2, **texto completo solo del capítulo N−1**, problemas del intento anterior | Texto completo de capítulos anteriores a N−1 |
| **Continuidad** | Biblia completa + texto del capítulo | Capítulos anteriores, referencias de género, memoria de estilo |
| **Género** | Referencia del género + texto del capítulo + posición en el arco | La biblia entera, los capítulos anteriores |
| **Estilo** | Texto del capítulo + `memoria-estilo.json` | La biblia, el outline, los capítulos anteriores |
| **Ensamblador** | Lista de rutas de archivo y metadatos | El texto de los capítulos: concatena por streaming |

**Regla:** el capítulo N−1 entra completo porque el escritor necesita la voz y la transición inmediata. Los anteriores entran comprimidos como resumen. Esto mantiene la ventana del escritor aproximadamente constante sea cual sea N.

### 2.3 Compactación

`hechos_establecidos` crece sin límite y acabaría dominando la ventana del escritor. Cada hecho lleva una etiqueta:

- `permanente`: siempre entra en contexto (muerte de un personaje, revelación estructural).
- `efimero`: entra solo si pertenece a los últimos `ventana_hechos` capítulos (por defecto 3).

Cuando `hechos_establecidos` supera `umbral_compactacion` entradas (por defecto 60), el orquestador lanza una pasada de compactación que fusiona hechos efímeros antiguos en un resumen por capítulo y los retira de la lista activa. Los `permanente` nunca se compactan.

### 2.4 Presupuesto de contexto

`src/contexto.py` calcula el tamaño de cada ventana antes de llamar. Si excede `max_tokens_contexto` (por defecto 100.000), aplica en orden: recortar hechos efímeros, acortar resúmenes, y como último recurso omitir el texto del capítulo N−1 dejando solo su resumen. Toda reducción se registra en el informe.

---

## 3. Flujo

```
Inicio
  → Orquestador: carga config/ (fusión por precedencia)
  → Agente Arquitecto: premisa, personajes, outline
  → Biblia de la novela (personajes · timeline · hechos)
  → Agente Escritor: redacta capítulo N          ◄─────────────┐
  → Validadores EN PARALELO, cada uno en su subagente:         │
       · Continuidad  ¿contradice la biblia?                   │
       · Género       ¿cumple tono y convenciones?             │
       · Estilo       ¿repetitivo, cliché, ritmo?              │
  → Orquestador: ¿los tres PASAN?                              │
       · No  → guardar intento, puntuar, escalar si toca,      │
               reescribir con lista de problemas ──────────────┘
       · Sí  → actualizar biblia y resúmenes
  → ¿Quedan capítulos?  Sí → capítulo N+1
                        No → Ensamblar manuscrito
  → Novela e informe
```

---

## 4. Configuración: carpeta `config/`

La configuración no es un archivo sino un directorio, para separar lo que cambia a menudo de lo que casi nunca cambia.

```
config/
├── novela.json          # cambia en cada generación
├── estructura.json      # cambia a veces
├── modelos.json         # casi nunca cambia
├── validacion.json      # casi nunca cambia
├── runtime.json         # casi nunca cambia
└── perfiles/
    ├── romance.json
    ├── drama.json
    └── terror.json
```

### 4.1 Precedencia de fusión

De menor a mayor prioridad. Lo posterior pisa lo anterior:

1. Valores por defecto embebidos en el código
2. `config/perfiles/<genero>.json`, según el género de `novela.json`
3. Los cinco archivos de `config/`
4. Variables de entorno con prefijo `NOVELA_` (ejemplo: `NOVELA_NUM_CAPITULOS=5`)
5. Argumentos de línea de comandos

La configuración efectiva se vuelca en `salida/config-efectiva.json` al arrancar, para que el informe sea reproducible.

### 4.2 `config/novela.json`

```json
{
  "titulo": null,
  "genero": "terror",
  "tono": "sobrio, contenido",
  "punto_de_vista": "tercera persona limitada",
  "idioma": "es",
  "semilla_tematica": null
}
```

### 4.3 `config/estructura.json`

```json
{
  "num_capitulos": 12,
  "palabras_min": 1200,
  "palabras_max": 2200
}
```

### 4.4 `config/modelos.json`

```json
{
  "escalera_escritor": ["claude-haiku-4-5", "claude-sonnet-5", "claude-opus-5"],
  "intentos_por_modelo": 2,
  "modelo_validadores": "claude-sonnet-5",
  "modelo_arquitecto": "claude-sonnet-5",
  "modelo_ensamblador": "claude-haiku-4-5"
}
```

### 4.5 `config/validacion.json`

```json
{
  "validadores_activos": ["continuidad", "genero", "estilo"],
  "pesos_gravedad": { "alta": 5, "media": 2, "baja": 1 },
  "paralelo": true
}
```

### 4.6 `config/runtime.json`

```json
{
  "directorio_salida": "./salida",
  "max_tokens_contexto": 100000,
  "ventana_hechos": 3,
  "umbral_compactacion": 60,
  "reanudar_si_existe_estado": true,
  "conservar_intentos": false,
  "nivel_log": "info"
}
```

### 4.7 `config/perfiles/<genero>.json`

Preajustes por género que pisan los valores por defecto. Ejemplo de `terror.json`:

```json
{
  "estructura": { "palabras_min": 900, "palabras_max": 1600 },
  "novela": { "tono": "sobrio, contenido, sin adjetivación excesiva" }
}
```

Capítulos más cortos en terror porque el ritmo corto sostiene mejor la tensión. El usuario puede pisarlo desde `estructura.json`.

### 4.8 Credenciales

La clave de API se lee **exclusivamente** de la variable de entorno `ANTHROPIC_API_KEY`. Ningún archivo bajo `config/` contiene secretos. `config/` se versiona en git; no hay nada que excluir.

---

## 5. Inputs y outputs

### 5.1 Inputs

| Input | Origen | Obligatorio |
|---|---|---|
| Configuración | Carpeta `config/` | Sí |
| Clave de API | Variable de entorno | Sí |
| Semilla temática | `config/novela.json` | No |
| Estado previo | `salida/estado.json` | No: si existe y `reanudar_si_existe_estado`, reanuda |

### 5.2 Outputs

| Archivo | Contenido |
|---|---|
| `salida/manuscrito.md` | Portada + capítulos concatenados en orden |
| `salida/biblia.json` | Estado final completo |
| `salida/informe-validacion.md` | Por capítulo: intentos, modelo que lo resolvió, veredictos, problemas sin resolver, puntuación, recortes de contexto aplicados |
| `salida/config-efectiva.json` | Configuración fusionada realmente usada |

Los capítulos sueltos y los intentos viven en `salida/.tmp/` y se borran al ensamblar, salvo que `conservar_intentos` sea `true`.

---

## 6. Bucle de reescritura y escalado

### 6.1 Regla de bloqueo

Los tres validadores bloquean por igual. Un capítulo se aprueba **solo si los tres devuelven `PASA`**. Un único `FALLO`, de cualquier validador y con cualquier gravedad, dispara la reescritura.

### 6.2 Escalera de modelos

Con la configuración por defecto (3 modelos × 2 intentos), **6 intentos máximos** por capítulo:

| Intento | Modelo del escritor |
|---|---|
| 1, 2 | `claude-haiku-4-5` |
| 3, 4 | `claude-sonnet-5` |
| 5, 6 | `claude-opus-5` |

Cada reintento recibe la lista acumulada de problemas. Al escalar de modelo se pasan también los problemas: no se empieza de cero.

### 6.3 Los validadores no escalan

`modelo_validadores` es fijo durante toda la generación. Si cambiara junto con el escritor, las puntuaciones de los intentos dejarían de ser comparables y la regla de mejor versión no tendría sentido.

### 6.4 Mejor versión intentada

Agotada la escalera sin que ningún intento pase, se acepta la versión de menor puntuación:

```
puntuacion = Σ (problemas de los tres validadores × peso de su gravedad)
```

Con los pesos por defecto, dos problemas de gravedad media puntúan 4 y uno de gravedad alta puntúa 5: gana el primero. **Empate:** gana el intento más tardío, por haber incorporado más feedback.

Se marca en el informe como `ACEPTADO_POR_PUNTUACION`.

### 6.5 Nunca abortar

Ningún capítulo detiene la generación.

---

## 7. Contratos de datos

### 7.1 `biblia.json`

```json
{
  "titulo": "string",
  "genero": "romance | drama | terror",
  "premisa": "string",
  "conflicto_central": "string",
  "ambientacion": { "lugar": "string", "epoca": "string", "reglas": ["string"] },
  "personajes": [
    {
      "nombre": "string",
      "rol": "protagonista | antagonista | secundario",
      "rasgos_fijos": ["string"],
      "motivacion": "string",
      "secreto": "string"
    }
  ],
  "outline": [{ "capitulo": 1, "sinopsis": "string", "cambio": "string" }],
  "timeline": [{ "capitulo": 1, "momento": "string" }],
  "hechos_establecidos": [
    { "capitulo": 1, "hecho": "string", "persistencia": "permanente | efimero" }
  ]
}
```

### 7.2 JSON de veredicto

Formato idéntico para los tres validadores.

```json
{
  "validador": "continuidad | genero | estilo",
  "capitulo": 3,
  "veredicto": "PASA | FALLO",
  "problemas": [
    {
      "gravedad": "alta | media | baja",
      "descripcion": "string",
      "evidencia": "string",
      "correccion_sugerida": "string"
    }
  ]
}
```

`veredicto: "PASA"` obliga a `problemas: []`.

### 7.3 `estado.json`

```json
{
  "capitulo_actual": 4,
  "intento_actual": 2,
  "modelo_actual": "claude-haiku-4-5",
  "capitulos_aprobados": [1, 2, 3],
  "capitulos_marcados": [],
  "iniciado": "2026-09-15T10:00:00Z"
}
```

### 7.4 `memoria-estilo.json`

```json
{
  "frases_recurrentes": [{ "frase": "string", "apariciones": 4, "capitulos": [1, 3, 5] }],
  "muletillas": ["string"]
}
```

---

## 8. Skills

Cada skill es un `SKILL.md` con frontmatter YAML (`name`, `description`) y cuerpo en imperativo. La `description` es el mecanismo de activación: debe decir qué hace **y cuándo usarse**.

| Skill | Rol |
|---|---|
| `novela-arquitecto` | Premisa, conflicto, 3–6 personajes con rasgos verificables, ambientación, outline de exactamente `num_capitulos` entradas. Salida: solo el JSON de la biblia |
| `novela-escritor` | Redacta el capítulo N. Longitud dentro del rango configurado. Respeta rasgos fijos y hechos vigentes. Solo prosa narrativa. Salida: `# Capítulo N — Título` más el texto |
| `novela-continuidad` | Audita rasgos, nombres, cronología, hechos, objetos, lugares, relaciones y punto de vista. No juzga calidad ni tono. Cada problema cita el dato de la biblia y el fragmento que lo contradice. Salida: JSON de veredicto |
| `novela-genero` | Lee primero `references/<genero>.md`. Evalúa registro emocional, ritmo, elementos exigidos por la fase del arco y clichés prohibidos. Salida: JSON de veredicto |
| `novela-estilo` | Detecta repetición léxica y sintáctica, muletillas del modelo, clichés de prosa, diálogo sin subtexto, problemas de ritmo. Consulta `memoria-estilo.json` para detectar repeticiones entre capítulos. Salida: JSON de veredicto |
| `novela-ensamblador` | Concatena con portada, genera el informe. No reescribe |

### 8.1 Referencias de género

- **`romance.md`** — arco encuentro → tensión → obstáculo → reconciliación. La química se muestra en escena, no se resume. Prohibidos: el malentendido que se resolvería con una frase; la declaración de amor sin nada en juego.
- **`drama.md`** — arco dilema → escalada → punto de quiebre → consecuencia irreversible. Cada capítulo cierra con el protagonista en peor o distinta posición. Prohibidos: deus ex machina; conflicto que se disuelve sin coste.
- **`terror.md`** — arco normalidad → grieta → escalada → revelación. La amenaza se sugiere antes de mostrarse. Prohibidos: susto sin construcción previa; explicación completa antes del último tercio.

---

## 9. Subagentes

Archivos markdown en `agents/`. Los subagentes de plugin admiten `name`, `description`, `model`, `effort`, `maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background` e `isolation`. **Por seguridad, `hooks`, `mcpServers` y `permissionMode` no están soportados en subagentes distribuidos por plugin**, así que no se usan aquí.

El campo `skills` precarga el contenido completo de la skill en el contexto del subagente al arrancar, sin que tenga que descubrirla durante la ejecución. Se usa en los cinco.

| Subagente | `model` | `skills` precargadas | `disallowedTools` |
|---|---|---|---|
| `novela-arquitecto` | sonnet | `novela-arquitecto` | Write, Edit |
| `novela-escritor` | inherit | `novela-escritor` | Write, Edit |
| `novela-continuidad` | sonnet | `novela-continuidad` | Write, Edit, Bash |
| `novela-genero` | sonnet | `novela-genero` | Write, Edit, Bash |
| `novela-estilo` | sonnet | `novela-estilo` | Write, Edit, Bash |

**`model: inherit` en el escritor** es lo que permite el escalado: el orquestador fija el modelo de la sesión y el subagente lo hereda.

**Ningún subagente escribe en disco.** Devuelven texto o JSON, y el orquestador es quien persiste. Así hay un único punto de escritura y el estado nunca queda a medias.

**Caveat a verificar en tu versión de Claude Code:** existe un reporte de que una skill con `context: fork` y `agent: <nombre>` puede ejecutarse en línea en vez de despacharse al subagente nombrado. El rodeo documentado es indicar explícitamente en el cuerpo de la skill que use la herramienta Task para lanzar el subagente. Comprobar el comportamiento antes de confiar en `context: fork`.

---

## 10. Hooks

`hooks/hooks.json`. Tres hooks, todos de tipo `command`:

| Evento | Qué hace | Por qué |
|---|---|---|
| `SessionStart` | Verifica que `ANTHROPIC_API_KEY` está definida y que `config/` parsea | Falla rápido, antes de gastar una sola llamada |
| `SubagentStop` | Registra en el log qué subagente terminó, con qué modelo y cuántos tokens | Es la fuente del informe de validación |
| `PreCompact` | Vuelca `estado.json` a disco antes de que el contexto se compacte | Evita perder el progreso en una sesión larga |

Los hooks usan `${CLAUDE_PLUGIN_ROOT}` para referenciar sus scripts y `${CLAUDE_PROJECT_DIR}` para el directorio de salida.

---

## 11. Estructura de archivos completa

```
novela-harness/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── novela-arquitecto/SKILL.md
│   ├── novela-escritor/SKILL.md
│   ├── novela-continuidad/SKILL.md
│   ├── novela-genero/
│   │   ├── SKILL.md
│   │   └── references/{romance,drama,terror}.md
│   ├── novela-estilo/SKILL.md
│   └── novela-ensamblador/SKILL.md
├── agents/
│   ├── novela-arquitecto.md
│   ├── novela-escritor.md
│   ├── novela-continuidad.md
│   ├── novela-genero.md
│   └── novela-estilo.md
├── hooks/
│   └── hooks.json
├── scripts/
│   ├── verificar-entorno.sh
│   ├── registrar-subagente.sh
│   └── checkpoint-estado.sh
├── config/
│   ├── novela.json
│   ├── estructura.json
│   ├── modelos.json
│   ├── validacion.json
│   ├── runtime.json
│   └── perfiles/{romance,drama,terror}.json
├── src/
│   ├── orquestador.py
│   ├── agentes.py
│   ├── biblia.py
│   ├── contexto.py
│   ├── puntuacion.py
│   ├── estado.py
│   ├── config.py
│   └── ensamblador.py
├── salida/
│   ├── manuscrito.md
│   ├── biblia.json
│   ├── informe-validacion.md
│   ├── config-efectiva.json
│   ├── estado.json
│   ├── resumenes/
│   ├── memoria-estilo.json
│   └── .tmp/
├── DECISIONES.md
└── README.md
```

**Restricción:** el directorio `.claude-plugin/` contiene únicamente `plugin.json`. Todos los demás directorios de componentes (`skills/`, `agents/`, `hooks/`) van en la raíz del plugin, nunca dentro de `.claude-plugin/`.

### 11.1 `plugin.json`

```json
{
  "name": "novela-harness",
  "displayName": "Generador de novelas",
  "version": "3.0.0",
  "description": "Genera novelas de romance, drama y terror con validación por subagentes",
  "license": "MIT"
}
```

`name` es el único campo obligatorio; el resto es metadato. Las rutas por defecto (`skills/`, `agents/`, `hooks/hooks.json`) se autodescubren, así que no hace falta declararlas.

---

## 12. Criterios de aceptación

1. `claude plugin validate . --strict` pasa sin errores.
2. `claude plugin details novela-harness` lista 6 skills, 5 agentes y 3 hooks.
3. Con `num_capitulos: 3` e `intentos_por_modelo: 1`, la ejecución termina sin errores y produce los cuatro archivos de salida.
4. Los tres validadores se ejecutan **en paralelo**, no en secuencia.
5. Un `FALLO` de cualquier validador dispara reescritura, sea cual sea su gravedad.
6. Al agotar los intentos de un modelo, el siguiente usa el modelo siguiente de la escalera, y el informe lo refleja.
7. Agotada la escalera completa, se acepta la versión de menor puntuación, marcada como `ACEPTADO_POR_PUNTUACION`.
8. Ningún fallo de capítulo detiene la generación.
9. **La ventana de contexto del escritor en el capítulo 12 no es mayor que en el capítulo 3** (verifica que la compactación funciona).
10. Matar el proceso en el capítulo 5 y relanzarlo reanuda desde el 5, no desde el 1.
11. Introducir una contradicción manual (cambiar el color de ojos de un personaje) hace que `novela-continuidad` devuelva `FALLO`.
12. Una variable `NOVELA_NUM_CAPITULOS=5` pisa el valor de `config/estructura.json`.
13. Toda salida declarada como JSON parsea sin limpieza manual de backticks.
14. La clave de API no aparece en ningún archivo del repositorio.

---

## 13. Orden de implementación

1. `plugin.json`, estructura de carpetas, `config/` y `src/config.py` con la precedencia de fusión.
2. Contratos de datos, `biblia.py`, `estado.py`.
3. `novela-arquitecto`: skill, subagente y parseo validado.
4. `novela-escritor` sin validación: pipeline mínimo de extremo a extremo.
5. `contexto.py`: presupuesto y compactación. Verificar el criterio 9 antes de seguir.
6. `novela-continuidad` y el bucle de reintentos con un solo modelo.
7. Escalera de modelos y `puntuacion.py`.
8. `novela-genero` y `novela-estilo`, con ejecución en paralelo.
9. Hooks y logging.
10. `novela-ensamblador` e informe.

Cada paso deja el proyecto en estado ejecutable.

---

## 14. Fuentes

- Referencia de plugins de Claude Code: https://code.claude.com/docs/en/plugins-reference
- Subagentes: https://code.claude.com/docs/en/sub-agents
- Visión general de extensiones: https://code.claude.com/docs/en/features-overview
