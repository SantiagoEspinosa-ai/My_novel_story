# EJECUCION.md — Manual de ejecución del harness

**Qué es este documento:** el contrato de ejecución del proyecto. Describe qué
hace el harness cuando se lanza, en qué orden, con qué reglas y qué deja en
disco. Es la referencia que manda sobre el comportamiento en tiempo de
ejecución; el `SPEC-generador-novelas-v3.md` explica el *porqué* de cada
decisión y la `ADENDA-openrouter-vscode.md` la capa de modelos.

**A quién va dirigido:** a quien ejecuta el harness, no a quien lo programa.

---

## 0. Estado de implementación

El proyecto se construye por etapas (spec §13, una por sesión). Este documento
describe el contrato **completo**, incluido lo que todavía no existe. Esta tabla
dice qué puedes ejecutar hoy:

| Pieza | Archivo | Estado |
|---|---|---|
| Cargador de configuración | `src/config.py` | ✅ implementado |
| Tests de configuración | `tests/test_config.py` | ✅ implementado |
| Contratos de datos, biblia, estado | `src/biblia.py`, `src/estado.py` | ⬜ pendiente (etapa 2) |
| Cliente de modelos y arquitecto | `src/agentes.py` | ⬜ pendiente (etapa 3) |
| Escritor y pipeline mínimo | `src/orquestador.py` | ⬜ pendiente (etapa 4) |
| Presupuesto de contexto | `src/contexto.py` | ⬜ pendiente (etapa 5) |
| Validadores y bucle de reintentos | `src/orquestador.py` | ⬜ pendiente (etapas 6–8) |
| Puntuación y escalera | `src/puntuacion.py` | ⬜ pendiente (etapa 7) |
| Ensamblador e informe | `src/ensamblador.py` | ⬜ pendiente (etapa 10) |

Los comandos marcados con ⬜ en la sección 2 fallarán hasta que llegue su etapa.
Eso es lo esperado, no un error de instalación.

---

## 1. Requisitos previos

### 1.1 Lo que necesitas

| Requisito | Comprobación | Notas |
|---|---|---|
| Python 3.10 o superior | `python --version` | Probado con 3.12 |
| pytest | `python -m pytest --version` | Solo para los tests |
| SDK de OpenAI | `python -c "import openai"` | Cliente de OpenRouter (adenda §3.2). Hace falta a partir de la etapa 3 |
| Cuenta de OpenRouter con crédito | panel de openrouter.ai | Con un límite de gasto puesto |
| Clave `OPENROUTER_API_KEY` | ver §1.3 | Nunca en el código ni en `config.json` |

### 1.2 Instalación

Desde la raíz del proyecto, en PowerShell:

```powershell
python -m pip install pytest openai
```

