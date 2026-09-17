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

**Entorno verificado:** los hallazgos 1 a 8 se comprobaron con Claude Code
**2.1.263**. El 2026-09-17, más tarde, se actualizó a la **2.1.274** y se repitió
la sonda del hallazgo 3, que es el único que dependía de la versión.
Documentación consultada: `code.claude.com/docs/en/sub-agents` y `/skills`,
contrastada con las definiciones de tipos `sdk-tools.d.ts` de la versión
instalada.

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

### Hallazgo 3 — `omitClaudeMd` necesita la 2.1.271. Resuelto al actualizar

**Qué se comprobó:** por defecto, el contexto inicial de un subagente incluye
toda la jerarquía de CLAUDE.md (el de usuario, el del proyecto, el local y las
políticas gestionadas), salvo en los agentes integrados Explore y Plan. La
opción documentada para evitarlo es `omitClaudeMd: true` en el frontmatter.

**Primera prueba, con la 2.1.263:** se lanzó el subagente `estilo`, que lleva esa
línea, con una sonda que le preguntaba qué reglas de proyecto había recibido.
Respondió con el nombre del proyecto, su estructura de carpetas, sus comandos de
ejecución y el contenido de CLAUDE.md. La opción se estaba ignorando.

**Causa:** `omitClaudeMd` se añadió en la versión **2.1.271** del CLI. Un campo
de frontmatter desconocido se ignora en silencio, sin aviso ni error, así que el
archivo parece correcto y no lo es. Esto es lo que hace que la versión del CLI
sea un requisito de ejecución y no un detalle: el fallo no se manifiesta como un
error, sino como un aislamiento que silenciosamente no existe.

**Segunda prueba, con la 2.1.274 (misma sonda, mismo subagente):**

| Pregunta de la sonda | Respuesta con 2.1.263 | Respuesta con 2.1.274 |
|---|---|---|
| ¿Has recibido un CLAUDE.md? | Sí, y lo citó | **NO** |
| Estructura de carpetas del proyecto | La enumeró | «No tengo información clara» |
| Comando de los tests | `pytest` | **NO LO SE** |

**Decisión:** la línea `omitClaudeMd: true` se queda en los cinco subagentes y
la versión mínima de Claude Code pasa a ser un requisito documentado en
`EJECUCION.md` §1.1. El aislamiento de la sección 2.2 del spec se cumple.

**Residuo conocido, y es inevitable:** el subagente sigue sabiendo el nombre del
proyecto, porque deduce `My_novel_story` de la ruta del directorio de trabajo,
que va en su bloque de entorno y no en CLAUDE.md. Es un dato inerte: no le
cuenta qué arquitectura tiene el proyecto ni qué reglas sigue. Si algún día
importara de verdad, la única salida sería un nombre de carpeta neutro.

**Por qué importa:** la tabla de la sección 2.2 dice exactamente qué ve cada
validador, y ese aislamiento es lo que da sentido a tener validadores separados.
Un CLAUDE.md que describe la arquitectura del proyecto metido en la ventana del
validador de estilo no es solo ruido: es ruido con autoridad, porque llega con
formato de instrucciones y el validador no tiene forma de saber que no van con
él.

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

### Decisión 9 — La temperatura ya no se puede fijar, y eso cambia qué significa la puntuación

**Qué se comprobó:** la herramienta de delegación de la versión instalada acepta
`subagent_type`, `prompt`, `description`, `model` y poco más. **No acepta
ningún parámetro de muestreo**: ni `temperature`, ni `top_p`, ni una semilla. El
frontmatter del subagente tampoco admite esos campos, y lo que no reconoce lo
ignora en silencio (misma trampa del hallazgo 3). En la práctica: cada delegación
usa el muestreo por defecto del modelo y el harness no tiene voz en ello.

**Qué se pierde.** La configuración anterior fijaba una temperatura por rol, y
cada una tenía su motivo:

| Rol | Temperatura anterior | Para qué |
|---|---|---|
| Arquitecto | 0.9 | Que dos ejecuciones no produzcan la misma novela |
| Escritor | 0.8 | Prosa con variedad |
| Validadores | **0.1** | Que juzgar el mismo texto dos veces dé el mismo resultado |

Las dos primeras eran comodidades: un modelo por defecto ya escribe con
variedad suficiente, y si una premisa sale sosa se relanza al arquitecto. La
tercera no era una comodidad, era un cimiento.

**Qué implica para la regla de mejor versión (spec §6.4, `EJECUCION.md` §3.5f).**
La regla dice que, agotada la escalera sin aprobación, se acepta el intento de
menor puntuación, siendo:

```
puntuacion = Σ (problemas de los tres validadores × peso de su gravedad)
```

Con los validadores a 0.1, esa puntuación era casi una **medida**: el mismo
texto juzgado dos veces daba la misma lista de problemas, así que una diferencia
de dos puntos entre el intento 3 y el intento 5 significaba algo sobre los
textos. Sin temperatura fija, parte de esa diferencia es ruido de muestreo del
propio validador, no una propiedad del capítulo.

