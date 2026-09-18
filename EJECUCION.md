# EJECUCION.md — Manual de ejecución del harness

**Qué es este documento:** el contrato de ejecución del proyecto. Describe qué
hace el harness cuando se lanza, en qué orden, con qué reglas y qué deja en
disco. Es la referencia que manda sobre el comportamiento en tiempo de
ejecución; el `SPEC-generador-novelas-v3.md` explica el *porqué* de cada
decisión y `DECISIONES.md` recoge lo que se comprobó ejecutándolo.

**A quién va dirigido:** a quien ejecuta el harness, no a quien lo programa.

**Quién ejecuta el harness:** una sesión de Claude Code. No hay un programa que
se lance y funcione solo. El orquestador es la sesión: lee el estado, delega en
subagentes, recoge lo que devuelven y vuelve a escribir el estado. Los comandos
de este documento son las piezas de apoyo que esa sesión invoca entre
delegación y delegación.

---

## 0. Estado de implementación

El proyecto se construye por etapas (spec §13, una por sesión). Este documento
describe el contrato **completo**, incluido lo que todavía no existe. Esta tabla
dice qué puedes ejecutar hoy:

| Pieza | Archivo | Estado |
|---|---|---|
| Cargador de configuración | `src/config.py` | ✅ implementado |
| Biblia: contrato, hechos, timeline | `src/biblia.py` | ✅ implementado |
| Estado y reanudación | `src/estado.py` | ✅ implementado |
| Ventanas de contexto y presupuesto | `src/contexto.py` | ✅ implementado |
| Los seis subagentes y sus skills puente | `.claude/agents/`, `.claude/skills/` | ✅ implementado |
| Máquina de estados de la orquestación | `src/orquestacion.py` | ✅ implementado |
| Veredictos y puntuación | `src/puntuacion.py` | ✅ implementado |
| Comprobación de longitud del capítulo | `src/puntuacion.py` (`veredicto_longitud`) | ✅ implementado |
| Resúmenes redactados por un modelo | subagente `resumidor` | ✅ implementado |
| Ensamblador e informe | `src/ensamblador.py` | ✅ implementado |
| Registro de delegaciones y tokens | `src/delegaciones.py` | ✅ implementado |
| Marca de delegación en curso | `src/delegaciones.py` (`delegacion_en_curso`) | ✅ implementado (la sesión la escribe antes de delegar; ver sección 2.4) |
| Filtro de redacción de secretos | `src/redaccion.py` | ✅ implementado (se aplica al volcar `config-efectiva.json`) |
| Panel de control de la generación | `panel.html` | ✅ implementado, seis vistas (ver sección 10) |
| Tests de carga del panel | `tests/test_panel_carga.py`, `tests/panel_sonda.js` | ✅ implementado (requieren `node`; si no está, se saltan) |
| Servidor local del panel | `src/servidor.py` | ✅ implementado: sirve el panel, escribe `config.json`, arranca generaciones y amplía novelas (ver sección 11) |
| Narración del estado en lenguaje llano | `src/narracion.py` | ✅ implementado (ver sección 11.4) |
| Telemetría OTEL hacia Langfuse | `.claude/settings.json`, `herramientas/` | ✅ implementado (requiere una variable de entorno con la credencial; ver la sección 9) |
| Compactación de hechos | `src/biblia.py` (`compactar`) | ⬜ pendiente (hoy devuelve la biblia sin tocar) |
| Hechos y timeline extraídos de cada capítulo | biblia | ⬜ pendiente (`hechos_establecidos` no se rellena) |

Con esto se puede generar una novela completa de principio a fin. Lo que
queda pendiente no bloquea la generación, pero conviene saberlo:

- **La compactación de hechos** no hace nada todavía. Con pocos capítulos no se
  dispara; en una novela larga es lo que evita que la ventana crezca.
- **`hechos_establecidos` no se rellena.** Nadie extrae hechos de los capítulos
  escritos, así que la biblia no crece durante la generación y el bloque de
  hechos vigentes de la ventana del escritor va vacío. La continuidad se apoya
  mientras tanto en los resúmenes y en el texto del capítulo anterior.

Los comandos marcados con ⬜ en la sección 2 fallarán hasta que llegue su etapa.
Eso es lo esperado, no un error de instalación.

---

## 1. Requisitos previos

### 1.1 Lo que necesitas

| Requisito | Comprobación | Notas |
|---|---|---|
| Claude Code 2.1.271 o superior | `claude --version` | Por debajo de 2.1.271, `omitClaudeMd` se ignora en silencio y los validadores dejan de estar aislados (`DECISIONES.md`, hallazgo 3) |
| Python 3.10 o superior | `python --version` | Probado con 3.12 |
| pytest | `python -m pytest --version` | Solo para los tests |
| FastAPI, uvicorn, httpx | `python -c "import fastapi, uvicorn, httpx"` | Solo para el servidor del panel (sección 11) y sus tests. El harness genera novelas sin ellos |

Y nada más. En concreto, **no** hacen falta:

- una clave de API de ningún tipo;
- una cuenta en OpenRouter ni crédito en ningún proveedor;
- el SDK de OpenAI ni ningún cliente HTTP.

Las llamadas a modelo las hace Claude Code con tu suscripción. El harness no
tiene credenciales propias y ningún módulo de Python sale a la red.

> Si vienes de la arquitectura anterior, el archivo `.env` de la raíz ya no se
> lee. Puedes borrarlo sin consecuencias.

### 1.2 Instalación

Desde la raíz del proyecto, en PowerShell:

```powershell
python -m pip install pytest
```

Y, si vas a usar el panel con su servidor:

```powershell
python -m pip install fastapi uvicorn httpx
```

Esas tres no hacen falta para generar novelas: el harness y sus comandos
funcionan sin ellas. Si no están, los tests del servidor se saltan.

Si prefieres aislar el proyecto (recomendado, pero opcional):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pytest
```

`.venv/` ya está en `.gitignore`.

### 1.3 Los subagentes

Los seis agentes viven en `.claude/agents/` y sus skills puente en
`.claude/skills/`. No hay que instalarlos: Claude Code los descubre al abrir el
proyecto.

| Subagente | Cuándo actúa | Modelo |
|---|---|---|
| `arquitecto` | Una vez, al principio: escribe la biblia | `modelos.arquitecto` |
| `escritor` | Una vez por intento de capítulo | El escalón que toque de `escalera_escritor` |
| `continuidad`, `genero`, `estilo` | Los tres a la vez, tras cada intento | `modelos.validadores` |
| `resumidor` | Una vez por capítulo cerrado, salvo el último | `modelos.resumidor` |

Dos cosas que ahorran una tarde de depuración, ambas comprobadas y anotadas en
`DECISIONES.md`:

- **Un subagente nuevo no aparece en caliente.** Si creas o renombras un archivo
  en `.claude/agents/`, hay que reiniciar Claude Code o recargar la ventana de
  VS Code. Editar el *cuerpo* de uno que ya existía sí se recoge al vuelo. Las
  skills sí se recargan solas.
- **`claude --agent <nombre>` no precarga las skills.** Un subagente lanzado así
  responde `SIN INSTRUCCIONES`. Solo la ruta de delegación —que es la que usa el
  orquestador— le entrega su prompt de sistema. No se puede probar un subagente
  con `--agent` y concluir nada.

### 1.4 Ajustar la configuración

Todo lo ajustable vive en `config.json`. Para depurar, baja el tamaño del
trabajo antes de la primera ejecución larga:

```json
"estructura": { "num_capitulos": 2 },
"modelos":    { "intentos_por_modelo": 1 }
```

Cualquier valor se puede pisar sin tocar el archivo, con una variable de entorno
de prefijo `NOVELA_`:

```powershell
$env:NOVELA_NUM_CAPITULOS = "2"
$env:NOVELA_GENERO = "romance"
```

Los detalles de la precedencia están en la sección 3.1.

---

## 2. Comandos exactos

Todos se lanzan desde la raíz del proyecto.

### 2.1 Tests ✅

```powershell
python -m pytest
```

Variantes útiles:

```powershell
python -m pytest -v                          # nombre de cada test
python -m pytest tests/test_config.py -v     # solo los de configuración
python -m pytest -k perfil -v                # solo los que mencionan "perfil"
```

Los tests **no salen a internet y no delegan en ningún subagente**: usan
configuraciones de juguete en carpetas temporales. Deben pasar siempre.

La única excepción, y conviene saberla: `tests/test_panel_carga.py` levanta un
servidor estático de la librería estándar en `127.0.0.1` con un puerto que elige
el sistema, y ejecuta con `node` el JavaScript real de `panel.html` contra él.
Es tráfico local, contra una carpeta temporal, y es la única forma honesta de
comprobar que un capítulo que está en disco llega a la pantalla. Si no hay
`node` instalado, esos tests se saltan en vez de fallar.

### 2.2 Comprobar la configuración efectiva ✅

Carga, fusiona y valida sin gastar una sola delegación:

```powershell
python -c "from src.config import cargar_config; c = cargar_config(); print(c['novela']['genero'], c['estructura']['num_capitulos'])"
```

Si algo está mal configurado, aquí te enteras gratis.

### 2.3 Comprobar el entorno y el inventario ✅

```powershell
python -m src.orquestacion comprobar
```

Verifica lo que tiene que estar en su sitio antes de empezar: la versión de
Claude Code, la configuración válida, los seis subagentes con su
`omitClaudeMd`, las seis skills puente y los prompts de `prompts/`.

### 2.4 Arrancar y conducir una generación ✅

La generación no se lanza con un comando: se la pides a la sesión de Claude
Code, que va invocando estos comandos entre delegación y delegación.

```powershell
python -m src.orquestacion iniciar              # prepara salida/ y el estado
python -m src.orquestacion iniciar --desde-cero # ignora el estado anterior
python -m src.orquestacion estado               # qué toca hacer ahora
python -m src.orquestacion empezar-delegacion --rol escritor --modelo opus --capitulo 4 --intento 2
python -m src.orquestacion cancelar-delegacion  # borra la marca sin registrar nada
python -m src.orquestacion ventana arquitecto
python -m src.orquestacion ventana escritor --capitulo 3
python -m src.orquestacion ventana estilo --capitulo 3
python -m src.orquestacion registrar-biblia    --archivo salida/.tmp/biblia.raw
python -m src.orquestacion registrar-intento   --capitulo 3 --archivo salida/.tmp/cap-03.raw
python -m src.orquestacion registrar-veredicto --capitulo 3 --validador estilo --archivo salida/.tmp/v.raw
python -m src.orquestacion resolver            --capitulo 3
python -m src.orquestacion ventana resumidor --capitulo 3
python -m src.orquestacion registrar-resumen --capitulo 3 --archivo salida/.tmp/r.raw
python -m src.orquestacion registrar-resumen --capitulo 3 --usar-sinopsis
python -m src.orquestacion ensamblar            # manuscrito.md e informe-validacion.md
python -m src.orquestacion informe              # solo el informe, sin tocar nada más
```

**Los cuatro comandos `registrar-*` aceptan además `--tokens-in` y
`--tokens-out`.** La sesión los saca del `subagent_tokens` que le devuelve cada
delegación y los pasa tal cual:

```powershell
python -m src.orquestacion registrar-intento --capitulo 3 `
    --archivo salida/.tmp/cap-03.raw --tokens-in 41230 --tokens-out 2180
```

