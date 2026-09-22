# Verificación — My_novel_story

2026-09-22 · @Santiago Espinosa Domínguez

Cómo se prueba que **el sistema** hace lo que dice que hace. Este documento no
evalúa la novela que el sistema escribe: de eso se ocupan las invariantes
`INV-01`…`INV-16`, que aquí son el objeto verificado, no el sujeto.

Generado con la skill `verification-plan` (`.agents/skills/verification-plan/`) y
reorganizado según `Docs/revisiones/REV-02 - Verification.md`, que añadió el eje
que faltaba: **el punto ciego de cada validador**.

## Qué se verifica aquí

| Pregunta | Quién la responde |
| --- | --- |
| ¿Es buena la novela? ¿Da miedo? ¿Se sostiene la continuidad? | Las invariantes `INV-01`…`INV-16` de `Docs/definitions.md`, ejecutadas por el harness |
| ¿Están bien implementadas esas invariantes, el presupuesto de contexto, la máquina de estados y los agentes? | **Este documento** |

Dicho de otro modo: `INV-05` dice que ninguna escena se da por buena sin su
delta aplicado. Que esa regla exista es dominio. Que el código la cumpla de
verdad, y que falle cuando debe fallar, es lo que se planifica aquí.

---

## Cómo se lee este documento

El modelo no garantiza que sus resultados sean correctos, así que la fiabilidad
no sale de él: sale de los validadores que lo rodean. Y **un validador aislado no
significa nada**, porque cada uno tiene un punto ciego por construcción. Lo que
importa es si esos puntos ciegos se solapan o se cubren entre sí.

De ahí las tres reglas que gobiernan este documento:

### Regla 1 — Todo validador declara su punto ciego

La columna **Punto ciego** no es documentación: es la columna que decide si un
validador vale. Un validador sin punto ciego declarado es un validador que no se
ha entendido.

### Regla 2 — Un validador nuevo entra solo si su punto ciego es distinto

Si el punto ciego de un validador nuevo coincide con el de uno que ya está, es
**cobertura falsa**: parece que se cubre más y no se cubre nada nuevo. El caso de
libro son los validadores de análisis estático: hay once y comparten el mismo
límite, así que el duodécimo no taparía nada. Un validador que no puede
justificar un punto ciego propio no entra, y el hueco que iba a tapar se anota en
"Puntos ciegos asumidos".

### Regla 3 — Un validador no comparte implementación con lo que valida

**Si el validador usa la misma pieza que la cosa validada, no está verificando:
está haciendo eco.** Un contador de tokens que se comprueba consigo mismo siempre
da que sí. Un aplicador de deltas comparado con otra ejecución de sí mismo
siempre coincide, incluso cuando los dos están mal.

Esto no es el arreglo de dos filas concretas: es una condición de admisión. Al
escribir o revisar un validador hay que responder **de dónde sale su referencia**,
y la respuesta no puede ser "de la misma función". Las referencias válidas son
tres:

1. **Una fuente externa al sistema** —lo que devuelve el proveedor del modelo, lo
   que dice el documento normativo—.
2. **Una implementación de referencia escrita solo para la prueba**,
   deliberadamente ingenua: lenta, sin optimizar y fácil de leer. Si la de
   producción y la ingenua coinciden, el acuerdo significa algo.
3. **Un dato fijado a mano** en el caso de prueba.

Las dos filas que incumplían esta regla, `VER-05` y `VER-09`, están corregidas:
ver la nota bajo la tabla de nivel artefacto.

---

## Estado de implantación

| | |
| --- | --- |
| **Validadores definidos** | **43** (`VER-01`…`VER-43`) |
| **De ellos, no verificables hoy** | 6 (`VER-32`…`VER-37`) |
| **Validadores implementados** | **0** |
| **Puntos ciegos asumidos a sabiendas** | 8 |

**Cero implementados, y conviene decirlo en voz alta: una lista más larga no es
más cobertura.** Este documento ha pasado de 37 validadores a 43 y sigue sin
proteger nada, porque no existen `backend/`, `frontend/` ni `harness/`, y
`CLAUDE.md` dice que aún no hay build ni tests. Un plan de verificación con más
filas y cero implementación es un plan mejor, no un sistema más fiable. La única
cifra que mide fiabilidad es la tercera.

## Semilla de contexto

