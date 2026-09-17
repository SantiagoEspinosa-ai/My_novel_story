# DECISIONES.md

Registro de las decisiones de arquitectura que no son evidentes al leer el
código, con el porqué de cada una. Si dentro de un mes algo te parece raro,
búscalo aquí antes de "arreglarlo".

Formato: una entrada por decisión, con fecha, qué se comprobó y qué se decidió.

---

## 2026-09-17 — Cambio de arquitectura: de OpenRouter a subagentes de Claude Code

**Contexto:** `SPEC-generador-novelas-v3.md` vuelve a ser la especificación
principal. `ADENDA-openrouter-vscode.md` queda deprecada. El orquestador ya no es
un programa Python que llama a OpenRouter: es Claude Code, y los cinco agentes
del spec pasan a ser subagentes de proyecto.

**Entorno verificado:** Claude Code **2.1.263** (confirmado en el `package.json`
del paquete instalado, no solo con `claude --version`). Documentación consultada:
`code.claude.com/docs/en/sub-agents` y `/skills`, contrastada con las
definiciones de tipos `sdk-tools.d.ts` de esa misma versión instalada.

Todo lo que sigue se comprobó ejecutándolo, no leyéndolo.

---

### Hallazgo 1 — El modelo se puede fijar en cada invocación

**Qué dice la versión instalada:** la herramienta que lanza subagentes acepta un
parámetro `model` (`sonnet`, `opus`, `haiku`, `fable`) y su documentación indica
que **tiene precedencia sobre el `model` del frontmatter** del subagente.

**Decisión:** el escritor es **un solo subagente**, no tres. La escalera de la
sección 6.2 del spec (haiku → sonnet → opus) la aplica el orquestador pasando el
modelo que toca en cada intento.

**Por qué importa:** tres definiciones del escritor serían tres archivos que
mantener en paralelo, y bastaría tocar uno y olvidar los otros dos para que los
intentos dejaran de ser comparables. El frontmatter deja `model: sonnet` como
valor por defecto sensato para cuando nadie pase nada.

---

### Hallazgo 2 — El cuerpo de un subagente es un prompt estático

**Qué se comprobó:** el markdown de un subagente **no** admite inyección
dinámica (`` !`comando` ``) ni inclusión de archivos. Lo que escribes ahí es
literalmente todo lo que recibe. Las skills sí admiten inyección dinámica.

**Decisión:** cada subagente precarga una **skill puente** con el campo `skills:`
del frontmatter. Cada skill tiene una sola línea de contenido:

```
!`cat "${CLAUDE_PROJECT_DIR}/prompts/<rol>.md"`
```

**Por qué importa:** `prompts/` sigue siendo la única fuente de verdad de los
prompts de sistema. No hay una segunda copia que se desincronice, y editar
`prompts/estilo.md` cambia el comportamiento del validador sin tocar nada más.
La alternativa descartada era que el subagente leyera el archivo con Read al
arrancar: funciona, pero gasta un turno por invocación (unas 40 en una novela de
doce capítulos) y depende de que obedezca esa primera instrucción.

**Comprobado ejecutándolo:** el validador de continuidad devolvió el esquema
exacto del veredicto, la escala de gravedad y las reglas de evidencia del
prompt, ninguna de las cuales aparecía en el mensaje de delegación.

---

### Hallazgo 3 — `omitClaudeMd` NO funciona en la 2.1.263. Pendiente de actualizar

**Qué se comprobó:** por defecto, el contexto inicial de un subagente incluye
toda la jerarquía de CLAUDE.md (el de usuario, el del proyecto, el local y las
políticas gestionadas), salvo en los agentes integrados Explore y Plan. La
opción documentada para evitarlo es `omitClaudeMd: true` en el frontmatter.

**Qué pasó al probarlo:** se lanzó el subagente `estilo`, que lleva esa línea,
con una sonda que le preguntaba qué reglas de proyecto había recibido. Respondió
con el nombre del proyecto, su estructura de carpetas, sus comandos de ejecución
y el contenido de CLAUDE.md. **La opción se está ignorando.**