Son opcionales: sin ellos la delegación se anota igual y solo se pierde el
desglose de tokens. El detalle de por qué se guardan y qué se puede preguntar
después está en la sección 5.3.

Y hay un comando más, que se usa poco pero cierra el recuento:

```powershell
python -m src.orquestacion registrar-delegacion --rol escritor --capitulo 3 `
    --intento 2 --tokens-in 41230 --tokens-out 0 --nota "devolvio vacio"
```

Es para las delegaciones que **no dejaron nada que registrar**: el subagente
devolvió la respuesta vacía, se quedó sin contexto, o la sesión la abortó a
medias. Sin él, esas delegaciones serían invisibles y el freno de mano de la
regla 6 contaría de menos. No se usa cuando la respuesta llegó pero no parseaba:
en ese caso el `registrar-*` correspondiente ya la contó antes de fallar.

`informe` reescribe `informe-validacion.md` a partir de lo que hay en disco, sin
tocar el manuscrito ni borrar `.tmp/`. Sirve para sacar el informe de una novela
terminada hace semanas desde una sesión que no la generó.

#### `empezar-delegacion`: decir que algo está pasando ✅

**La sesión tiene que lanzarlo justo antes de cada delegación**, sin excepción,
igual que registra el resultado justo después. No es instrumentación de lujo:
es la única señal en disco de que la generación está viva.

```powershell
python -m src.orquestacion empezar-delegacion --rol escritor --modelo opus `
    --capitulo 4 --intento 2
```

Escribe en `estado.json` la clave `delegacion_en_curso` con el rol, el modelo,
el capítulo, el intento y la hora de inicio:

```json
"delegacion_en_curso": {
  "rol": "escritor", "modelo": "opus", "capitulo": 4,
  "intento": 2, "inicio": "2026-09-18T16:20:31Z"
}
```

La marca **desaparece sola** en cuanto se registra el resultado: los cinco
comandos `registrar-*` pasan todos por el mismo sitio y la limpian ahí, así que
no hay que acordarse de nada al terminar.

El motivo de que exista es que el resto del registro solo sabe de delegaciones
**terminadas**: una entrada aparece en `delegaciones_detalle` cuando ya hay una
respuesta que anotar. Mientras el escritor con `opus` piensa durante dos o tres
minutos no hay ni un byte en disco que lo diga, y desde fuera —desde el panel, o
desde otra ventana— una generación trabajando y una abandonada a medias se ven
**exactamente igual**.

Detalles que ahorran confusión:

- **Solo hay una marca a la vez**, y la nueva pisa a la anterior. Los tres
  validadores se lanzan en paralelo, así que marcarlos uno a uno dejaría ver
  solo el último: para ese paso se marca `--rol validadores`, que es lo que de
  verdad está ocurriendo.
- **Una marca vieja no es una generación viva.** Si la sesión muere entre el
  marcado y el registro, la marca se queda puesta. Eso no es un fallo: dice
  «esto se lanzó y no se supo más», que es información cierta y además la que
  más falta hace. El comando `estado` avisa cuando una marca lleva más de
  quince minutos.
- **`cancelar-delegacion` es solo para lo que no se llegó a lanzar.** Una
  delegación que sí se lanzó y no devolvió nada **no se cancela**: se anota con
  `registrar-delegacion`, que además la cuenta. Cancelar algo que ya se pagó
  devolvería el contador al problema que ya hubo una vez.
- **La clave es opcional hacia atrás.** Un `estado.json` de una generación
  anterior, que no la tenga, se sigue leyendo sin tocar nada.

### 2.5 Comprobar que el contador no miente ✅

```powershell
python -m src.orquestacion reconciliar
```

Reconstruye, desde los artefactos de `salida/`, cuántas delegaciones hicieron
falta **como mínimo** para producirlos, y lo compara con el contador:

| Resultado | Qué significa |
|---|---|
| contador **>** suelo | Normal. La diferencia son delegaciones que no dejaron artefacto: reintentos por formato y delegaciones abortadas. Es la señal de que se están contando |
| contador **=** suelo | Sospechoso en una novela con reescrituras: ningún reintento se anotó. Repasa si faltó algún `registrar-delegacion` |
| contador **<** suelo | Error. Se perdieron delegaciones que sí produjeron trabajo |

El suelo solo se puede calcular si los intentos siguen en `salida/.tmp/`, o sea
con `runtime.conservar_intentos` en `true`. Sin ellos el comando lo dice y no
concluye nada, en vez de dar por bueno un suelo de cero.

Cuando se sabe que faltan delegaciones pero no cuántas:

```powershell
python -m src.orquestacion marcar-contador-incompleto --motivo "..."
```

Deja escrito en `estado.json` que ese contador es un **suelo y no una medida**.
A partir de ahí, el comando `estado` y el informe de validación lo advierten
junto al número. Se marca en vez de corregir a ojo porque un número escrito a
mano deja de distinguirse después de uno medido, y entonces ya no se puede
confiar en ninguno de los dos.

`--usar-sinopsis` es la válvula de escape del resumen: no delega en nadie y cae
a la sinopsis del outline. Se usa si el resumidor devuelve algo ilegible dos
veces seguidas. La regla 1 manda: una novela no se queda parada esperando un
resumen de tres frases.

`estado` es el comando que hace que la sesión no tenga que recordar nada: dice
en qué capítulo y en qué intento va, con qué modelo, y cuál es el siguiente
paso. Se puede cerrar la ventana en mitad de una novela y retomarla desde una
sesión nueva.

---

## 3. Flujo principal

Esto es lo que hace el orquestador, en orden. Cada número corresponde a un paso
del contrato.

### 3.1 Paso 1 — Cargar la configuración

`src/config.py` construye la configuración efectiva fusionando cuatro capas, de
menor a mayor prioridad (spec §4.1). Lo posterior pisa a lo anterior:

| Capa | Origen | Ejemplo |
|---|---|---|
| 1 | Valores por defecto embebidos en `src/config.py` | `palabras_min: 1200` |
| 2 | Perfil del género activo, de la sección `perfiles` de `config.json` | terror → `palabras_min: 900` |
| 3 | El resto de `config.json` | `palabras_min: 1200` |
| 4 | Variables de entorno `NOVELA_` | `NOVELA_PALABRAS_MIN=1500` |

La capa 5 del spec (argumentos de línea de comandos) está pendiente.

Dos detalles que conviene tener presentes:

- **El perfil no gana a `config.json`.** Si `config.json` fija `palabras_min` en
  su sección `estructura`, ese valor manda sobre el del perfil del género. Para
  que mande el perfil, borra la clave de `estructura`.
- **Cambiar el género cambia el perfil.** `NOVELA_GENERO=romance` aplica también
  el perfil de romance, no el que hubiera en `config.json`.

El resultado se vuelca en `salida/config-efectiva.json` antes de la primera
delegación, para que el informe sea reproducible.

Ese volcado pasa por el **filtro de redacción** (`src/redaccion.py`). La capa 4
copia variables de entorno dentro de la configuración, así que una variable mal
elegida —`NOVELA_ALGO_TOKEN`— acabaría escrita en claro en un archivo que se
guarda, se comparte para reproducir una generación y lo lee el panel por red. El
filtro mira el **nombre** de cada clave, no su valor, y sustituye por
`[REDACTADO]` el valor de toda clave que contenga `KEY`, `TOKEN`, `SECRET`,
`AUTH` o `CREDENTIAL`, sin distinguir mayúsculas.

Dos consecuencias prácticas:

- **Solo se redacta la copia que se escribe.** El harness sigue trabajando en
  memoria con la configuración completa, así que ningún ajuste deja de aplicarse
  por estar redactado en el archivo.
- **Enmascara de más antes que de menos.** Los patrones se buscan como
  subcadena, de modo que una clave llamada `monkey` también saldría redactada.
  Es deliberado: redactar de más estropea la legibilidad de un volcado,
  redactar de menos filtra un secreto.
- **Salvo las excepciones de `CLAVES_EXENTAS`.** En este harness `token`
  significa casi siempre token de modelo, no credencial: `max_tokens_contexto`,
  `tokens`, `tokens_in`, `tokens_out` y `sin_tokens` están exentas por nombre
  exacto. Sin esa lista, `max_tokens_contexto` salía redactado del volcado, que
  es un ajuste real y hace falta para reproducir una generación. La exención es
  por nombre completo y no por patrón: `tokens_de_acceso` sigue redactándose.

### 3.2 Paso 2 — Verificar el entorno

Antes de gastar una sola delegación:

- La versión de Claude Code es 2.1.271 o superior. Por debajo, los validadores
  reciben CLAUDE.md y el aislamiento del spec §2.2 no se cumple.
- Los seis subagentes existen, llevan `omitClaudeMd: true` y declaran su skill
  puente. Los prompts de `prompts/` existen y no están vacíos.
- Los alias de modelo de `config.json` están entre `haiku`, `sonnet`, `opus` y
  `fable`. Un alias inválido falla en el momento de delegar, no al arrancar, así
  que se comprueba a propósito por adelantado.
- La configuración es válida: `num_capitulos` entero positivo, `palabras_min <
  palabras_max`, género entre `romance`, `drama` y `terror`.

Si algo falla, el harness aborta **antes** de empezar, con un mensaje en español
que dice qué arreglar. Este es el único punto del flujo donde abortar es
correcto.

### 3.3 Paso 3 — Reanudar si procede

Si existe `salida/estado.json` y `runtime.reanudar_si_existe_estado` es `true`,
la ejecución continúa desde donde se quedó en vez de empezar de cero. Los
capítulos ya aprobados no se regeneran. Ver la sección 6.

### 3.4 Paso 4 — El arquitecto

Una única delegación al subagente `arquitecto`, con el modelo de
`modelos.arquitecto`. Devuelve la biblia de la novela: premisa, conflicto
central, ambientación, 3–6 personajes con rasgos verificables, outline de
exactamente `num_capitulos` entradas y timeline.