Si prefieres aislar el proyecto (recomendado, pero opcional):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pytest openai
```

`.venv/` ya está en `.gitignore`.

### 1.3 La clave de API

La clave de OpenRouter se lee **exclusivamente** de la variable de entorno
`OPENROUTER_API_KEY`. No va en `config.json`, no va en el código, no se
imprime en ningún log.

Para una sola sesión de terminal:

```powershell
$env:OPENROUTER_API_KEY = "tu_clave_de_openrouter"
```

Para dejarla puesta de forma permanente en tu usuario de Windows:

```powershell
[Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "tu_clave", "User")
```

Después de esto hay que **abrir una terminal nueva**: las ya abiertas conservan
el entorno antiguo.

El archivo `.env` de la raíz está en `.gitignore` y hoy **no lo lee nadie**: es
una nota para ti, no una fuente de configuración. Si en alguna etapa se añade un
lector de `.env`, se documentará aquí.

Comprobar que la variable existe, sin imprimir su valor:

```powershell
if ($env:OPENROUTER_API_KEY) { "definida" } else { "NO definida" }
```

### 1.4 Ajustar la configuración

Todo lo ajustable vive en `config.json`. Para depurar, baja el coste antes de la
primera ejecución larga (adenda §9):

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

Los tests **no tocan la red ni tu clave de API**: usan configuraciones de
juguete en carpetas temporales y una clave falsa. Deben pasar siempre, tengas o
no crédito en OpenRouter.

### 2.2 Comprobar la configuración efectiva ✅

Carga, fusiona, valida y vuelca `salida/config-efectiva.json` sin gastar una
sola llamada a modelo:

```powershell
python -c "from src.config import cargar_config; c = cargar_config(); print(c['novela']['genero'], c['estructura']['num_capitulos'])"
```

Si algo está mal configurado, aquí te enteras gratis.

### 2.3 Prueba de conexión ⬜ (etapa 3)

```powershell
python -m src.agentes --probar-conexion
```

Hace lo mínimo para confirmar que la capa de modelos funciona:

1. Comprueba que `OPENROUTER_API_KEY` existe.
2. Pide a OpenRouter el catálogo de modelos y verifica que **todos** los slugs
   de `config.json` (escalera del escritor, arquitecto y validadores) están en
   él.
3. Lanza una llamada mínima al modelo más barato de la escalera y enseña la
   respuesta.

Coste: céntimos. Merece la pena antes de cada ejecución larga.

### 2.4 Ejecución completa ⬜ (etapa 4 en adelante)

```powershell
python -m src.orquestador
```

Genera la novela entera según `config.json`. Es el comando principal.

Opciones previstas (capa 5 de la precedencia, pendiente):

```powershell
python -m src.orquestador --config otra-config.json
python -m src.orquestador --desde-cero          # ignora estado.json
python -m src.orquestador --solo-capitulo 7     # regenera un capítulo suelto
```

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
llamada a un modelo, para que el informe sea reproducible.

### 3.2 Paso 2 — Verificar el entorno

Antes de gastar una sola llamada:

- `OPENROUTER_API_KEY` existe y no está vacía. Solo se comprueba su existencia:
  el valor no se lee, ni se guarda, ni se imprime.
- Los slugs de modelo de `config.json` existen en el catálogo de OpenRouter. Un
  slug inválido falla en tiempo de ejecución, no al arrancar, así que se
  comprueba a propósito por adelantado (adenda §3.1).
- La configuración es válida: `num_capitulos` entero positivo, `palabras_min <
  palabras_max`, género entre `romance`, `drama` y `terror`.

Si algo falla, el harness aborta **antes** de gastar dinero, con un mensaje en
español que dice qué arreglar. Este es el único punto del flujo donde abortar es
correcto.

### 3.3 Paso 3 — Reanudar si procede

Si existe `salida/estado.json` y `runtime.reanudar_si_existe_estado` es `true`,
la ejecución continúa desde donde se quedó en vez de empezar de cero. Los
capítulos ya aprobados no se regeneran. Ver la sección 6.

### 3.4 Paso 4 — El arquitecto

Una única llamada al modelo del arquitecto (temperatura 0.9: aquí quieres
variedad). Devuelve la biblia de la novela: premisa, conflicto central,
ambientación, 3–6 personajes con rasgos verificables, outline de exactamente
`num_capitulos` entradas y timeline.

Su salida **tiene que parsear** como el `biblia.json` del spec §7.1. Si no
parsea, se reintenta **una vez** pasándole el error de parseo. Si vuelve a
fallar, la ejecución **aborta** con un mensaje claro.

Esta es la segunda y última excepción a la regla de no abortar: sin biblia no
hay novela que escribir, así que seguir no tendría sentido.

### 3.5 Paso 5 — Bucle por capítulos

Para cada capítulo del outline, en orden:

**a. Llamar al escritor.** Su ventana de contexto la monta `src/contexto.py`
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

**b. Guardar el intento.** El texto va a `salida/.tmp/cap-NN-intento-M.md` antes
de validarlo. Sin esto no se podría elegir la mejor versión al agotar la
escalera.

**c. Los tres validadores, en paralelo.** `asyncio.gather(...,
return_exceptions=True)` sobre continuidad, género y estilo (adenda §5). Cada
uno recibe solo lo suyo y devuelve un JSON de veredicto (spec §7.2). Una
excepción en uno no tumba a los otros dos: se convierte en un veredicto
`INDETERMINADO`, que cuenta como `FALLO`.

| Validador | Qué audita | Qué ve |
|---|---|---|
| Continuidad | Rasgos, nombres, cronología, hechos, objetos, lugares, punto de vista | Biblia completa + texto del capítulo |
| Género | Registro emocional, ritmo, elementos de la fase del arco, clichés prohibidos | `prompts/referencias/<genero>.md` + texto + posición en el arco |
| Estilo | Repetición léxica y sintáctica, muletillas, clichés de prosa, diálogo sin subtexto | Texto + `memoria-estilo.json` |

**d. Aprobar solo si los tres devuelven `PASA`.** Los tres bloquean por igual.
Un único `FALLO`, de cualquier validador y con cualquier gravedad, dispara la
reescritura. Un veredicto `PASA` obliga a `problemas: []`.

**e. Si falla: acumular problemas y reintentar.** La lista de problemas se
acumula entre intentos y viaja con cada reescritura. Al agotar
`intentos_por_modelo` con un modelo, se sube al siguiente de la escalera, y los
problemas suben con él: no se empieza de cero.

Con la configuración actual (3 modelos × 2 intentos) son **6 intentos máximos**
por capítulo:

| Intentos | Modelo del escritor |
|---|---|
| 1, 2 | `mistralai/mistral-small-2603` |
| 3, 4 | `deepseek/deepseek-v3.2` |
| 5, 6 | `anthropic/claude-sonnet-4.6` |

La escalera cruza proveedores a propósito: cuando un modelo se atasca en un
error, otro de la misma familia tiende a repetirlo (adenda §3.3). La
contrapartida es que cada proveedor escribe con otra voz, y por eso
`mantener_voz_ganadora: true` hace que, una vez que un modelo resuelve un
capítulo, el siguiente empiece por ese mismo modelo en lugar de volver al
primero de la escalera.

**f. Agotada la escalera sin aprobación: aceptar la mejor versión.** Se calcula:

```
puntuacion = Σ (problemas de los tres validadores × peso de su gravedad)
```

Con los pesos por defecto (alta 5, media 2, baja 1), dos problemas medios
puntúan 4 y uno alto puntúa 5: gana el primero, porque **menor puntuación es
mejor**. En caso de empate gana el intento más tardío, por haber incorporado más
feedback. El capítulo se marca en el informe como `ACEPTADO_POR_PUNTUACION`.

**g. Al aprobar, actualizar la memoria larga.** Se escriben `salida/biblia.json`
(hechos nuevos, timeline), `salida/resumenes/cap-NN.md` (2–3 frases) y
`salida/memoria-estilo.json`. Si `hechos_establecidos` supera
`contexto.umbral_compactacion` entradas, se lanza una pasada de compactación que
funde los hechos efímeros antiguos en un resumen por capítulo. Los hechos
`permanente` no se compactan nunca.

### 3.6 Paso 6 — Ensamblar

Concatena por streaming los capítulos aprobados con su portada en
`salida/manuscrito.md` y genera `salida/informe-validacion.md`. El ensamblador
no reescribe nada. Después borra `salida/.tmp/`, salvo que
`runtime.conservar_intentos` sea `true`.

---

## 4. Reglas inviolables

Seis reglas que no se negocian. Si una implementación futura las contradice, la
implementación está mal, no el documento.

**1. Ningún capítulo detiene la generación.** Un capítulo que no pasa la
validación se acepta por puntuación y se marca en el informe. Nunca se aborta por
un fallo de capítulo. Las dos únicas excepciones son previas al bucle: entorno
inválido (§3.2) y biblia que no parsea (§3.4).

**2. Un validador cuyo JSON no parsea cuenta como `FALLO`, jamás como `PASA`.**
El procedimiento defensivo (adenda §3.5) es: `json.loads` directo → extraer el
primer bloque `{...}` equilibrado → repetir la llamada **una vez** incluyendo el
error de parseo → registrar `INDETERMINADO` y tratarlo como `FALLO`. Si un
validador roto aprobara por defecto, la validación sería decorativa.

**3. Los validadores no cambian de modelo durante una generación.**
`modelos.validadores` es fijo de principio a fin, y su temperatura es 0.1. Si el
modelo o la temperatura cambiaran, las puntuaciones de dos intentos dejarían de
ser comparables y la regla de mejor versión (§3.5f) no significaría nada.

**4. Ningún módulo salvo `src/agentes.py` toca la red.** Un único punto de
salida. Cuando algo falle, hay un solo sitio donde poner un `print`.

**5. La clave de API nunca se imprime ni se registra.** Solo se comprueba que la
variable de entorno existe. No aparece en logs, ni en `config-efectiva.json`, ni
en el informe, ni en mensajes de error. Hay un test que lo verifica.

**6. Comprobar los límites antes de cada llamada.** Antes de llamar a un modelo
se verifica el coste acumulado contra `limites.coste_max_usd` y el número de
llamadas contra `limites.llamadas_max_totales`. Si se supera y
`abortar_si_supera_coste` es `true`, se para de forma ordenada: se escribe
`estado.json`, se ensambla lo que haya y se deja constancia en el informe. Un
bucle de reintentos mal cerrado quema crédito muy rápido, y el contrato permite
hasta seis intentos por capítulo.

---

## 5. Qué aparece en `salida/`

`salida/` está en `.gitignore`: nunca se versiona.

### 5.1 Resultado final

| Archivo | Contenido |
|---|---|
| `manuscrito.md` | Portada más los capítulos concatenados en orden. El producto |
| `biblia.json` | Estado canónico final: premisa, personajes, outline, timeline, hechos |
| `informe-validacion.md` | Qué pasó en cada capítulo. Ver la sección 7 |
| `config-efectiva.json` | La configuración realmente usada tras fusionar las cuatro capas |

### 5.2 Memoria de trabajo

| Archivo | Contenido | Se actualiza |
|---|---|---|
| `estado.json` | Progreso: capítulo actual, intento, modelo activo, capítulos aprobados | Tras cada intento |
| `resumenes/cap-NN.md` | 2–3 frases por capítulo aprobado | Tras cada aprobación |
| `memoria-estilo.json` | Muletillas y frases recurrentes detectadas | Tras cada validación de estilo |
| `.tmp/cap-NN-intento-M.md` | Texto de cada intento | Cada intento |
| `.tmp/cap-NN-intento-M.json` | Veredictos y puntuación de ese intento | Cada intento |

Los `.tmp` son obligatorios durante la ejecución: sin ellos no se puede elegir la
mejor versión al agotar la escalera. Se borran al ensamblar salvo que
`conservar_intentos` sea `true`, y conservarlos es lo primero que hay que hacer
cuando quieras entender por qué un capítulo salió como salió.

---

## 6. Reanudar una ejecución interrumpida

Si la ejecución se corta (cierras la terminal, se cae la red, se agota el
crédito), el progreso está en `salida/estado.json`, que se escribe tras cada
intento.

**Para reanudar**, con `runtime.reanudar_si_existe_estado` en `true` (el valor
por defecto), basta con relanzar el mismo comando:

```powershell
python -m src.orquestador
```

Los capítulos ya aprobados no se regeneran ni se vuelven a pagar. La ejecución
retoma el primer capítulo no aprobado.

**Para empezar de cero**, borra el estado:

```powershell
Remove-Item salida\estado.json
```

O, si quieres borrar todo el trabajo anterior:

```powershell
Remove-Item -Recurse -Force salida
```

Cuidado: eso se lleva por delante el manuscrito y la biblia.

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
modelo de la escalera, la escalera está mal ordenada o el primero es demasiado
flojo para este género: te está costando cinco intentos de más por capítulo.

**El número de intentos.** Un capítulo que necesita cuatro intentos suele
señalar un problema en la biblia, no en el escritor: un outline confuso o un
personaje con rasgos contradictorios.

**Los problemas sin resolver.** Cada uno trae gravedad, descripción, evidencia
(el fragmento concreto del texto) y corrección sugerida. La evidencia es lo que
te permite ir al manuscrito y juzgar por ti mismo si el validador tenía razón.

**La puntuación.** Menor es mejor. Solo tiene sentido comparar puntuaciones
dentro de una misma generación, porque dependen del modelo validador.

**Los recortes de contexto aplicados.** Si en los últimos capítulos aparecen
recortes que no aparecían en los primeros, la ventana está creciendo con N y la
compactación no está haciendo su trabajo. Es la señal de alarma más importante
del informe: significa que el proyecto no escalaría a una novela más larga.

**Validadores `INDETERMINADO`.** Ese validador no devolvió JSON parseable y
contó como `FALLO`. Uno suelto es ruido; varios seguidos significan que el modelo
validador no respeta el formato y hay que cambiarlo.

---

## 8. Errores frecuentes

### 8.1 Configuración y entorno

| Mensaje | Qué pasa | Arreglo |
|---|---|---|
| `Falta la variable de entorno OPENROUTER_API_KEY` | No está definida en **esta** terminal | `$env:OPENROUTER_API_KEY = "tu_clave"`. Si la pusiste como permanente, abre una terminal nueva |
| `novela.genero vale ... y solo se admiten estos tres` | Género fuera de `romance`, `drama`, `terror` | Corrige `genero` en `config.json` o `NOVELA_GENERO` |
| `estructura.num_capitulos ... tiene que ser un numero entero mayor que cero` | Valor cero, negativo o no entero | Corrige `num_capitulos` |
| `estructura.palabras_min (X) tiene que ser menor que estructura.palabras_max (Y)` | Rango invertido | Revisa `estructura` **y** el perfil del género: el rango puede venir de cualquiera de los dos |
| `La variable de entorno NOVELA_X no corresponde a ningun ajuste` | Nombre mal escrito | Usa el nombre exacto de una clave de `config.json`, o borra la variable |
| `La variable de entorno NOVELA_X es ambigua` | Ese nombre existe en varias secciones | Usa la ruta completa, p. ej. `NOVELA_MODELOS__ARQUITECTO__MODELO` |
| `El archivo config.json no es JSON valido` | Coma de más o comillas sin cerrar | Ve a la línea que indica el mensaje |

### 8.2 OpenRouter

| Síntoma | Qué pasa | Arreglo |
|---|---|---|
| `404` o "model not found" | Slug de modelo inexistente o retirado | Los slugs cambian a menudo: verifícalos en openrouter.ai/models y actualiza `config.json` |
| `401 Unauthorized` | Clave inválida, revocada o mal copiada | Genera una nueva en el panel de OpenRouter |
| `402` o "insufficient credits" | Sin crédito | Recarga. El progreso está en `estado.json`: al reanudar no pagas lo ya generado |
| `429 Too Many Requests` | Límite de velocidad del proveedor | El cliente reintenta con espera creciente (`reintentos_red`, `backoff_segundos`). Si persiste, baja el paralelismo o cambia de modelo validador |
| Timeout | Respuesta más lenta que `proveedor.timeout_segundos` | Sube el timeout o baja `max_tokens` |
| Se detiene diciendo que se superó el coste | Se alcanzó `limites.coste_max_usd` | Sube el límite a conciencia, o reduce `num_capitulos` e `intentos_por_modelo` |

### 8.3 Generación

| Síntoma | Qué pasa | Arreglo |
|---|---|---|
| Un validador sale `INDETERMINADO` | Su JSON no parseó ni tras el reintento. Cuenta como `FALLO` | Si se repite, cambia `modelos.validadores` por un modelo que respete mejor el formato JSON |
| Todos los capítulos salen `ACEPTADO_POR_PUNTUACION` | Los validadores son demasiado estrictos, o el rango de palabras es incompatible con el género | Mira los problemas repetidos en el informe: suelen apuntar a una sola causa |
| Los capítulos son mucho más cortos o largos de lo pedido | El rango efectivo no es el que crees | Mira `salida/config-efectiva.json`: el perfil del género o una variable `NOVELA_` pueden estar cambiándolo |
| Reanuda y mezcla dos historias distintas | `estado.json` es de otra configuración | Borra `salida/` y relanza |
| La prosa cambia de voz entre capítulos | Distintos modelos resolvieron distintos capítulos | Es el efecto conocido de la escalera multiproveedor. `mantener_voz_ganadora: true` lo mitiga |
| `ModuleNotFoundError: No module named 'src'` | Lo lanzaste desde otra carpeta | Ejecuta siempre desde la raíz del proyecto |

---

## 9. Documentos relacionados

| Documento | Para qué |
|---|---|
| `SPEC-generador-novelas-v3.md` | Especificación completa y el porqué de cada decisión |
| `ADENDA-openrouter-vscode.md` | Capa de modelos sobre OpenRouter y montaje. Manda sobre el spec donde se contradigan |
| `CLAUDE.md` | Reglas del proyecto para trabajar en el código |
| `config.json` | Toda la configuración ajustable |
| `Harness_novela.drawio.png` | Diagrama del flujo |