La regla **se mantiene**, porque sigue siendo la mejor respuesta disponible a
"elige uno de seis textos malos", pero baja de categoría: deja de ser una medida
y pasa a ser una **ordenación aproximada entre intentos de un mismo capítulo
dentro de una misma generación**. De ahí tres consecuencias concretas:

1. **Nunca compares puntuaciones entre capítulos ni entre generaciones.** Antes
   ya era discutible; ahora carece de sentido.
2. **Nada debe depender de un umbral absoluto de puntuación.** No se puede
   escribir "si la puntuación baja de 5, apruébalo": el mismo capítulo puede
   puntuar 4 o 6 según el día. El único criterio de aprobación sigue siendo el
   de la regla 1: los tres validadores dicen `PASA`.
3. **El desempate gana peso.** Ante puntuaciones parecidas —y ahora lo van a ser
   más a menudo— manda la regla de "gana el intento más tardío". No es un
   capricho: el intento tardío ha incorporado más feedback acumulado, y eso sí es
   una propiedad real del texto, no una casualidad del muestreo.

**Qué hacer en su lugar.** Fijar `modelos.validadores` y no tocarlo durante una
generación pasa de ser una regla prudente a ser **la única palanca que queda**
para que dos intentos sean comparables. Por eso la regla 3 de `EJECUCION.md` §4
se mantiene y se refuerza. Y al leer el informe, fíate de los problemas
concretos y de su evidencia —que son verificables abriendo el manuscrito— antes
que de la diferencia de uno o dos puntos entre dos intentos.

**Alternativa descartada:** pedir el mismo veredicto tres veces y quedarse con la
mediana. Reduciría el ruido de verdad, pero triplica las delegaciones de
validación, que ya son tres por intento y hasta dieciocho por capítulo. No
compensa para una regla que solo se aplica cuando ya han fallado los seis
intentos.

---

### Decisión 10 — Los resúmenes los escribe un subagente, no el outline

**El problema.** El escritor del capítulo N recibe el texto completo del
capítulo N−1 y, de los capítulos 1…N−2, solo un resumen. Ese resumen es lo
**único** que sabrá de ellos. Alguien tiene que escribirlo, y había dos
candidatos.

**Opción A, la sinopsis del outline.** Es la que se usó mientras no existía el
resumidor. Sale gratis: el arquitecto ya la escribió, es determinista y no
cuesta ninguna delegación.

**Opción B, un subagente que lea el capítulo.** Cuesta una delegación de `haiku`
por capítulo.

**Decisión: la opción B.** El motivo es que las dos cosas no son la misma:

| | Qué contiene |
|---|---|
| Sinopsis del outline | Lo que el arquitecto **planeó** que pasara |
| Resumen del resumidor | Lo que el capítulo **dice** que pasó |

Mientras un capítulo se aprueba al primer intento, las dos casi coinciden. Pero
el contrato permite hasta seis intentos, y cada reescritura responde a problemas
concretos de continuidad, género y estilo: un capítulo que costó cuatro intentos
ha sido empujado cuatro veces en direcciones que el outline no previó. A partir
de ahí, la sinopsis describe una novela que no se escribió.

Y el error se acumula hacia adelante. El escritor del capítulo 8 lee los
resúmenes del 1 al 6. Si tres de ellos describen el plan y no el texto, está
escribiendo la continuación de una novela que no existe, y quien paga la factura
es el validador de continuidad, que empezará a sacar `FALLO` sin que el problema
esté en el capítulo 8.

**Qué se le pasa al resumidor, y qué no.** Recibe el número del capítulo y su
texto. **No recibe el outline**, y eso es lo importante del diseño: teniendo el
plan delante resumiría el plan, que es más fácil de resumir y suena mejor
escrito. La única forma de garantizar que levanta acta del texto es que el texto
sea lo único que tenga.

Tampoco recibe la biblia ni los capítulos anteriores: no le hacen falta para
resumir uno solo, y cada cosa que entre en su ventana es una cosa más que puede
colarse en el resumen.

**Lo que cuesta.** Una delegación de `haiku` por capítulo cerrado, menos el
último, cuyo resumen no leería nadie. En una novela de doce capítulos son once
delegaciones sobre las cuarenta y tantas que ya cuesta. Es el añadido más barato
del harness.

**La válvula de escape.** Si el resumidor devuelve algo que no parsea, el comando
falla y sugiere reintentar. Si insiste,
`registrar-resumen --capitulo N --usar-sinopsis` cae a la sinopsis del outline
sin delegar en nadie. Es peor que el acta, pero la regla 1 dice que ningún
capítulo detiene la generación, y sería absurdo que una novela entera se quedara
parada esperando tres frases.

---

### Estado de las pruebas de los subagentes (2026-09-17)

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
(`src/biblia.py` más `extraer_json`, que entonces vivía en `src/agentes.py`
y hoy está en `archivo/agentes.py`). De paso quedó
demostrado por qué el parseo defensivo sigue haciendo falta: la salida del
subproceso traía una línea de aviso delante del JSON, y el extractor la sorteó.