Su salida **tiene que parsear** como el `biblia.json` del spec §7.1. Si no
parsea, se reintenta **una vez** pasándole el error de parseo. Si vuelve a
fallar, la ejecución **aborta** con un mensaje claro.

Esta es la segunda y última excepción a la regla de no abortar: sin biblia no
hay novela que escribir, así que seguir no tendría sentido.

### 3.5 Paso 5 — Bucle por capítulos

Antes de **cada una** de las delegaciones que siguen —el escritor, los
validadores, el resumidor— la sesión lanza `empezar-delegacion` (sección 2.4).
Es un paso más del bucle, no un extra: sin él no hay forma de saber desde fuera
que la generación está trabajando. Al registrar el resultado la marca se borra
sola.

Para cada capítulo del outline, en orden:

**a. Delegar en el escritor.** Su ventana de contexto la monta `src/contexto.py`
según el spec §2.2, y contiene exactamente esto:

| Entra | No entra |
|---|---|
| Biblia: personajes, ambientación, outline completo | Texto completo de capítulos anteriores a N−1 |
| Hechos vigentes (permanentes + efímeros recientes) | |
| Resúmenes de los capítulos 1…N−2 | |
| Texto completo **solo** del capítulo N−1 | |
| Problemas del intento anterior, acumulados | |

El capítulo N−1 entra entero porque el escritor necesita la voz y la transición
inmediata; los anteriores entran comprimidos. Así la ventana se mantiene
aproximadamente constante sea cual sea N, que es el criterio de aceptación más
importante del proyecto (spec §12.9).

**b. Guardar el intento y contar las palabras.** El texto va a
`salida/.tmp/cap-NN-intento-M.md` antes de validarlo. Sin esto no se podría
elegir la mejor versión al agotar la escalera.

En esta misma llamada, y en la de cada validador y cada resumen, la sesión pasa
los tokens que consumió la delegación con `--tokens-in` y `--tokens-out`. Los
saca del `subagent_tokens` que le devuelve la herramienta de delegación. Es un
hábito, no un paso aparte: si se olvida, la delegación se cuenta igual y solo se
pierde el desglose (sección 5.3).

En el mismo momento, `registrar-intento` cuenta las palabras y las compara con
`estructura.palabras_min` y `estructura.palabras_max`. Si el capítulo está fuera
de rango, el intento **nace ya con un veredicto de `FALLO`** emitido por un
cuarto auditor llamado `longitud`, que no es un subagente sino el propio
contador: no cuesta una delegación, no puede equivocarse y no hace falta
esperarlo.

Ese veredicto tiene exactamente la misma forma que los de los tres validadores y
lleva un único problema de gravedad **media**, así que:

- suma a la puntuación del intento como cualquier otro problema medio;
- **bloquea la aprobación igual que un `FALLO`**, aunque los tres validadores
  digan `PASA`;
- viaja con la reescritura por el camino normal, de modo que el escritor lee
  "el capítulo se queda corto: 944 palabras, y el mínimo configurado son 1200"
  en su lista de problemas, sin que nadie tenga que añadir texto suelto a su
  ventana.

Dentro de rango no se emite nada: el contador solo habla cuando tiene una pega.
La longitud es determinista, así que no se delega en un modelo; ver
`DECISIONES.md`, hallazgo 11.

**c. Los tres validadores, en paralelo.** Las tres delegaciones se lanzan **en un
solo mensaje**: eso, y solo eso, es lo que las hace correr a la vez. Cada
validador recibe solo lo suyo y devuelve un JSON de veredicto (spec §7.2). Uno
que falle no tumba a los otros dos: se registra como `INDETERMINADO`, que cuenta
como `FALLO`.

| Validador | Qué audita | Qué ve |
|---|---|---|
| Continuidad | Rasgos, nombres, cronología, hechos, objetos, lugares, punto de vista | Biblia completa + texto del capítulo |
| Género | Registro emocional, ritmo, elementos de la fase del arco, clichés prohibidos | Ruta de `prompts/referencias/<genero>.md`, que lee él mismo, + texto + posición en el arco |
| Estilo | Repetición léxica y sintáctica, muletillas, clichés de prosa, diálogo sin subtexto | Texto + `memoria-estilo.json` |

El validador de género es el único que lee un archivo: se le pasa la ruta de su
referencia, no su contenido, para no arrastrar 2,5 KB de convenciones por el
contexto del orquestador una vez por capítulo.

**d. Aprobar solo si los tres devuelven `PASA`.** Los tres bloquean por igual.
Un único `FALLO`, de cualquier validador y con cualquier gravedad, dispara la
reescritura. Un veredicto `PASA` obliga a `problemas: []`.

Y solo si además el capítulo está dentro del rango de palabras: el veredicto de
`longitud` del paso b, cuando existe, bloquea como un cuarto validador. Tres
`PASA` sobre un capítulo corto no aprueban nada.

**e. Si falla: acumular problemas y reintentar.** La lista de problemas se
acumula entre intentos y viaja con cada reescritura. Al agotar
`intentos_por_modelo` con un modelo, se sube al siguiente de la escalera, y los
problemas suben con él: no se empieza de cero.

Con la configuración actual (3 modelos × 2 intentos) son **6 intentos máximos**
por capítulo:

| Intentos | Modelo del escritor |
|---|---|
| 1, 2 | `haiku` |
| 3, 4 | `sonnet` |
| 5, 6 | `opus` |

El alias se pasa en cada delegación y **pisa al `model` del frontmatter** del
subagente. Por eso el escritor es un solo subagente y no tres: tres archivos en
paralelo se desincronizan y los intentos dejarían de ser comparables.

`mantener_voz_ganadora: true` hace que, una vez que un modelo resuelve un
capítulo, el siguiente empiece por ese mismo modelo en lugar de volver al
primero de la escalera. Cada escalón escribe con otra voz, y saltar de vuelta
al primero en cada capítulo se nota al leer.

**f. Agotada la escalera sin aprobación: aceptar la mejor versión.** Se calcula:

```
puntuacion = Σ (problemas de los tres validadores × peso de su gravedad)
```

Con los pesos por defecto (alta 5, media 2, baja 1), dos problemas medios
puntúan 4 y uno alto puntúa 5: gana el primero, porque **menor puntuación es
mejor**. En caso de empate gana el intento más tardío, por haber incorporado más
feedback. El capítulo se marca en el informe como `ACEPTADO_POR_PUNTUACION`.

**g. Al aprobar, actualizar la memoria larga.** Se escribe
`salida/memoria-estilo.json` con las frases que el validador de estilo manda
vigilar, y se delega en el subagente `resumidor` para obtener
`salida/resumenes/cap-NN.md` (2–3 frases).

Ese resumen es lo **único** que sabrán de este capítulo los escritores de los
capítulos N+2 en adelante, así que resume lo que el capítulo **dice**, no lo que
el outline había planeado. El resumidor no recibe el outline justamente por eso
(`DECISIONES.md`, decisión 10). El último capítulo no se resume: nadie leería
ese resumen.

Los hechos nuevos y la timeline todavía no se extraen: ver la tabla de la
sección 0. Si `hechos_establecidos` supera
`contexto.umbral_compactacion` entradas, se lanza una pasada de compactación que
funde los hechos efímeros antiguos en un resumen por capítulo. Los hechos
`permanente` no se compactan nunca.

### 3.6 Paso 6 — Ensamblar

```powershell
python -m src.orquestacion ensamblar
```

Concatena los capítulos con su portada en `salida/manuscrito.md` y genera
`salida/informe-validacion.md`. Después borra `salida/.tmp/`, salvo que
`runtime.conservar_intentos` sea `true`.

Tres cosas que el ensamblador **no** hace, y las tres a propósito:

- **No reescribe ni retoca nada.** Con el manuscrito entero delante es tentador
  arreglar aquí una transición floja. Si lo hiciera, el informe dejaría de
  describir el manuscrito: diría que el capítulo 7 se aceptó con tres problemas,
  pero el capítulo 7 del manuscrito ya no sería ese. La trazabilidad entre lo
  auditado y lo entregado es lo único que hace útil al informe.
- **No inventa los capítulos que falten.** Un capítulo que no llegó a generarse
  no aparece en el manuscrito, y el informe lo marca `SIN_GENERAR`. Un
  manuscrito con un capítulo vacío sería un manuscrito que miente.
- **No borra `.tmp/` antes de escribir el informe.** Todos los intentos y
  veredictos viven ahí; al revés, el informe saldría vacío y el dato ya no se
  podría recuperar.

---

## 4. Reglas inviolables

Seis reglas que no se negocian. Si una implementación futura las contradice, la
implementación está mal, no el documento.

**1. Ningún capítulo detiene la generación.** Un capítulo que no pasa la
validación se acepta por puntuación y se marca en el informe. Nunca se aborta por
un fallo de capítulo. Las dos únicas excepciones son previas al bucle: entorno
inválido (§3.2) y biblia que no parsea (§3.4).

**2. Un validador cuyo JSON no parsea cuenta como `FALLO`, jamás como `PASA`.**
El procedimiento defensivo es: `json.loads` directo → extraer el primer bloque
`{...}` equilibrado → repetir la delegación **una vez** incluyendo el error de
parseo → registrar `INDETERMINADO` y tratarlo como `FALLO`. Si un validador roto
aprobara por defecto, la validación sería decorativa.

**3. Los validadores no cambian de modelo durante una generación.**
`modelos.validadores` es fijo de principio a fin. Es la única palanca que queda
para que dos intentos del mismo capítulo sean comparables: la temperatura ya no
se puede fijar desde el harness (`DECISIONES.md`, decisión 9), así que la
puntuación de §3.5f ya no es una medida estable, sino una comparación entre
intentos de una misma generación. Cambiar además el modelo la dejaría sin
ningún significado.

**4. Ningún código del harness toca la red.** El único que habla con un modelo
es Claude Code, delegando en subagentes. Un módulo de Python que importe un
cliente HTTP es un error de diseño, no una optimización.

**5. El aislamiento de los validadores no se toca.** Los seis subagentes llevan
`omitClaudeMd: true` y `tools: Read` (o ninguna herramienta), y cada validador
recibe solo su ventana. Ese aislamiento es lo que hace que tres veredictos
independientes signifiquen algo: si los tres vieran el mismo material y las
reglas del proyecto, serían tres copias del mismo juicio.