**Causa:** `omitClaudeMd` se añadió en la versión **2.1.271** del CLI. La versión
instalada es la **2.1.263**. Un campo de frontmatter desconocido se ignora en
silencio, sin aviso ni error, así que el archivo parece correcto y no lo es.

**Decisión:** la línea `omitClaudeMd: true` se queda en los cinco subagentes.
Hoy no hace nada, y el día que se actualice el CLI empieza a funcionar sin tocar
ningún archivo. Mientras tanto, el aislamiento de la sección 2.2 del spec está
**incompleto**: los validadores ven CLAUDE.md.

**Qué falta:** actualizar Claude Code a 2.1.271 o posterior y repetir la sonda.
Es una decisión del usuario porque afecta a una herramienta global de su máquina,
no solo a este proyecto.

**Por qué importa:** la tabla de la sección 2.2 dice exactamente qué ve cada
validador, y ese aislamiento es lo que da sentido a tener validadores separados.
Un CLAUDE.md que describe la arquitectura antigua metido en la ventana del
validador de estilo no es solo ruido: es ruido que contradice lo que está
haciendo.

---

### Hallazgo 4 — El paralelismo de los tres validadores no tiene problema

**Qué se comprobó:** el límite por defecto son **20 subagentes simultáneos**
(configurable con `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) y **3 niveles** de
anidamiento (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`).

**Decisión:** los tres validadores se lanzan en un solo mensaje, que es lo que
los hace correr a la vez. Necesitamos 3 de 20 y un nivel de 3: sobra margen.

**Por qué importa:** en la arquitectura anterior el paralelismo costaba
`asyncio.gather()` y manejo de excepciones. Aquí sale gratis, pero conviene
saber que el límite existe por si algún día se paralelizan capítulos enteros.

---

### Hallazgo 5 — `--agent` como sesión principal NO precarga las skills

**Qué se comprobó:** `claude -p --agent continuidad` devolvió `SIN
INSTRUCCIONES`, la señal de fallo puesta a propósito en el cuerpo del subagente.
La **misma definición**, invocada como subagente desde una sesión, sí recibe el
prompt completo.

**Decisión:** ninguna que cambie el diseño, pero queda anotado: el patrón de
skill puente **solo se valida por la ruta de delegación**, que es la que usa el
orquestador. No se puede probar un subagente con `--agent` y concluir nada.

**Por qué importa:** esto costó un falso negativo y estuvo a punto de hacernos
cambiar de mecanismo sin motivo. Si algún día un subagente parece no tener
instrucciones, comprueba primero **cómo** lo estás lanzando.

La señal `SIN INSTRUCCIONES` en el cuerpo de los cinco subagentes se queda ahí
justo por esto: distingue "prompt ausente" de "prompt malo". Sin ella, un
subagente sin instrucciones improvisa algo plausible y el fallo pasa inadvertido.

---

### Hallazgo 6 — Las skills se recargan en caliente; los subagentes no

**Qué se comprobó, en esta máquina y en esta versión:** al crear
`.claude/skills/<nombre>/SKILL.md`, la skill aparece en la sesión en curso a los
pocos segundos. Al crear `.claude/agents/<nombre>.md`, el subagente **no**
aparece: la sesión sigue respondiendo `Agent type not found`. Ocurre igual con el
directorio recién creado y con archivos nuevos en un directorio que ya existía.

**Decisión:** después de crear o renombrar un subagente hay que **reiniciar
Claude Code** (o recargar la ventana de VS Code). Mientras tanto, se pueden
probar desde una sesión nueva no interactiva:

```powershell
claude -p 'Lanza el subagente X con la herramienta Agent y pasale ...'
```