| Documento | Qué afirmaciones aporta |
| --- | --- |
| `CLAUDE.md` | Stack, presupuesto de 100.000 tokens y su reparto, reglas de Pydantic y enumeraciones, reglas de persistencia |
| `AGENTS.md` | Precedencia entre documentos, reglas de uso del modelo de dominio, estabilidad de identificadores |
| `Docs/definitions.md` | Las dieciséis invariantes con su nivel y severidad, los vocabularios controlados, la política de casos negativos |
| `Docs/domain-knowledge.md` | La máquina de estados de la escena y la secuencia de generación |
| `Docs/architecture.md` | Reglas de dependencia entre features, contrato de los agentes, cola de trabajos, reglas de presentación del frontend |

Si la semilla cambia, este plan cambia. Una fila cuyo origen desaparezca del
documento de partida se marca obsoleta, no se borra.

---

## Nivel artefacto — ¿es correcto el código?

Ninguna fila lleva columna de estado: **todas están pendientes**. Ver "Estado de
implantación".

| ID | Afirmación | Clase | Metodología | Criterio de salida | **Punto ciego** | Dónde vive |
| --- | --- | --- | --- | --- | --- | --- |
| VER-01 | Los esquemas Pydantic y las fichas de clase de `Docs/definitions.md` tienen exactamente los mismos campos, **en los dos sentidos** | A | static analysis | El comprobador recorre los esquemas contra las fichas y las fichas contra los esquemas: cero campos de más y cero campos de menos | Ve **nombres**, no tipos ni valores: un campo `severidad: str` donde debería haber un `Enum` pasa | `harness/esquema/` |
| VER-02 | Un valor fuera de un vocabulario controlado es error de validación, y **cada `Enum` tiene exactamente los valores de su tabla** | T | unit testing | Cada enumeración rechaza un valor inventado, **y** su número de miembros coincide con el de la tabla de vocabularios | Compara cardinalidad y pertenencia, no **uso**: un campo tipado `str` que nunca toca el `Enum` pasa | `commons/dominio/tests/` |
| VER-03 | El endpoint de generación no bloquea: devuelve un identificador de trabajo | T | integration testing | La respuesta llega antes de que termine la generación y trae un identificador consultable | No comprueba que el trabajo **llegue a ejecutarse**: un worker parado deja `202` y trabajos eternos | `features/generacion/tests/` |
| VER-04 | Un trabajo encolado sobrevive a un reinicio del servidor | T | integration testing | Se encola, se mata el proceso, se levanta, y el trabajo sigue ahí y se completa | **No comprueba unicidad**: el trabajo puede completarse habiendo llamado al modelo dos veces | `commons/trabajos/tests/` |
| VER-05 | Ninguna llamada al modelo supera los 100.000 tokens, salida incluida, **medido con un contador independiente del ensamblador** | T | property-based testing | El contexto ensamblado más la reserva de salida cabe en el límite **según el `usage` que devuelve el modelo o un segundo tokenizador**, no según el contador de producción (Regla 3) | Mide el **techo**, no el **contenido**: un contexto de 3.000 tokens que dejó fuera al protagonista pasa | `features/contexto/tests/` |
| VER-06 | Cuando no cabe, se recorta por el nivel de menor prioridad, nunca truncando por el final | T | property-based testing | Ningún recorte parte un bloque, y el orden de recorte respeta la prioridad declarada | **El orden completo de los seis niveles no está fijado todavía**: hoy solo puede comprobar los extremos | `features/contexto/tests/` |
| VER-07 | Nunca se manda el texto completo de la obra al modelo | T | unit testing | Con una obra de muchas escenas, el contexto no contiene el texto de ninguna escena salvo la anterior | Mira **texto de escena**, no **volumen equivalente**: resúmenes que crecen hasta reconstruir la obra pasan | `features/contexto/tests/` |
| VER-08 | El texto completo de una escena se guarda pero no se recupera por similitud | T | integration testing | La búsqueda vectorial solo devuelve fichas, resúmenes y presagios | Comprueba el **índice**, no el **camino de lectura**: leer el texto por clave primaria lo esquiva *(lo cubre `VER-07`)* | `commons/db/tests/` |
| VER-09 | El estado del mundo se reconstruye acumulando deltas en orden, **contrastado con una implementación de referencia** | T | property-based testing | Reconstruir con el aplicador de producción y con un **aplicador de referencia ingenuo escrito solo para la prueba** da el mismo estado (Regla 3) | Comprueba que el estado **se construye bien desde el delta**, no que el **delta sea cierto** *(lo cubre parcialmente `VER-39`)* | `features/consolidacion/tests/` |
| VER-10 | Ninguna escena pasa a `consolidada` sin su delta aplicado (`INV-05`) | T | unit testing | Intentar consolidar sin delta aplicado falla; la escena siguiente no se puede generar | Comprueba que el delta **se aplicó**, no que se aplicara **entero** *(lo cubre `VER-42`)* | `features/consolidacion/tests/` |
| VER-11 | `bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y dejan seguir | T | unit testing | Un hallazgo de cada severidad produce exactamente el comportamiento declarado | Comprueba el comportamiento **dada** una severidad, no que la **asignada sea la correcta** *(lo cubre `VER-38`)* | `commons/invariantes/tests/` |
| VER-12 | Todo hallazgo cita su invariante por identificador, nunca por descripción | A | static analysis | Todo `Hallazgo` construido lleva un identificador del registro `INV-xx` | Comprueba que el id **existe**, no que sea el **correcto**: un verificador copiado que no cambió el id pasa | `commons/invariantes/` |
| VER-13 | Una feature nunca importa de otra feature, salvo `orquestacion/` | A | static analysis | El comprobador de importaciones falla el build ante cualquier import cruzado no autorizado | Estático: no ve importación dinámica ni acoplamiento por datos compartidos | CI |
| VER-14 | `commons/` nunca importa de una feature | A | static analysis | Mismo comprobador; la flecha va en un solo sentido | El mismo que `VER-13` | CI |
| VER-15 | Los `Enum` de los vocabularios controlados viven solo en `commons/dominio/` | A | static analysis | No hay ninguna definición de `Enum` de dominio fuera de esa carpeta | **Sin punto ciego relevante**: regla estructural sobre artefacto estático. El único escape sería crear un `Enum` en tiempo de ejecución a propósito | CI |
| VER-16 | El frontend nunca accede a la base de datos ni calcula estado de dominio | A | static analysis | El frontend no depende de ningún cliente de base de datos | Comprueba **dependencias**, no **lógica**: deducir el estado de una escena a partir de campos sueltos pasa | CI |
| VER-17 | Un módulo del frontend solo importa de capas FSD estrictamente inferiores | A | static analysis | El comprobador de FSD pasa sin violaciones | Comprueba **capas**, no **responsabilidades**: lógica de negocio dentro de `shared/` pasa | CI |
| VER-18 | Una escena nunca se muestra sin su estado y sus hallazgos abiertos | T | unit testing | El componente no renderiza texto si falta el estado o la lista de hallazgos | Comprueba el **componente**, no la **API**; y presencia, no que sean los de estado `abierto` | `frontend/.../tests/` |
| VER-19 | Un dato sin medir se muestra "sin medir", nunca como cero | T | unit testing | Con el valor ausente la interfaz pinta "sin medir"; con cero, pinta cero | Comprueba la **presentación**, no el **origen**: si el backend devuelve `0` donde no midió, la interfaz acierta y el dato miente | `frontend/.../tests/` |
| VER-20 | El Escritor devuelve texto y delta en la misma respuesta | T | contract testing | Una respuesta sin delta, o con delta fuera de esquema, se rechaza sin llegar a las puertas | Comprueba **forma**, no **correspondencia con el texto** *(lo cubre parcialmente `VER-39`)* | `features/generacion/tests/` |
| VER-21 | Todo cambio de un atributo obligatorio en `Docs/definitions.md` lleva su migración en el mismo commit | A | CI/CD integration | Un commit que toque un atributo obligatorio sin añadir migración falla en CI | Comprueba que la migración **existe**, no que sea **correcta**: una migración vacía pasa | CI |
| VER-22 | Cada invariante `INV-01`…`INV-16` tiene un caso negativo **que de verdad la caza** | A | mutation testing | **Se desactiva la comprobación de la invariante y su caso negativo tiene que fallar.** Si sigue pasando, el caso no estaba probando nada | Prueba la **eficacia del caso**, no su **representatividad**: un solo caso negativo no cubre todas las formas de violar la invariante | `harness/` |
| VER-23 | Ningún identificador publicado se reutiliza ni se renumera | A | static analysis | El conjunto de identificadores solo crece; lo retirado queda marcado obsoleto | Ve el **conjunto**, no el **significado**: cambiar el enunciado de `INV-14` manteniendo el número pasa | CI |
| **VER-38** | La severidad, el nivel y el tipo declarados en el código para cada invariante coinciden con la tabla de `Docs/definitions.md` | A | static analysis | Se parsea la tabla de invariantes y se compara con el registro de `commons/invariantes/`: identificador, nivel, severidad y tipo, los cuatro iguales | Compara **declaración contra declaración**: no comprueba que el verificador respete la severidad que declara *(lo cubre `VER-11`)* | `harness/esquema/` |
| **VER-39** | Toda entidad que el delta declara aparece mencionada en el texto de la escena, y todo personaje mencionado está en `personajes_presentes[]` | T | contract testing | Por cada entrada del delta, su `nombre_canonico` o algún `alias` aparece en el texto; y ningún nombre del texto queda fuera de `personajes_presentes[]` | **Compara superficie léxica, no sentido**: un delta equivocado sobre alguien que **sí** está mencionado pasa | `features/consolidacion/tests/` |
| **VER-42** | Aplicar un delta es atómico: o entran todas sus entradas o ninguna | T | integration testing | Se fuerza un fallo a mitad de la aplicación y el estado queda exactamente como antes; el número de cambios aplicados coincide con el de entradas del delta | Cuenta **entradas aplicadas**, no la **corrección de cada una** *(lo cubre parcialmente `VER-39`)* | `features/consolidacion/tests/` |
| **VER-43** | Una escena no supera un número acotado de ciclos de regeneración | T | unit testing | Con un tope configurado, la escena número `tope+1` se detiene y se marca en vez de volver a generarse. **El valor del tope sale de medir, no se fija aquí** | Cuenta **ciclos**, no **diagnostica la causa**: detecta que gira, no por qué | `features/orquestacion/tests/` |

**Nota sobre la Regla 3 aplicada a `VER-05` y `VER-09`.** Eran las dos filas que
compartían implementación con lo que validaban.

- **`VER-05`** contaba tokens con el contador del ensamblador, así que un
  tokenizador equivocado se validaba a sí mismo y la llamada real se pasaba del
  límite sin que nadie lo viera. Ahora su referencia es **externa**: el `usage`
  que devuelve el modelo, o un segundo tokenizador independiente. Esto lo ata a
  `VER-41`, que es quien hace la reconciliación.
- **`VER-09`** comparaba dos ejecuciones del mismo aplicador de deltas, que
  coinciden incluso cuando las dos están mal. Ahora su referencia es una
  **implementación ingenua escrita solo para la prueba**: lenta, sin optimizar y
  legible de un vistazo. Cuando la de producción y la ingenua coinciden, el
  acuerdo significa algo.

---

## Nivel proceso — ¿se comportan los agentes de forma fiable?

| ID | Afirmación | Clase | Metodología | Criterio de salida | **Punto ciego** | Dónde vive |
| --- | --- | --- | --- | --- | --- | --- |
| VER-24 | Cada llamada de agente deja una traza consultable después del hecho | T | runtime observability / tracing | Toda llamada emite traza con agente, escena, niveles de contexto enviados y tokens consumidos | Comprueba que la traza **existe**, no que su contenido sea **real** *(lo cubre `VER-41` para los tokens, no para los niveles)* | `commons/modelo/` |
| VER-25 | El Juez no recibe el prompt ni el razonamiento del Escritor | T | unit testing | El contexto que llega al Juez contiene texto y rúbrica, y nada del prompt del Escritor | Comprueba **una** fuga concreta, no todas: el `Borrador` completo lleva `modelo` y `prompt_hash` y entra por otro campo | `features/verificacion/tests/` |
| VER-26 | El Juez no aprueba sistemáticamente lo que una persona rechaza | T | evals | Existe una medición publicada de concordancia entre Juez y persona. **El umbral se fija después de la primera medición, no antes** | Mide **concordancia**, no **corrección**: si persona y Juez se equivocan igual, la concordancia es alta | `harness/evals/` |
| VER-27 | La salida de cada agente valida contra su esquema tipado, o se rechaza | T | guardrails | Una salida fuera de esquema no llega nunca a la capa siguiente; se rechaza y se registra | **Una salida vacía es esquema válido**: no distingue "no encontró nada" de "no funcionó" *(lo cubre `VER-40`)* | `commons/modelo/` |
| VER-28 | No existe ningún camino de `planificada` a `consolidada` que no pase por `en_verificacion` | A | model checking | Exploración exhaustiva de la máquina de estados: ningún camino alcanzable salta la puerta | Verifica el **modelo**, no la **implementación**: un `UPDATE` directo a la base lo esquiva | `features/orquestacion/tests/` |
| VER-29 | Ninguna ruta del worker lleva una escena a `aceptada` | A | static analysis | El worker no tiene ninguna ruta de código que produzca esa transición | Comprueba que **el worker no puede**, no que quien acepta sea **una persona**: sin autenticación, un script llama al endpoint igual | `features/orquestacion/tests/` |
| VER-30 | El Escritor no viola las reglas de la amenaza bajo los prompts adversarios del corpus | T | red-teaming / adversarial testing | El corpus adversario se ejecuta en CI y ningún caso conocido vuelve a fallar | Cubre lo que **ya está en el corpus**: no inventa ataques nuevos, para eso sigue haciendo falta una persona | `harness/adversarial/` |
| VER-31 | Los cambios generados por agente pasan por la misma tubería que los escritos a mano | A | CI/CD integration | No hay ninguna ruta que publique cambios saltándose CI | Comprueba que **se pasa** por CI, no que CI **compruebe algo útil** | CI |
| **VER-40** | El Juez caza el defecto conocido del canario en cada lote de verificación | T | guardrails | Cada lote incluye una escena con un defecto plantado; si el Juez no lo señala, el lote se marca como no fiable | Detecta que el Juez **funciona**, no que **acierte**. Y un canario fijo puede acabar acertándose por memorización | `harness/evals/` |
| **VER-41** | Los tokens que registra la traza coinciden con los que declara la respuesta del modelo | T | runtime observability / tracing | La diferencia entre lo trazado y el `usage` de la respuesta es cero para toda llamada | Valida el contador **contra el proveedor**, no contra la verdad: si el `usage` del proveedor es incorrecto, los dos coinciden en el error | `commons/modelo/` |

**`VER-29` ha cambiado de metodología.** Declaraba `human-in-the-loop review` y
su criterio era *"el worker no tiene ninguna ruta de código"*, que es análisis
estático puro: la etiqueta decía juicio humano y el trabajo lo hacía un
comprobador. Ahora dice lo que hace. Que la aceptación la ejecute **una persona**
no lo verifica nadie, y eso está anotado en "Puntos ciegos asumidos".

---

## No verificable hoy

| ID | Afirmación | Qué falta exactamente | Decisión abierta que lo desbloquea |
| --- | --- | --- | --- |
| VER-32 | La distancia estilométrica a las anclas se mantiene bajo umbral (`INV-15`) | Medir la distancia sobre un corpus y fijar el número con esa medición | `Docs/definitions.md` § Decisiones abiertas → **"Umbrales"** |
| VER-33 | La varianza de la curva de dread supera el mínimo fijado (`INV-16`) | Lo mismo: primero medir, después fijar | `Docs/definitions.md` § Decisiones abiertas → **"Umbrales"** |
| VER-34 | Cada agente cabe en su parte del presupuesto de contexto | Instrumentar el consumo por agente durante varias escenas. **Depende de `VER-41`**: sin reconciliar, mediría sobre un dato sin validar | `Docs/architecture.md` § Decisiones abiertas → "Reparto de tokens por agente" |
| VER-35 | Cuando el Juez marca `INV-03` y la regla de continuidad no ve nada, gana el correcto | La decisión de quién gana. **La parte medible —cuántas veces discrepan y en qué dirección— no necesita la decisión y se puede instrumentar ya** | `Docs/definitions.md` → "Desempate juez vs. regla" |
| VER-36 | El coste por escena es sostenible para una obra completa | Coste real de una escena con `A-03`. **Depende de `VER-41`** | Ninguna. Nace aquí |
| VER-37 | El reparto por niveles de `CLAUDE.md` basta para una escena real | Ensamblar el contexto de una escena real y ver si cabe. **Depende de `VER-41`** | Ninguna. Nace aquí |

`VER-32` y `VER-33` **son la decisión "Umbrales" con dos fichas**: quien la cierre
en `Docs/definitions.md` tiene que cerrarlas aquí en el mismo commit, y al revés.
Ninguna de las seis lleva umbral provisional, porque un umbral inventado que
queda escrito deja de distinguirse de uno medido.

**Tres de las seis dependen de `VER-41`**, que es nuevo y barato. Es la razón de
que suba tan arriba en el orden de implantación.

---

## Puntos ciegos asumidos

Huecos que **hoy no tapa nadie** y que se asumen a sabiendas. Un hueco escrito no
es un problema; uno que nadie escribió, sí. Cada uno con el fallo concreto que
dejaría pasar.

| # | Punto ciego asumido | Fallo concreto que se cuela | Por qué se asume |
| --- | --- | --- | --- |
| **PC-1** | **El análisis estático no ve la ejecución.** Once validadores lo comparten: `VER-01`, `VER-12`, `VER-13`, `VER-14`, `VER-15`, `VER-16`, `VER-17`, `VER-21`, `VER-23`, `VER-28`, `VER-31`, `VER-38` | Un script de mantenimiento hace `UPDATE escena SET estado='consolidada'` y salta la máquina de estados entera | Taparlo pide auditoría en tiempo de ejecución sobre la base. No es caro, pero no hay base todavía |
| **PC-2** | **Nadie comprueba que quien acepta una escena sea una persona.** `VER-29` solo comprueba que el worker no puede | Un script llama a `POST /escenas/{id}/aceptar` en bucle y consolida la obra entera sin que nadie la lea | `SPEC-01` §2.5 excluye la autenticación de la v1. Sin identidad no hay nada que comprobar |
| **PC-3** | **La fiabilidad del Juez no está medida**, y `VER-26` en verde significa "se midió", no "es fiable" | `INV-03` es `bloqueante` y de tipo `juez_llm`: es la única puerta que detiene una escena basándose en un modelo cuya fiabilidad se desconoce | El corpus de `VER-26` es una decisión abierta. Hasta entonces, `VER-40` detecta al menos que el Juez funciona |
| **PC-4** | **Los resúmenes pueden crecer hasta reconstruir la obra.** Se propuso un validador de ratio de compresión y **se rechazó por la Regla 2**: su punto ciego —mide longitud, no calidad— ya lo tienen seis validadores | El Resumidor devuelve resúmenes casi tan largos como la escena. `VER-07` está en verde porque no hay texto de escena en el contexto, y el contexto lleva la obra entera de todos modos | Se asume hasta encontrar una comprobación con un punto ciego propio |
| **PC-5** | **`VER-39` compara léxico, no sentido** | El delta dice que Marta coge el cuchillo y en el texto lo coge Luis. Los dos nombres están mencionados, así que `VER-39` pasa | La comprobación semántica exige un juez, y un juez sin fiabilidad medida no mejora esto |
| **PC-6** | **`VER-12` comprueba que el identificador existe, no que sea el correcto** | Se copia un verificador y no se cambia el id: todos los hallazgos salen como `INV-01` y el recuento por invariante miente | `VER-38` valida el registro, no qué id usa cada verificador al construir el hallazgo |
| **PC-7** | **`VER-21` comprueba que la migración existe, no que sea correcta** | Se añade un atributo obligatorio y se commitea una migración vacía. CI verde y la columna no existe | Validar que una migración hace lo que dice exige ejecutarla contra un esquema de referencia |
| **PC-8** | **`VER-41` valida el contador contra el proveedor, no contra la verdad** | El `usage` del proveedor es incorrecto: el contador propio y el del proveedor coinciden en el mismo error | No hay una tercera fuente. Se asume que el proveedor mide bien lo que factura |

---

## Juicio que en realidad es una comparación

`Docs/definitions.md` clasifica cuatro invariantes como `juez_llm` y este
documento tenía dos validadores etiquetados como juicio. Al revisarlos, varios
resultaron ser aritmética disfrazada.

| Caso | Qué dice que es | Qué es en realidad | Estado |
| --- | --- | --- | --- |
| **`VER-29`** | `human-in-the-loop review` | Análisis estático: *"el worker no tiene ninguna ruta de código"* | **Corregido en este documento** |
| **`VER-30`** | Inspección (clase `I`) | Regresión sobre un corpus, que es un test | **Corregido en este documento** |
| **`INV-14`** — *"cada deterioro es monótono, o su reversión está justificada"* | `juez_llm` | `Deterioro.serie_por_escena` es una serie numérica: la monotonía es una comparación. Solo la cláusula de la justificación necesita criterio | **Pendiente**: cambiarlo toca `Docs/definitions.md`, que es dominio y necesita spec |
| **`INV-11`** — *"el grado de explicación acumulado no supera el fijado"* | `juez_llm` | Un conteo: cuántos `HechoCanonico` sobre la amenaza están revelados al lector frente a `grado_de_explicacion_permitido`. Solo lo implícito necesita juez | **Pendiente**, mismo motivo |
| **`VER-26`** | `evals` con persona | La **estabilidad** del Juez se mide sin nadie: misma escena N veces, varianza del veredicto. Un juez que se contradice consigo mismo se descarta sin corpus | **Pendiente**: no cambia la fila, añade un paso previo |

`INV-03` e `INV-10` admiten un filtro determinista previo —comparar ids del
registro de conocimiento, comprobar si el delta registra el coste de
invocación— pero conservan una parte que solo el juez puede resolver, así que
siguen siendo `juez_llm` con razón.

---

## Casos negativos

Toda fila de clase `T` necesita una entrada que la viole a propósito. Una regla
que nunca ha fallado en las pruebas no está verificada, solo declarada.

| ID | Caso negativo | Qué debe cazarlo |
| --- | --- | --- |
| VER-02 | `rol_dramatico = "narrador"`, y un `Enum` al que le falta un valor de la tabla | Validación del esquema y la comparación de cardinalidad |
| VER-03 | Un generador que tarda mucho más que el tiempo de respuesta del endpoint | El test comprueba que la respuesta llega igualmente |
| VER-04 | Matar el proceso con un trabajo a medias | El worker lo retoma al arrancar |
| VER-05 | Un contexto que el contador de producción da por bueno y el `usage` real desmiente | La reconciliación falla |
| VER-06 | Un contexto que excede por poco, con el nivel inmutable al máximo | Se recorta por prioridad y ningún bloque queda partido |
| VER-07 | Una obra con cuarenta escenas consolidadas | El contexto no contiene el texto de la escena 3 |
| VER-08 | Una consulta de similitud cuyo vecino más próximo sea un texto completo | La consulta no puede devolverlo: no está indexado |
| VER-09 | Una secuencia de deltas con un movimiento y una muerte en el mismo `t` | El aplicador de producción y el de referencia coinciden |
| VER-10 | Consolidar una escena cuyo delta no se ha aplicado | La transición se rechaza |
| VER-11 | Un hallazgo `mayor` en una escena por lo demás correcta | La escena sigue; el hallazgo queda abierto y visible |
| VER-18 | Una respuesta de la API sin la lista de hallazgos | El componente no renderiza el texto |
| VER-19 | Un contador de tokens ausente frente a uno con valor cero | "sin medir" en el primero, `0` en el segundo |
| VER-20 | Una respuesta del Escritor con texto y sin delta | Se rechaza antes de las puertas |
| VER-24 | Una llamada que falla con excepción | También deja traza |
| VER-25 | Un contexto de Juez al que se le cuela el prompt del Escritor | El test lo detecta |
| VER-26 | Una escena mala que el Escritor considera buena | Se mide si el Juez la aprueba |
| VER-27 | Una salida del modelo con un campo de más | Se rechaza y se registra |
| VER-29 | Una ruta del worker que intente llevar una escena a `aceptada` | El comprobador estático la encuentra |
| **VER-30** | Un prompt adversario del corpus que ya hizo fallar al Escritor una vez | Vuelve a comprobarse en cada ejecución de CI |
| **VER-39** | Un delta que declara una muerte de un personaje que no aparece en el texto | La comprobación de menciones falla |
| **VER-40** | Un Juez que devuelve lista vacía | El canario no aparece señalado y el lote se marca |
| **VER-41** | Una traza que registra el presupuesto planificado en vez del consumido | La diferencia con el `usage` no es cero |
| **VER-42** | Un fallo forzado a mitad de aplicar un delta de tres entradas | El estado queda como antes; no hay una entrada aplicada |
| **VER-43** | Una escena que falla la misma invariante `tope+1` veces | Se detiene y se marca en vez de regenerarse |

---

## Orden de implantación

Ordenado por **hueco que tapa**, no por facilidad. Un validador barato que no
tapa nada nuevo no va primero por ser barato.

| # | Qué | Por qué en ese puesto |
| --- | --- | --- |
| **1** | **`VER-38`** — clasificación de invariantes contra la tabla | Es el validador que **valida a otros tres**: hoy `VER-11`, `VER-12` y `VER-22` pueden estar los tres en verde con una severidad mal puesta, que es justo el anti-patrón *"bajar una bloqueante a mayor para desatascar"* de la skill `harness-invariantes`. Parsear una tabla y comparar dos diccionarios |
| **2** | **Las cuatro modificaciones**: `VER-01` bidireccional, `VER-02` con cardinalidad, `VER-22` con mutación de verdad, `VER-30` de inspección a regresión | Rinden más que las altas y cuestan menos: es el mismo comprobador recorrido en los dos sentidos, un conteo añadido, un criterio reescrito y un corpus movido a CI |
| **3** | **`VER-39`** — menciones del delta en el texto | Ataca el hueco más grande, que nada contraste el delta con su origen, y es el **único validador determinista que lee el texto generado** |
| **4** | **`VER-41`** — reconciliación de trazas | Barato, cierra el punto ciego de `VER-24` y **desbloquea `VER-34`, `VER-36` y `VER-37`**, que hoy medirían sobre un dato sin validar |
| **5** | **`VER-40`** y **`VER-42`** | Los dos fallos silenciosos: el agente que devuelve vacío y el delta que se aplica a medias |
| **6** | **`VER-43`** | Necesita un tope que hay que medir antes de fijar; la maquinaria se puede escribir ya |
| **7** | **`VER-10`, `VER-11`, `VER-28`** — máquina de estados y puertas | Siguen siendo lo que corta la propagación del error, pero después de `VER-38`, que es quien garantiza que las severidades sobre las que operan son las correctas |
| **8** | **`VER-13`…`VER-17`, `VER-23`** — comprobadores de estructura | Baratos y se escriben una vez, pero **comparten `PC-1` entre todos**: implantarlos pronto da una sensación de cobertura que no se corresponde con los huecos que quedan |
| **9** | **`VER-02`, `VER-20`, `VER-27`** — contratos de datos | Baratos y cazan mucho |
| **10** | **`VER-05`, `VER-06`, `VER-07`, `VER-09`** — presupuesto y deltas | Donde vive el riesgo de que el sistema no escale. `VER-05` depende de `VER-41` para tener referencia externa |
| **11** | **`VER-03`, `VER-04`, `VER-24`** — trabajos asíncronos y trazas | — |
| **12** | **`VER-22`, `VER-26`, `VER-30`** — mutación, evals y red-teaming | Los más caros, y sin sentido hasta que haya código que probar |

---

## Decisiones abiertas

- [ ] **Qué comprobador de importaciones** se usa para `VER-13`, `VER-14` y `VER-15`.
- [ ] **Qué herramienta de FSD** cierra `VER-17`.
- [ ] **Qué conjunto de escenas** sirve de corpus para los evals de `VER-26`.
- [ ] **Qué defecto planta el canario** de `VER-40`, y cada cuánto se cambia para
      que el Juez no acabe acertándolo por memorización.
- [ ] **Quién genera prompts nuevos** para el corpus de `VER-30` y cada cuánto.
- [ ] **Dónde viven las trazas** de `VER-24` y quién las mira.
- [ ] **El tope de ciclos de regeneración** de `VER-43`. Sale de observar cuántas
      veces regenera de verdad una escena problemática.
- [ ] **Umbrales de `INV-15` e `INV-16`** (`VER-32`, `VER-33`). Es la misma
      decisión "Umbrales" de `Docs/definitions.md`: se cierran las tres a la vez.
- [ ] **Coste por escena** (`VER-36`) y **suficiencia del reparto por niveles**
      (`VER-37`). Nacen aquí y hay que abrirlas en `Docs/architecture.md`.
- [ ] **Bajar `INV-14` a `regla` y `INV-11` a `regla` con juez de desempate.**
      Toca `Docs/definitions.md`, que es dominio: necesita spec aprobada.