**6. Contar las delegaciones y frenar antes del límite.** Antes de cada
delegación se comprueba el contador acumulado contra
`limites.delegaciones_max_totales`. Si se supera y
`abortar_si_supera_delegaciones` es `true`, se para de forma ordenada: se
escribe `estado.json`, se ensambla lo que haya y se deja constancia en el
informe. El coste en dinero ya no es medible desde aquí —las llamadas van con la
suscripción y el orquestador no recibe datos de uso—, pero un bucle de
reintentos mal cerrado sigue siendo capaz de encadenar cientos de delegaciones,
y el contrato permite hasta seis intentos por capítulo.

---

## 5. Qué aparece en `salida/`

`salida/` está en `.gitignore`: nunca se versiona.

### 5.1 Resultado final

| Archivo | Contenido |
|---|---|
| `manuscrito.md` | Portada más los capítulos concatenados en orden. El producto |
| `biblia.json` | Estado canónico final: premisa, personajes, outline, timeline, hechos |
| `informe-validacion.md` | Qué pasó en cada capítulo. Ver la sección 7 |
| `config-efectiva.json` | La configuración realmente usada tras fusionar las cuatro capas, con los valores de claves sensibles sustituidos por `[REDACTADO]` (sección 3.1) |

### 5.2 Memoria de trabajo

| Archivo | Contenido | Se actualiza |
|---|---|---|
| `capitulos/cap-NN.md` | Texto de cada capítulo generado | Al terminar cada capítulo |
| `estado.json` | Progreso: capítulo actual, intento, modelo activo, capítulos aprobados, delegaciones gastadas y el detalle de cada una (ver 5.3) | Tras cada intento y tras cada delegación |
| `resumenes/cap-NN.md` | 2–3 frases escritas por el subagente `resumidor` | Tras cerrar cada capítulo, salvo el último |
| `memoria-estilo.json` | Muletillas y frases recurrentes detectadas | Tras cada validación de estilo |
| `.tmp/cap-NN-intento-M.md` | Texto de cada intento | Cada intento |
| `.tmp/cap-NN-intento-M.json` | Veredictos y puntuación de ese intento | Cada intento |
| `.tmp/cap-NN-intento-M-<validador>.raw` | Respuesta cruda de cada validador, antes de parsearla | Cada veredicto |
| `.tmp/cap-NN-resumen.raw` | Respuesta cruda del resumidor | Cada resumen |
| `.tmp/cap-NN-ventana.json` | Tamaño en tokens y recortes de la ventana del escritor | Al pedir la ventana |

Los `.tmp` son obligatorios durante la ejecución: sin ellos no se puede elegir la
mejor versión al agotar la escalera. Se borran al ensamblar salvo que
`conservar_intentos` sea `true`, y conservarlos es lo primero que hay que hacer
cuando quieras entender por qué un capítulo salió como salió.

### 5.3 El registro de delegaciones dentro de `estado.json`

Cada delegación deja una entrada en la lista `delegaciones_detalle`:

```json
{
  "n": 17,
  "momento": "2026-09-17T18:22:04Z",
  "rol": "escritor",
  "modelo": "sonnet",
  "capitulo": 3,
  "intento": 2,
  "tokens_in": 41230,
  "tokens_out": 2180,
  "en_manuscrito": true
}
```

Junto a esa lista, y solo mientras hay algo en marcha, vive la clave
`delegacion_en_curso` (sección 2.4). La lista mira al pasado y esa clave al
presente: sin ella, `estado.json` describe con todo detalle lo que ya terminó y
no dice absolutamente nada de lo que está pasando ahora, que es justo lo que
necesita cualquiera que esté mirando la generación mientras ocurre.

Tres cosas que conviene entender de este archivo:

**Se anota toda delegación emitida, no toda delegación aprovechada.** La entrada
se escribe en cuanto la respuesta del subagente está en un archivo, y **antes**
de intentar interpretarla. Si el resumidor devuelve algo que no es JSON, esa
delegación ya se pagó y queda contada; el reintento que venga detrás se cuenta
otra vez. Hasta ahora el contador solo subía cuando el registro salía bien, así
que los reintentos por formato desaparecían: en la generación de tres capítulos
del 17 de septiembre el contador decía 59 cuando habían sido 61.

**`en_manuscrito` se decide más tarde, al resolver el capítulo.** Mientras el
capítulo está abierto vale `null`, porque todavía no se sabe qué intento gana.
Cuando `resolver` elige uno, las delegaciones de ese intento —el escritor que lo
escribió y los tres validadores que lo auditaron— pasan a `true`, y las de los
intentos descartados, a `false`. Las que no tienen número de intento (arquitecto
y resumidor) se quedan en `null`: no es que su trabajo se tirara, es que la
pregunta no les aplica.

**El registro sobrevive a `ensamblar`.** Los intentos viven en `.tmp/`, que se
borra; esto vive en `estado.json`, que no. Por eso `python -m src.orquestacion
informe` puede reconstruir el coste de una novela terminada hace semanas, desde
una sesión que no la generó. Es el mismo principio que el resto del proyecto: el
estado está en los archivos, no en la memoria de la conversación.

Los tokens son opcionales. Si la sesión no los pasó, la delegación cuenta igual
y el informe avisa de que ese total es un suelo, no una medida.

---

## 6. Reanudar una ejecución interrumpida

Si la sesión se corta (cierras VS Code, se acaba el contexto, se interrumpe la
generación), el progreso está en `salida/estado.json`, que se escribe tras cada
intento.

**Para reanudar**, con `runtime.reanudar_si_existe_estado` en `true` (el valor
por defecto), abre una sesión nueva y pídele que continúe. Lo primero que hará
es:

```powershell
python -m src.orquestacion estado
```

que dice en qué capítulo y en qué intento se quedó. Los capítulos ya aprobados
no se regeneran.

Que el estado viva en archivos y no en la conversación es justo lo que permite
esto. Una sesión de Claude Code tiene contexto finito y una novela de doce
capítulos no cabe en ella; el orquestador no recuerda nada entre pasos porque no
le hace falta.

**Para empezar de cero**, borra el estado:

```powershell
Remove-Item salida\estado.json
```

O, si quieres borrar todo el trabajo anterior:

```powershell
Remove-Item -Recurse -Force salida
```

Cuidado: eso se lleva por delante el manuscrito y la biblia.

**Un capítulo que no llegó a generarse** (por ejemplo, porque se interrumpió la
delegación) no cuenta como hecho: se queda pendiente y se reintenta en la
siguiente ejecución. Un fallo pasajero no puede dejar un agujero permanente en
el manuscrito. Lo que sí se conserva es un capítulo con texto aceptado por
puntuación.

**Advertencia:** `estado.json` y `biblia.json` van juntos. Si cambias el género,
el número de capítulos o la semilla temática en `config.json` y reanudas, estás
mezclando dos novelas distintas. Al cambiar cualquier valor de la sección
`novela` o `estructura`, borra `salida/` antes de relanzar.

---

## 7. Cómo interpretar `informe-validacion.md`

El informe tiene una entrada por capítulo. Estas son las cosas a mirar, en orden
de importancia:

**El estado del capítulo.**

| Estado | Qué significa | Qué hacer |
|---|---|---|
| `APROBADO` | Los tres validadores dijeron `PASA` | Nada |
| `ACEPTADO_POR_PUNTUACION` | Se agotaron los 6 intentos; se quedó el menos malo | Leer los problemas sin resolver y decidir si lo retocas a mano |

**El modelo que lo resolvió.** Si todos los capítulos los resuelve el tercer
escalón de la escalera, la escalera está mal ordenada o el primero es demasiado
flojo para este género: te está costando cinco intentos de más por capítulo.

**El número de intentos.** Un capítulo que necesita cuatro intentos suele
señalar un problema en la biblia, no en el escritor: un outline confuso o un
personaje con rasgos contradictorios.

**Los problemas sin resolver.** Cada uno trae gravedad, descripción, evidencia
(el fragmento concreto del texto) y corrección sugerida. La evidencia es lo que
te permite ir al manuscrito y juzgar por ti mismo si el validador tenía razón.

**La puntuación.** Menor es mejor, y solo tiene sentido comparar puntuaciones
**dentro de un mismo capítulo de una misma generación**. Dos intentos del mismo
capítulo son comparables porque los juzga el mismo modelo con la misma ventana;
dos capítulos distintos, o dos generaciones distintas, no lo son.

**Los recortes de contexto aplicados.** Si en los últimos capítulos aparecen
recortes que no aparecían en los primeros, la ventana está creciendo con N y la
compactación no está haciendo su trabajo. Es la señal de alarma más importante
del informe: significa que el proyecto no escalaría a una novela más larga.

**El coste en delegaciones y tokens.** La sección "Coste: delegaciones y tokens"
tiene dos tablas. La primera reparte el gasto por rol: si los validadores gastan
más tokens que el escritor, estás pagando la auditoría más cara que la novela, y
lo que hay que mirar es `modelos.validadores`. La segunda separa lo que acabó en
el manuscrito de lo que se gastó en intentos descartados. Un porcentaje alto de
descarte no es malo por sí solo —es lo que cuesta validar y reescribir— pero si
crece de una generación a la siguiente, la escalera está subiendo demasiado y
toca revisar `modelos.escalera_escritor` y `modelos.intentos_por_modelo`.

Si el informe dice que hay delegaciones sin cifras de tokens, los totales son un
suelo: la sesión no pasó `--tokens-in`/`--tokens-out` en alguna delegación.

**Validadores `INDETERMINADO`.** Ese validador no devolvió JSON parseable y
contó como `FALLO`. Uno suelto es ruido; varios seguidos significan que el
modelo validador no respeta el formato y hay que cambiar
`modelos.validadores`.

**El validador `longitud`.** No es un modelo: es el contador de palabras del
paso 3.5b. Si aparece en la lista de veredictos de un intento, ese intento
estaba fuera del rango configurado. Que aparezca en un capítulo suelto no dice
nada; que aparezca en la mayoría significa que el rango de `estructura` no
encaja con lo que el género y el outline dan de sí, y lo que hay que tocar es la
configuración, no el escritor. Un capítulo `ACEPTADO_POR_PUNTUACION` con un
problema de `longitud` sin resolver es un capítulo que entró corto o largo en el
manuscrito: la regla 1 manda, y es preferible a un hueco, pero conviene saberlo.

---

## 8. Errores frecuentes

### 8.1 Configuración y entorno