**Por qué importa:** es exactamente el tipo de cosa que hace perder una tarde
creyendo que el archivo está mal escrito cuando lo único que pasa es que la
sesión no lo ha visto. Editar el **cuerpo** de un subagente que ya existía sí se
recoge en caliente; crear uno nuevo, no.

**Detalle añadido:** una sesión lanzada con `claude -p` **no puede escribir
archivos**: las peticiones de Write se deniegan por permisos. Si necesitas
quedarte con lo que produce, redirige su salida estándar desde tu propia shell
(`claude -p '...' > archivo.txt`) en vez de pedirle que guarde el archivo.

---

### Hallazgo 7 — Las vallas ```json venían de la sesión intermedia

**Qué se comprobó:** en la primera prueba, hecha por subproceso, la respuesta del
validador llegó envuelta en un bloque de código, que su prompt prohíbe
expresamente. Al repetir la prueba **delegando directamente** desde la sesión
orquestadora, la respuesta empezó por `{` y terminó por `}`, sin vallas.

**Decisión:** no se toca `prompts/continuidad.md`. Las vallas las añadía la
sesión intermedia al imprimir la respuesta, no el validador.

**Por qué importa:** el parseo defensivo (quitar vallas, extraer el primer
`{...}` equilibrado) se mantiene de todas formas, porque un modelo puede
añadirlas cualquier día. Pero no había que arreglar un prompt que no estaba roto.

---

### Decisión 8 — El validador de género lee su propia referencia

**Contexto:** `prompts/genero.md` espera un bloque `CONVENCIONES:` con el
documento de referencia del género. Ese documento depende del género de la
novela y ocupa unos 2,5 KB.

**Decisión:** el orquestador pasa la **ruta** del archivo
(`prompts/referencias/<genero>.md`) y el subagente la lee con Read. El cuerpo del
subagente `genero` lo explica y le prohíbe leer cualquier otro archivo.

**Por qué importa:** si el orquestador leyera la referencia y la copiara en cada
delegación, ese texto se repetiría una vez por capítulo dentro del contexto del
orquestador, que es justo el contexto que hay que cuidar. Así se paga una lectura
barata dentro del contexto aislado del validador, que muere al terminar.

**Comprobado ejecutándolo:** al validador de género se le pasó
`CONVENCIONES: prompts/referencias/terror.md` y un capítulo con tres
infracciones plantadas. Las encontró las tres y citó los clichés prohibidos
palabra por palabra tal como están escritos en ese archivo, así que lo leyó.

---

### Estado de las pruebas de los cinco subagentes (2026-09-17)

Todos probados con datos de juguete, con infracciones plantadas a propósito para
que un acierto no pueda ser casualidad.

| Subagente | Cómo se probó | Resultado |
|---|---|---|
| `continuidad` | Biblia + capítulo con dos contradicciones plantadas (color de ojos, y un perro muerto que ladra) | Encontró las dos. No señaló al personaje nuevo, que no es una contradicción |
| `genero` | Capítulo con tres infracciones de `terror.md` (dos clichés prohibidos y la explicación completa de la amenaza en la fase 1) | Encontró las tres, citando la referencia |
| `estilo` | Capítulo con repeticiones y una memoria de estilo con dos frases ya gastadas | Detectó la repetición entre capítulos y devolvió `nuevas_frases_recurrentes`, campo que solo está en `prompts/estilo.md` |
| `arquitecto` | Configuración de dos capítulos con semilla temática | Biblia validada con `src/biblia.py` contra el contrato 7.1: correcta |
| `escritor` | Biblia y outline del arquitecto, capítulo 1 | Capítulo con la línea de título exigida, en tercera persona limitada y respetando los rasgos fijos |

La validación de la biblia se hizo con el código Python que se conserva
(`src/biblia.py` más `extraer_json` de `src/agentes.py`). De paso quedó
demostrado por qué el parseo defensivo sigue haciendo falta: la salida del
subproceso traía una línea de aviso delante del JSON, y el extractor la sorteó.