| Mensaje | Qué pasa | Arreglo |
|---|---|---|
| `novela.genero vale ... y solo se admiten estos tres` | Género fuera de `romance`, `drama`, `terror` | Corrige `genero` en `config.json` o `NOVELA_GENERO` |
| `estructura.num_capitulos ... tiene que ser un numero entero mayor que cero` | Valor cero, negativo o no entero | Corrige `num_capitulos` |
| `estructura.palabras_min (X) tiene que ser menor que estructura.palabras_max (Y)` | Rango invertido | Revisa `estructura` **y** el perfil del género: el rango puede venir de cualquiera de los dos |
| `modelos.X vale ... y solo se admiten estos alias` | Alias de modelo inválido | Usa `haiku`, `sonnet`, `opus` o `fable`. No se admiten identificadores completos |
| `La variable de entorno NOVELA_X no corresponde a ningun ajuste` | Nombre mal escrito | Usa el nombre exacto de una clave de `config.json`, o borra la variable |
| `La variable de entorno NOVELA_X es ambigua` | Ese nombre existe en varias secciones | Usa la ruta completa, p. ej. `NOVELA_MODELOS__ARQUITECTO` |
| `El archivo config.json no es JSON valido` | Coma de más o comillas sin cerrar | Ve a la línea que indica el mensaje |

### 8.2 Subagentes

| Síntoma | Qué pasa | Arreglo |
|---|---|---|
| `Agent type not found` | El subagente existe en disco pero la sesión no lo ha visto | Reinicia Claude Code o recarga la ventana de VS Code. Los archivos nuevos de `.claude/agents/` no se recogen en caliente |
| El subagente responde `SIN INSTRUCCIONES` | No ha recibido su prompt de sistema | Comprueba que el frontmatter declara su skill puente en `skills:` y que la skill existe. Si lo lanzaste con `claude --agent`, ese es el motivo: por esa ruta las skills no se precargan |
| El validador conoce las reglas del proyecto | `omitClaudeMd` no está haciendo efecto | Comprueba `claude --version`: por debajo de 2.1.271 ese campo se ignora sin avisar. Un campo de frontmatter desconocido no da error |
| La respuesta del validador viene envuelta en ```json | Lo habitual es que lo añada una sesión intermedia al imprimir, no el validador | No toques el prompt. El parseo defensivo ya quita las vallas |
| Un validador tarda muchísimo | Se lanzó con un modelo más caro del previsto | `modelos.validadores` debe ser fijo. Comprueba que la delegación pasa ese alias y no otro |

### 8.3 Generación

| Síntoma | Qué pasa | Arreglo |
|---|---|---|
| Un validador sale `INDETERMINADO` | Su JSON no parseó ni tras el reintento. Cuenta como `FALLO` | Si se repite, sube `modelos.validadores` a un modelo que respete mejor el formato |
| Todos los capítulos salen `ACEPTADO_POR_PUNTUACION` | Los validadores son demasiado estrictos, o el rango de palabras es incompatible con el género | Mira los problemas repetidos en el informe: suelen apuntar a una sola causa |
| Los capítulos son mucho más cortos o largos de lo pedido | El rango efectivo no es el que crees | Mira `salida/config-efectiva.json`: el perfil del género o una variable `NOVELA_` pueden estar cambiándolo |
| Todos los intentos fallan por `longitud` y ninguno se acerca al rango | El rango configurado no encaja con el género ni con el outline | Ajusta `estructura.palabras_min` y `palabras_max`, o el perfil del género. Reescribir seis veces no arregla un rango imposible |
| Reanuda y mezcla dos historias distintas | `estado.json` es de otra configuración | Borra `salida/` y relanza |
| La prosa cambia de voz entre capítulos | Distintos escalones resolvieron distintos capítulos | Es el efecto conocido de la escalera. `mantener_voz_ganadora: true` lo mitiga |
| Dos intentos del mismo capítulo puntúan raro | Sin temperatura fija, el validador no es del todo reproducible | Es esperado y está documentado en `DECISIONES.md`, decisión 9. Fíate de los problemas concretos y de su evidencia, no de diferencias de uno o dos puntos |
| `ModuleNotFoundError: No module named 'src'` | Lo lanzaste desde otra carpeta | Ejecuta siempre desde la raíz del proyecto |

### 8.4 El servidor del panel

| Síntoma | Qué pasa | Arreglo |
|---|---|---|
| El panel dice «el servidor respondió 500» y nada más | No debería pasar ya: todo error sale con cuerpo explicado. Si vuelve a verse, es un fallo del propio manejador | Mira la terminal donde lanzaste `python -m src.servidor`: la traza completa está ahí |
| La sesión responde pidiendo un dato («dime cuántos capítulos…») | El prompt le llegó incompleto | El panel lo dice con esas palabras. Si vuelve a pasar, comprueba qué recibe de verdad el subproceso: `DECISIONES.md`, hallazgo 14 |
| `FileNotFoundError: [WinError 2]` al generar o ampliar | El ejecutable se estaba buscando por su nombre suelto. En Windows `claude` es un `.CMD` y `CreateProcess` no aplica `PATHEXT` | Ya está arreglado: todo se lanza por su ruta absoluta (`DECISIONES.md`, hallazgo 13). Si reaparece con otro programa, resuélvelo con `resolver_ejecutable()` |
| `503 No encuentro el ejecutable 'claude'` | El servidor no ve Claude Code en su `PATH` | Comprueba que `claude --version` funciona **en la misma terminal** desde la que lanzas el servidor. Un `PATH` puesto en otra ventana no cuenta |
| Ampliar responde `409` con capítulos pendientes | La novela no está terminada | Termina los capítulos que faltan, o acéptalos. No se amplía a medias a propósito |
| Aparece una `salida-novela-N/` que no pedí | La copia se hace **antes** de delegar, así que un fallo posterior la deja hecha | Es un duplicado de la novela actual y se puede borrar. El panel lo dice cuando pasa |
| `python -m src.servidor` falla al importar FastAPI | No está instalado | `python -m pip install fastapi uvicorn httpx`. El harness genera novelas sin ellas; solo el panel las necesita |

---

## 9. Telemetría: ver la generación en Langfuse

### 9.1 Quién habla con Langfuse, y por qué esto no rompe ninguna regla

La regla del proyecto es que **ningún módulo de Python del harness sale a la
red**. Esta sección no la toca: quien exporta las trazas es **Claude Code**, el
CLI, usando su propia telemetría OpenTelemetry. El harness no se entera de que
existe Langfuse, y `src/` sigue sin importar un solo cliente HTTP.

Dicho de otro modo, hay dos registros y no se pisan:

| | Quién lo escribe | Dónde vive | Qué contesta |
|---|---|---|---|
| Registro local (sección 5.3) | El harness | `salida/estado.json` | Cuánto costó *esta novela*, por rol y por capítulo |
| Trazas OTEL | El CLI de Claude Code | Langfuse | Qué pasó en *cada delegación*, con su duración y su árbol de llamadas |

El primero sobrevive sin red y va en el informe. El segundo es para mirar la
ejecución por dentro cuando algo va lento o raro. Tener los dos no es
redundante: el registro local es la contabilidad, las trazas son la radiografía.

### 9.2 Montaje

**Lo que ya está hecho** vive en `.claude/settings.json`, que va a git porque no
contiene ningún secreto:

| Variable | Valor | Para qué |
|---|---|---|
| `CLAUDE_CODE_ENABLE_TELEMETRY` | `1` | Enciende la telemetría. Sin esto no se exporta nada |
| `CLAUDE_CODE_ENHANCED_TELEMETRY_BETA` | `1` | Enciende las **trazas** (spans). Sin esto solo habría métricas y eventos |
| `OTEL_TRACES_EXPORTER` | `otlp` | Exportar por OTLP, no por consola |
| `OTEL_EXPORTER_OTLP_TRACES_PROTOCOL` | `http/protobuf` | Langfuse acepta HTTP/JSON y HTTP/protobuf, pero **no gRPC** |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | `https://us.cloud.langfuse.com/api/public/otel/v1/traces` | A dónde van. Cambia `us.` por nada si tu proyecto está en la nube europea |
| `OTEL_TRACES_EXPORT_INTERVAL` | `5000` | Cada cuántos milisegundos se vacía el buffer |
| `OTEL_RESOURCE_ATTRIBUTES` | `service.name=my-novel-story` | El nombre con el que aparecen las trazas |

**Lo que tienes que poner tú** es la credencial, y no se escribe en ningún
archivo del proyecto. Una sola vez, en tu usuario de Windows:

```powershell
$par = "pk-lf-TU_CLAVE_PUBLICA:sk-lf-TU_CLAVE_SECRETA"
$base64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($par))
[Environment]::SetEnvironmentVariable("LANGFUSE_AUTH_BASIC", $base64, "User")
```

Abre una terminal nueva (las variables de usuario solo se leen al arrancar la
terminal) y, **desde la raíz del proyecto**, arma la cabecera antes de lanzar
Claude Code:

```powershell
. .\herramientas\telemetria-langfuse.ps1
claude
```

El punto delante no es decorativo: sin él, el script se ejecuta en su propio
ámbito, las variables mueren con él y tu terminal se queda igual que estaba.

Ese script hace dos cosas y ninguna más: lee `LANGFUSE_AUTH_BASIC` y compone

```
OTEL_EXPORTER_OTLP_TRACES_HEADERS = Authorization=Basic <credencial>,x-langfuse-ingestion-version=4
```

**La segunda cabecera importa más de lo que parece.** Sin
`x-langfuse-ingestion-version: 4`, la traza se guarda igualmente, pero tarda
hasta quince minutos en aparecer en los endpoints v2 que usa la interfaz. Durante
esos quince minutos parece que el montaje no funciona, y lo normal es tocar la
configuración que ya estaba bien. Con la cabecera, aparece en segundos.

### 9.3 Cómo comprobar que una traza llega

Son dos comprobaciones, y conviene hacerlas en este orden porque fallan por
motivos distintos.

**Primera: ¿funciona el camino de red?** Manda una traza de prueba sin gastar
una sola delegación:

```powershell
. .\herramientas\telemetria-langfuse.ps1
.\herramientas\comprobar-langfuse.ps1
```

Si Langfuse responde `200`/`204`, la URL y la credencial son correctas. Abre
Langfuse, ve a **Tracing → Traces** y busca el span
`novela.comprobacion-telemetria`. Debería estar ahí en segundos.

Si falla, el propio script dice qué significa cada código: `401` es credencial
mal formada o de otro proyecto, `403` es credencial válida sin permisos, `404` es
URL o región equivocadas.

**Segunda: ¿Claude Code produce trazas y las manda por ahí?** En la misma
terminal, ya con el script cargado:

```powershell
claude -p "responde solo con la palabra hola"
```

Espera unos diez segundos (el exportador vacía el buffer cada cinco) y vuelve a
mirar **Tracing → Traces** en Langfuse: debería aparecer una traza nueva con
`service.name = my-novel-story`. A partir de ahí, la siguiente generación de
novela deja una traza por delegación, con el subagente y el modelo de cada una.

Si la primera comprobación pasa y la segunda no, el problema no está en Langfuse
sino en el arranque del CLI. Lo más frecuente: lanzaste `claude` desde otra
carpeta y no se leyó `.claude/settings.json`, o no hiciste el *dot-sourcing* del
script y la cabecera de autenticación no llegó al proceso.

---

## 10. El panel de control (`panel.html`)

`panel.html` es una página de una sola pieza, sin dependencias y sin paso de
compilación, que lee lo que el harness dejó en `salida/` y lo enseña en cinco
vistas: **Recorrido**, **Arquitectura**, **Estructura**, **Tokens** y **Libro**.

Vive en la raíz del proyecto y **se versiona**. No va dentro de `salida/`, que
está en `.gitignore`: ahí se perdería en cada limpieza y no llegaría a nadie.

### 10.1 Cómo se abre

**El panel necesita un servidor.** No hay una segunda forma de usarlo.

```powershell
python -m src.servidor
```

y abre <http://127.0.0.1:8000/>. La página lee `salida/` por su cuenta con
`fetch`, al arrancar, cada pocos segundos mientras hay una generación en marcha,
y cuando se pulsa «Releer todo». Los detalles del servidor están en la
sección 11. Para pararlo, `Ctrl+C`.

Cualquier servidor estático sirve igual para el panel, porque la página solo
lee archivos:

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

**Abierta desde el disco (`file://`) no funciona, y lo dice.** El navegador
prohíbe que una página abierta así lea archivos locales. En ese caso el panel no
enseña una interfaz a medias ni un selector de archivos: se para en seco, en
grande, con el comando del servidor escrito para copiarlo. Una página que parece
rota y una página que solo necesita un servidor tienen que distinguirse a la
primera.

La página busca `salida/` primero a su lado y después un nivel más arriba, así
que funciona igual desde la raíz o desde una carpeta `docs/`.

### 10.1b Las seis vistas

| Vista | Qué cuenta |
|---|---|
| **Monitoreo** | La principal. Arriba del todo, **la frase de qué está pasando ahora**, en grande, con su cronómetro y el histórico. Después, en vivo: qué agente trabaja, con qué modelo, y el progreso. Abajo, el recorrido: todos los intentos de cada capítulo con sus veredictos, su puntuación y **los problemas sin resolver con su evidencia** |
| **Biblia** | Contra qué validan los validadores: premisa, conflicto, ambientación, personajes con sus rasgos fijos, outline cruzado con lo que de verdad pasó, y hechos establecidos |
| **Consumo** | Dónde se fue el gasto y **cuánto se tiró**. Reparto por rol, modelo y capítulo. Lo no medido se dice con palabras, nunca con un `0` |
| **Configuración** | Los ajustes de la próxima novela. Con backend, **guarda de verdad**; sin él, explica que hace falta |
| **Arquitectura** | Por qué hay tres validadores con contexto aislado. No muestra datos: es el argumento |
| **Libro** | La novela, para leerla. Serif, columna estrecha, sin instrumentación |

**Con backend y sin backend.** El panel funciona de las dos maneras y lo detecta
solo, preguntando una vez por `/api/salud`. Servido por un servidor estático
lee la novela y ya; con `python -m src.servidor` detrás aparecen las dos cosas
que **escriben**: guardar la configuración y lanzar una generación. Si no hay
backend, esos controles no se pintan y se dice por qué, en vez de enseñar
botones que van a fallar.

**El botón de generar está detrás de una confirmación escrita.** No es un
«¿seguro?»: es una lista de lo que va a pasar —incluida **la carpeta exacta** a
la que se va a copiar la novela de ahora— y hay que **teclear la palabra
`GENERAR`** para que el botón final se active. Ese botón copia carpetas y
arranca un proceso que gasta delegaciones; no puede pulsarse sin querer.

**Lo primero y más grande de la pantalla es una frase.** Arriba del todo, en
Monitoreo, hay un recuadro que dice **en lenguaje llano qué está pasando ahora
mismo**, con el tiempo que lleva en ese paso: «El escritor está redactando el
capítulo 5, intento 2 de 6, con opus». Debajo, en pequeño, el histórico de las
últimas frases, para reconstruir lo que pasó sin haber estado mirando.

El tamaño no es decoración. Esa frase llega a 84 píxeles, por encima de
cualquier otra cosa de la página —el número del progreso se queda en 68—,
porque el panel se proyecta en una sala y es lo único que se lee desde el
fondo. Si algún día se agranda otro elemento, hay que subir esta por encima o
dejará de cumplir su función.

La frase la compone el servidor (`src/narracion.py`, sección 11.4), no el
panel: si la lógica de redactarla viviera en los dos sitios, acabarían
diciendo cosas distintas. El cronómetro sí corre en local, cada segundo, entre
una consulta y la siguiente.

**El botón de detener está visible durante toda la operación**, no solo
mientras se escribe. Durante la copia y mientras trabaja el arquitecto no hay
ningún proceso de generación vivo, y aun así se puede parar: si el botón
apareciera solo con la generación en marcha, justo en la fase más larga no
habría forma de detener, que es lo contrario de lo que hace falta.

**Ampliar está al lado, con la misma protección.** El control solo aparece
cuando la novela está **completa**; si falta algún capítulo por aprobar, en su
lugar se explica cuáles y por qué no se puede ampliar todavía. La confirmación
pide teclear **`AMPLIAR`** y dice las cinco cosas que van a pasar, entre ellas
que no se regenera nada de lo aprobado y que la petición tarda un par de
minutos.

Mientras se espera, la página **no se queda quieta**: enseña un cronómetro, la
lista de lo que el servidor está haciendo, y dice con todas las letras que la
espera es a propósito, que es una delegación real a un modelo y que no se
recargue. Dos minutos de pantalla parada se leen como «se ha colgado», y eso
es un fallo de la interfaz aunque el servidor esté trabajando bien.

Al terminar, **enseña las entradas de outline nuevas** —la sinopsis y el
cambio de cada capítulo añadido— junto con qué pasó con el resumen del que era
el último capítulo. Ampliar **no genera nada**: deja el plan puesto para que se
pueda leer y decidir.

**La vista Configuración señala qué valores está pisando el archivo.** El
perfil del género **no gana** a `config.json`: si una clave está en las dos
partes, manda la del archivo (sección 3.1). Como eso es al revés de lo que
parece, la vista lo dice clave por clave, con el valor de cada lado y cómo
arreglarlo. También avisa de que guardar reformatea el archivo.

### 10.2 Qué archivos pide, y qué pasa si falta alguno

| Archivo | Si falta |
|---|---|
| `salida/estado.json` | Se denuncia en pantalla |
| `salida/config-efectiva.json` | Se denuncia en pantalla |
| `salida/biblia.json` | Se denuncia en pantalla |
| `salida/informe-validacion.md` | Se denuncia en pantalla |
| `salida/manuscrito.md` | Se denuncia en pantalla |
| `salida/capitulos/cap-NN.md` | Ausencia normal: el capítulo puede no estar generado |
| `salida/.tmp/cap-NN-intento-M.json` | Ausencia normal: `.tmp/` se borra al ensamblar salvo que `conservar_intentos` sea `true` |

Los cinco primeros son obligatorios en el sentido de que su ausencia deja vistas
cojas, y **eso se dice con la ruta exacta y el código HTTP**. La regla es la
misma que la del resto del proyecto: una vista vacía porque no hay novela y una
vista vacía porque el servidor devolvió 404 se ven igual en pantalla y son
problemas distintos, así que el panel no se calla nunca.

Un fallo de conexión (no un 404) se reintenta una vez antes de darlo por
ausente, y las peticiones opcionales van en tandas de cuatro: treinta a la vez
contra un servidor estático sencillo hacen que alguna se caiga, y una petición
caída aquí se leería como un capítulo que no existe.

**Cuántos capítulos busca.** El panel no se fía de `config-efectiva.json` para
saber cuántos hay: esa cuenta es un **suelo**, no un techo. Busca al menos hasta
el mayor de tres números —`estructura.num_capitulos`, el capítulo más alto que
`estado.json` da por aprobado o marcado, y el más alto que ya haya cargado del
manuscrito— y a partir de ahí sigue subiendo hasta encontrar **tres ausencias
seguidas**, con un tope de 99. Por eso los capítulos se piden en serie y no en
tandas: cada respuesta decide si hay que seguir buscando.

Esto arregla un fallo real: antes el número salía solo de
`config-efectiva.json`, así que un capítulo que estuviera en disco pero fuera de
esa cuenta no se llegaba a pedir. Y un archivo que no se pide no da 404: no da
nada, así que la vista Libro salía vacía sin que el panel denunciara nada. Los
tests de `tests/test_panel_carga.py` ejecutan el JavaScript real de la página
contra un servidor de juguete y fallan si un capítulo que está en disco no llega
a la pantalla. Necesitan `node`; sin él se saltan.

### 10.3 La tabla de aprobación por validador

La vista **Recorrido** abre con una tabla que dice, de cada validador, cuántos
intentos aprobó sobre los que llegó a juzgar, y en cuántos fue **el único que
dijo `FALLO`**.

Los denominadores no son todos iguales a propósito: el auditor de `longitud`
solo emite veredicto cuando el capítulo se sale del rango (§3.5b), así que juzga
menos intentos que los tres validadores y medirlo contra el total sería mentir.

La columna «único que falló» es la que convierte la tasa en una consecuencia.
Como los tres validadores bloquean por igual (§3.5d), una reescritura que pidió
uno solo la pagó la novela entera. En la generación de tres capítulos del 17 de
septiembre, sobre 14 intentos: continuidad aprobó 11, género 13 y **estilo 2**, y
estilo fue el único que falló en **7** de esos 14. Ese contraste no se ve mirando
los capítulos de uno en uno, que es exactamente por lo que la tabla existe.

---

## 11. El servidor local (`src/servidor.py`)

### 11.1 Qué es, y qué no es


Un servidor HTTP **para la máquina de quien lo lanza y para nadie más**. Sirve
`panel.html` y los archivos de `salida/`. Está construido con FastAPI.

Lo que **no** es, y conviene tenerlo claro antes de leer el resto:

- **No llama a ningún modelo.** Hoy no lanza ningún proceso.
- **No sale a la red.** Escucha; no pide nada a nadie. La regla del proyecto de
  que ningún módulo de Python salga a la red sigue intacta.
- **No sirve el proyecto entero.** Solo el panel y `salida/`.

```powershell
python -m src.servidor                 # http://127.0.0.1:8000/
python -m src.servidor --puerto 8765   # otro puerto
```

### 11.2 Los endpoints de hoy


| Método y ruta | Qué hace |
|---|---|
| `GET /` y `GET /panel.html` | El panel |
| `GET /salida/<lo que sea>` | Un archivo de `salida/`, incluido lo de `.tmp/` |
| `GET /api/salud` | Dónde mira el servidor, y **qué puede escribir** |
| `GET /api/config` | La configuración, en sus dos formas, y si ahora mismo se puede tocar |
| `PUT /api/config` | Aplica cambios sobre `config.json` |
| `POST /api/ampliar` | Añade capítulos a una novela terminada **y arranca su escritura**, sin regenerar nada |
| `POST /api/generar` | Copia la novela actual y arranca una generación en segundo plano |
| `GET /api/generacion` | En qué fase va, **la frase de lo que está pasando**, el histórico, el outline nuevo y las últimas líneas del log |
| `POST /api/detener` | Para la generación en marcha |

Todas las respuestas de archivo van con `Cache-Control: no-store`: el panel
repregunta por `estado.json` cada pocos segundos, y una respuesta cacheada sería
seguimiento en vivo de datos viejos. Los archivos de texto van con el charset
declarado, para que un manuscrito con acentos no llegue roto.

`GET /api/salud` devuelve dónde está la raíz, dónde está `salida/`, si existen,
en qué dirección escucha y **la lista de lo que el servidor puede escribir**.
Hoy vale `["config.json"]`. Esa lista es una declaración, no un adorno: crece
solo cuando el servidor gana permiso para tocar algo nuevo, y hay un test que
hay que cambiar a mano cuando eso pasa.

### 11.3 Cómo se arranca Claude Code, y por qué así


Todo lo que este servidor lanza pasa por `resolver_ejecutable()`, que devuelve
la **ruta absoluta** del programa. Nunca se pasa el nombre suelto, y no es una
manía:

En Windows, `claude` instalado con npm **no es un `.exe`**: es un `claude.CMD`.
`shutil.which()` lo encuentra porque aplica `PATHEXT`, pero `CreateProcess`
—que es lo que hay debajo de `subprocess` cuando no se usa shell— **no lo
aplica**: busca el nombre literal y solo ejecuta binarios. El resultado es un
`FileNotFoundError: [WinError 2]` en un comando que funciona perfectamente en
la terminal. El detalle completo está en `DECISIONES.md`, hallazgo 13.

Sigue sin usarse shell y los argumentos siguen yendo como lista: lo único que
cambia es que `argv[0]` es una ruta y no un nombre.

**Y el prompt no va como argumento: va por la entrada estándar.** Es el mismo
`.CMD` mordiendo por segunda vez. Al pasar por `cmd.exe`, el analizador de
línea de comandos **termina el comando en el primer salto de línea**: un prompt
de 2303 caracteres y 46 líneas llegaba al otro lado convertido en 60
caracteres, su primera línea. La sesión recibía un encargo truncado, no podía
saberlo, y pedía el dato que le faltaba; desde fuera parecía que el modelo no
sabía devolver JSON (`DECISIONES.md`, hallazgo 14).

`claude -p` sin argumento lee de stdin. Por ahí llega el texto entero y
desaparece además el límite de longitud de la línea de comandos. Los dos
prompts van así, también el de generación, que hoy es de una sola línea y se
salvaba por casualidad.

### 11.4 Qué está pasando ahora: la frase, no los campos

`GET /api/generacion` devuelve, además del estado del proceso, **una frase en
lenguaje llano** con lo que está ocurriendo. No es un adorno: el panel tenía
todos los datos y aun así no se entendía, porque enseñaba campos sueltos
—`rol: escritor`, `capitulo: 5`, `intento: 2`— y había que recomponer la frase
mentalmente. Peor: durante los pasos que **no** son una delegación, como
copiar archivos o esperar al arquitecto, `estado.json` no cambia, así que la
pantalla decía «sin actividad» mientras el servidor trabajaba.

| Campo | Qué es |
|---|---|
| `fase` | En qué paso va: `copiando`, `arquitecto`, `validando`, `lanzando`, `generando`, y los finales |
| `frase` | Una sola frase, legible, de lo que pasa **ahora** |
| `segundos_en_fase` y `duracion_en_fase` | Cuánto lleva en este paso |
| `aviso_lentitud` | Solo si el paso se alarga más de lo normal |
| `historial` | Las últimas frases, de la más reciente a la más antigua |
| `outline_nuevo` | El plan de los capítulos añadidos, en cuanto existe |

Las frases las construye `src/narracion.py`, que no toca disco ni red: recibe
diccionarios y devuelve texto. El tono es sujeto, verbo y lo que hace, sin
jerga del sistema:

```
Copiando la novela actual a salida-novela-2, antes de tocar nada
El arquitecto está diseñando qué pasa en los capítulos 5 y 6
El escritor está redactando el capítulo 5, intento 2 de 6, con opus
Los tres validadores están auditando el capítulo 5 a la vez
El capítulo 5 no pasó: estilo encontró 3 problemas. Reescribiendo
Capítulo 5 aprobado limpio. Pasando al 6
```

Tres detalles que costaron su test y conviene conocer:

- **Cuando no hay nada en marcha se dice igual de claro**, y con lo último que
  pasó: «No hay nada en marcha. La última generación se cayó sin terminar. Lo
  último que pasó: …». Un «sin actividad» a secas no distingue una novela
  terminada de una que murió hace una hora.
- **Si un paso se alarga, se menciona.** Pasado lo normal para ese paso —del
  orden de tres minutos para el arquitecto o cinco para el escritor— la
  respuesta trae un aviso que dice cuánto lleva, que todavía puede terminar
  bien y que se puede detener. Callarse deja a quien mira adivinando si se
  colgó.
- **La primera lectura no cuenta eventos**, solo toma la foto del estado. Si no,
  al abrir el panel sobre una novela terminada hace días el histórico se
  llenaría de «Capítulo 1 aprobado limpio», «Capítulo 2 aprobado limpio»…

### 11.5 Los errores se explican, siempre


Ningún fallo de este servidor sale sin cuerpo. La razón es sencilla: el panel
solo puede enseñar lo que el servidor le mande, y un `500` pelado deja la
explicación en la terminal, que es justo donde no está mirando quien usa la
página.

| Qué pasó | Código | Qué trae la respuesta |
|---|---|---|
| Lo que llega no vale (claves, tipos, biblia inválida) | `400` | `mensaje` y la lista entera de `errores` |
| Hay algo en marcha, o la novela está a medias | `409` | `mensaje`, y `bloqueo` o `capitulos_pendientes` |
| La sesión de Claude Code devolvió algo que no sirve | `502` | `codigo_salida`, **lo que devolvió** y **su `stderr`** |
| La sesión **pidió un dato** en vez de trabajar | `502` | `pidio_datos: true` y lo que preguntó, en primer plano. Significa que el encargo le llegó incompleto |
| No está el ejecutable | `503` | `mensaje` y una `pista` con qué comprobar |
| El arquitecto no contestó a tiempo | `504` | `mensaje` con el límite que se agotó |
| Cualquier cosa imprevista | `500` | El tipo y el mensaje de la excepción, y dónde está la traza |

Las tres cosas que siempre se dicen cuando algo falla: **qué falló**, **si se
tocó algo** y **dónde mirar**. Cuando el fallo viene de la sesión de Claude
Code, lo que dijo la sesión **es** el diagnóstico y se enseña tal cual, sin
resumir.

### 11.6 Las cuatro reglas de seguridad


Este es el primer componente del proyecto que abre un puerto, y va a crecer
hasta escribir `config.json` y arrancar procesos. Las reglas no son opcionales:

1. **Escucha solo en `127.0.0.1`.** La dirección es una constante del código, no
   un parámetro de la línea de comandos. Un servidor que va a escribir
   configuración y arrancar procesos no puede acabar expuesto a la red local
   por un descuido al lanzarlo. No hay bandera para cambiarlo.
2. **Lista blanca, no lista negra.** Solo se sirven `panel.html` y lo que cuelga
   de `salida/`. Cualquier otra cosa del proyecto es `404` aunque exista. Esto
   importa de verdad: en la raíz hay un `.env` con una clave de la arquitectura
   anterior, y un servidor que sirviera el directorio entero la dejaría a un
   `GET` de distancia.
3. **Ninguna ruta sale del proyecto.** La ruta pedida se resuelve —lo que
   deshace `..` y sigue los enlaces simbólicos— y después se comprueba que cae
   dentro de `salida/`. El orden importa: comprobar la cadena antes de
   resolverla no sirve de nada.
4. **Lo que no se sirve devuelve `404`, no `403`.** Un `403` confirmaría que el
   archivo existe, y eso ya es información que nadie tiene por qué sacar de
   aquí.

Si `runtime.directorio_salida` apuntara fuera del proyecto, el servidor **no
arranca** y lo dice: servir por HTTP una carpeta cualquiera del disco es
exactamente lo que no puede pasar.

Los tests de `tests/test_servidor.py` prueban sobre todo lo que **no** se debe
servir: el `.env`, el código, la documentación, y los intentos de salirse con
`..`, con la ruta codificada en porcentajes, con rutas absolutas y con un enlace
simbólico que apunte fuera.

---

### 11.7 Leer y escribir la configuración


**`GET /api/config`** devuelve cuatro cosas:

| Campo | Qué es |
|---|---|
| `archivo` | El contenido literal de `config.json`. **Esto es lo que se edita** |
| `efectiva` | La que el harness usará de verdad, tras aplicar valores por defecto, perfil de género y variables `NOVELA_` |
| `editable` | `false` si hay una generación en marcha |
| `errores` | Si `config.json` no es válido, aquí está el porqué |

Se devuelven las dos formas porque responden a preguntas distintas. Ver solo una
confunde: se edita `palabras_min` en el archivo, el perfil del género lo pisa, y
la generación usa otro número sin que nada lo explique (sección 3.1).

Las dos salen **redactadas** por `src/redaccion.py`, igual que el volcado de la
configuración efectiva.

**`PUT /api/config`** aplica cambios. Lo más importante de este endpoint es lo
que **no** hace: el cuerpo de la petición **no es la configuración nueva**. Es
una lista de ajustes a cambiar, y todo lo que no venga se queda como está.

```powershell
# cambia dos ajustes y no toca nada más
{"estructura": {"num_capitulos": 5}, "novela": {"genero": "romance"}}
```

Para escribir hay que pasar **cuatro puertas, en este orden**. Si falla
cualquiera, la respuesta dice por qué y **`config.json` queda intacto**:

1. **No hay una generación en marcha.** Se mira `delegacion_en_curso` de
   `estado.json` (sección 2.4). Si la hay, la respuesta es `409` y no se toca
   nada: cambiar la configuración a media novela dejaría unos capítulos escritos
   con unos ajustes y el resto con otros.
2. **Las claves existen y los tipos encajan.** Una clave que no esté ya en
   `config.json` es un error, no un añadido; un texto donde había un número es
   un error. Las claves que empiezan por guion bajo (`_meta`, `_comentario`) son
   documentación del archivo y no se editan desde aquí. Un valor que llegue como
   `[REDACTADO]` se rechaza, para que no se guarde esa palabra como si fuera el
   valor real.
3. **La configuración resultante entera pasa por `src/config.py`.** No el cambio
   suelto: el archivo completo, cargado como se cargaría de verdad. Así un
   `num_capitulos: 0` o un rango de palabras imposible se rechazan con el mismo
   mensaje que daría el harness al arrancar.
4. **Se escribe de forma atómica.** Primero a un temporal en la misma carpeta y
   después renombrado, igual que `estado.json`: un `config.json` a medias dejaría
   el harness sin arrancar.

Los errores vienen **todos juntos**, no de uno en uno, que es el mismo criterio
que usa el validador de la biblia. La respuesta de éxito lista los cambios con
su valor anterior y el nuevo, y si no había nada que cambiar lo dice y no
reescribe el archivo.

> **Consecuencia que conviene conocer:** al escribir, `config.json` se reformatea
> con sangría de dos espacios. El contenido y el orden de las claves se conservan
> enteros, incluidos los `_comentario`, pero las líneas que estuvieran compactadas
> a mano se expanden. Si el formato del archivo te importa, edítalo a mano en
> lugar de por el panel.

### 11.8 Generar desde el panel


**`POST /api/generar`** hace tres cosas, en este orden, y si falla cualquiera
no se pasa a la siguiente:

1. **Comprueba que existe el ejecutable `claude`.** Si no está en el `PATH`,
   responde `503` y no toca nada. Se mira antes de copiar para no dejar una
   carpeta de copia suelta por una generación que no iba a arrancar.
2. **Copia la novela actual a `salida-novela-N/`**, con el primer `N` libre. Si
   hay algo que copiar y la copia falla, **no se genera**: generar encima de una
   novela terminada la pierde para siempre, y eso no se arregla después. La
   respuesta dice a qué carpeta se copió.
3. **Arranca `claude -p` en segundo plano** y **vuelve enseguida**. Una
   generación son minutos; dejar la petición HTTP esperando todo ese rato no
   aporta nada, porque el seguimiento en vivo ya se hace repreguntando por
   `estado.json`.

El endpoint **no recibe nada**. El comando y el prompt son constantes de
`src/servidor.py`: desde el navegador solo se puede decir «empieza» y «para»,
nunca «empieza con esto». Se lanza sin shell y con la lista de argumentos
separada, así que no hay nada que pueda interpretarse.

La salida del proceso, la suya y la de sus errores, va a
`salida/.log-generacion.txt`, en modo añadir. Ese log es el único rastro que
queda si algo se tuerce, así que no se trunca nunca.

**`GET /api/generacion`** devuelve si hay algo vivo, desde cuándo, el código de
salida si ya terminó, a qué carpeta se copió la novela anterior y las últimas
líneas del log (40 por defecto, `?lineas=N` para cambiarlo).

#### Qué pasa cuando el proceso se muere

Es el caso que más cuidado necesita, porque una generación que muere en
silencio deja el panel mintiendo. Siempre que el proceso termina —bien, mal o
detenido a mano— pasan tres cosas:

1. **Se escribe en el log cómo terminó**, con la hora y el código de salida.
   Una caída se marca como `CAIDA` y explica que lo que haya en `salida/` es lo
   que quedó a medias.
2. **Se limpia `delegacion_en_curso` del estado.** Si el proceso murió a media
   delegación, esa marca se queda puesta, y sin limpiarla el panel enseñaría
   «escritor, trabajando» para siempre y la configuración quedaría bloqueada
   sin que nada estuviera generando.
3. **Se anota con qué murió**, para poder contarlo: «murió con el escritor del
   capítulo 2 abierto» es mucho más útil que «murió».

Esto lo hace un vigilante que espera al proceso, y además se comprueba cada vez
que alguien pregunta por el estado. Con las dos vías, una generación no puede
quedar marcada como viva cuando ya no lo está.

**Si reinicias el servidor con una generación en marcha**, el servidor nuevo no
es dueño de ese proceso y **lo dice**: responde `desconocida` en vez de
adivinar. Comprobar si un PID ajeno sigue vivo de forma portable no es fiable,
y en Windows la forma obvia de intentarlo mata el proceso.

**`POST /api/detener`** termina el proceso, le da diez segundos y, si no se va,
lo mata. Después hace lo mismo del cierre: log, limpieza de la marca y
anotación.

### 11.9 Ampliar una novela terminada


Llevar una novela de N capítulos a N+M **sin regenerar nada de lo aprobado**.

```
POST /api/ampliar      {"capitulos": 2}
```

#### El cuello de botella que esto resuelve

`src/biblia.py` exige que el outline tenga **exactamente** `num_capitulos`
entradas. Subir ese número a mano no amplía nada: deja la biblia inválida y el
harness deja de arrancar. Ampliar de verdad son **dos cambios que tienen que
ocurrir juntos o ninguno**: el outline crece y el número sube. Todo el endpoint
está construido alrededor de esa atomicidad.

**Ampliar y generar son una sola operación.** Al confirmar, el servidor hace
todo seguido —copia, pide el outline, lo valida, lo guarda, sube
`num_capitulos` y **arranca la escritura**— sin pedir confirmación en medio.
La petición **no espera**: devuelve en cuanto la operación arranca y el
seguimiento va por `GET /api/generacion`, que es lo que el panel ya consulta.

Juntarlas quita un punto de control humano, así que hay tres cosas que lo
sustituyen y que no se pueden perder:

- **El outline nuevo se puede leer en cuanto existe**, antes de que haya un
  solo capítulo escrito. Aparece en `outline_nuevo`.
- **Se puede detener en cualquier fase**, incluida la del arquitecto. Parar al
  leer el plan cuesta las delegaciones del arquitecto, no las de la novela
  entera.
- **Si el arquitecto falla o la biblia no valida, no se genera nada** y la
  novela queda como estaba. Eso ya no viaja en la respuesta HTTP —que solo
  dice «arrancada»— sino en `ampliacion.error`.

`POST /api/generar` se mantiene aparte, para regenerar sin ampliar.

#### Los siete pasos, y dónde se para

1. **No hay ninguna generación en marcha.** Ampliar con una en curso dejaría el
   outline creciendo debajo de un escritor que ya está trabajando. → `409`
2. **La novela está completa.** Si queda algún capítulo por aprobar, se
   rechaza y se dice cuáles: ampliar a medias mezcla terminar lo que falta con
   añadir lo que no estaba. → `409`
3. **Se copia la novela a `salida-novela-N/`**, igual que al generar.
4. **El arquitecto escribe las entradas nuevas.** Se lanza una sesión de Claude
   Code que delega en el subagente `arquitecto`. **Las entradas no las escribe
   el servidor**: un outline salido de un `str.format` sería texto de novela
   escrito por código, que es justo lo que este proyecto evita. La llamada es
   **síncrona** —hay que poder leer lo que propone antes de decidir— con un
   límite de 15 minutos.
5. **Se valida entero antes de escribir nada**, y con dos exigencias:
   - la biblia ampliada cumple el contrato 7.1 con el número nuevo;
   - y **solo añade**. Si el arquitecto reescribiera la sinopsis de un capítulo
     ya escrito, o cambiara los personajes o la premisa, se rechaza. Ese
     capítulo dejaría de corresponderse con su plan y el informe de validación
     pasaría a mentir sobre una novela que nadie ha vuelto a tocar. → `400`
6. **Se escribe la biblia y se sube `num_capitulos`.** Si la segunda escritura
   falla, **la biblia se restaura**: una biblia de N+M entradas con un config
   que dice N deja el harness sin arrancar.
7. **El estado no se toca.** Los capítulos aprobados y marcados siguen donde
   estaban, así que los nuevos salen como pendientes por sí solos y
   `python -m src.orquestacion estado` ya apunta al primero.

La respuesta trae **las entradas de outline nuevas**, para leerlas antes de
lanzar la generación.

#### Dos detalles que ya habían mordido

**El capítulo que era el último dejó de serlo.** El resumidor se salta el
último capítulo de una novela, porque nadie leería ese resumen. Al ampliar sí
se lee: es lo único que el escritor del capítulo N+2 sabrá de él. El endpoint
lo comprueba y lo genera si falta, por tres caminos, y **dice cuál usó**: ya
existía, lo escribió el resumidor en esta ampliación, o se cayó a la sinopsis
del outline (la misma válvula que `registrar-resumen --usar-sinopsis`).

**El arco del género se reabre.** La novela estaba cerrada: el último capítulo
resolvía el conflicto central. El prompt se lo dice al arquitecto con todas las
letras —que no repita ese clímax, que abra algo que nazca de las consecuencias
de ese final y lo cierre, y que la fase del arco vuelve a empezar—, porque sin
esa advertencia lo natural es que proponga otro final.

#### El único dato del navegador que llega a un prompt

Es `capitulos`, y es un **entero** entre 1 y 20, validado como número **antes**
de tocar la plantilla. No hay ninguna cadena del cliente que llegue al prompt:
interpolar un entero comprobado en un texto fijo no puede inyectar nada. Todo
lo demás del prompt es constante del código, como en `generar`.

## 12. Documentos relacionados

| Documento | Para qué |
|---|---|
| `SPEC-generador-novelas-v3.md` | Especificación completa y el porqué de cada decisión |
| `DECISIONES.md` | Lo que se comprobó ejecutándolo, y por qué la arquitectura es como es |
| `CLAUDE.md` | Reglas del proyecto para trabajar en el código |
| `config.json` | Toda la configuración ajustable |
| `.claude/settings.json` | Telemetría OTEL de Claude Code. Sin secretos: la credencial va en una variable de entorno |
| `herramientas/telemetria-langfuse.ps1` | Arma la cabecera de autenticación de Langfuse a partir de esa variable |
| `herramientas/comprobar-langfuse.ps1` | Manda una traza de prueba y dice si Langfuse la acepta |
| `Harness_novela.drawio.png` | Diagrama del flujo |
| `ADENDA-openrouter-vscode.md` | **Deprecada.** Arquitectura anterior sobre OpenRouter. Historia, no contrato |
| `archivo/NOTA.md` | Qué código de la arquitectura anterior se conserva y por qué |
| `panel.html` | Panel de control de la generación. Sección 10 |
| `README.md` | Presentación del proyecto y las dos formas de abrir el panel |
