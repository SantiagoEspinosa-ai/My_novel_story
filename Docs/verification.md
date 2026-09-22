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

# Modos de fallo

Este documento respondía a *cómo se verifica* y no a *qué puede salir mal*. Sin
esa lista, cada validador parece una buena idea suelta y no hay forma de saber si
el conjunto cubre algo. Aquí está el problema; después vienen los detectores.

## Las tres rejillas y qué aporta cada una

| Fuente | Qué aporta | Qué no |
| --- | --- | --- |
| **MAST** — *Why Do Multi-Agent LLM Systems Fail?*, arXiv 2503.13657. Catorce modos en tres categorías: diseño del sistema, desalineación entre agentes, verificación de tareas | La estructura de la sección y **prevalencias medidas**. Su crítica central —*los agentes verificadores hacen comprobaciones superficiales y hace falta verificación por capas*— es exactamente el eje de puntos ciegos de este documento | No sabe nada de narrativa. Ninguno de sus modos habla de continuidad ni de voz |
| **ConStory-Bench** — arXiv 2603.05890. Cinco categorías de error de consistencia narrativa con diecinueve subtipos: cronología y trama, caracterización, construcción de mundo, factual, estilo narrativo | El único inventario de fallos **del producto**, no del sistema. Y cuatro observaciones metodológicas que valen más que la taxonomía: los errores factuales y temporales dominan, se concentran **hacia la mitad** de la narración, aparecen en segmentos de **mayor entropía por token**, y ciertos tipos **co-ocurren** | No distingue si el error lo causó el modelo, el contexto o la orquestación, que es justo lo que a nosotros nos dice dónde poner el validador |
| **Fallos silenciosos de producción** — completado parcial, completado alucinado, aplicación errónea de acción, desbordamiento de contexto, desconexión entre razonamiento y acción, bucles infinitos | La propiedad que los une y que las otras dos no subrayan: **todos dejan los detectores en verde**. Es la clase de fallo contra la que un plan de verificación sirve de menos | No es una taxonomía publicada ni tiene prevalencias. Se usa como lista de comprobación, no como rejilla |

**Las prevalencias de MAST son de otros sistemas, no del nuestro.** Repetición de
pasos 15,7 %, no reconocer condiciones de terminación 12,4 %, desobedecer la
especificación 11,8 %, pérdida de historial 2,8 %, actuar fuera de rol 1,5 %.
Sirven para ordenar por dónde empezar a mirar, no para afirmar nada sobre esta
implementación: **aquí no se ha medido ninguna**, y no las hay porque no hay
sistema que medir. **Caduca con:** `backend/`.

ConStory-Bench mide **densidad de errores por diez mil palabras**. Es una métrica
que no tenemos y que conviene adoptar cuando haya texto: sin denominador, contar
hallazgos no dice si la obra mejora o solo se alarga. **Caduca con:** `backend/`.

## Cómo leer la tabla

Un modo entra **solo si se puede escribir cómo se manifestaría en una novela de
terror generada por este sistema**. *Alucinación* no es un modo de fallo, es una
categoría; *el delta declara un movimiento que el texto no narra* sí lo es.

La columna de validador se deja **vacía cuando no hay ninguno**. Un hueco marcado
vale más que una fila rellenada por compromiso, y los huecos son el resultado
útil de esta sección.

### A · Diseño del sistema

| ID | En qué consiste | Cómo se manifestaría aquí | Detecta |
| --- | --- | --- | --- |
| **MF-01** | Desobedecer la especificación de la tarea (11,8 % en MAST) | La escaleta asigna a la escena 7 un `pov` en tercera limitada y `tiempo_verbal` pasado; el Escritor devuelve la escena en presente y con narrador omnisciente | `INV-04` solo comprueba que el POV **no cambie dentro** de la escena. **Nadie compara el POV y el tiempo verbal generados con los que la escaleta asignó** |
| **MF-02** | Actuar fuera del rol asignado (1,5 %) | El Juez, en vez de devolver puntuación y hallazgos, devuelve la escena reescrita "mejorada" | `VER-27` |
| **MF-03** | Repetición de pasos (15,7 %, el más prevalente) | La escena 3 gira entre `rechazada` y `generada` sin converger: el Escritor insiste en devolverla sin `cambio_de_valor` y nadie para el bucle | `VER-43` |
| **MF-04** | El mismo paso se ejecuta dos veces por reanudación | El worker muere después de llamar al modelo y antes de registrar el resultado; al reanudar vuelve a llamar, se paga dos veces y sale una escena distinta de la que ya existía | — `VER-04` comprueba que el trabajo **sobrevive**, no que se ejecute **una sola vez** |
| **MF-05** | Pérdida de historial (2,8 %) | El contexto no cabe y el recorte se lleva las fichas de entidad; el Escritor describe a Marta sin tener su ficha delante | **Prevenido para el caso grave**: el orden de `SPEC-01` §2.4 pone el registro de conocimiento en cuarta posición, así que `RF-26` hace fallar el trabajo antes de que el recorte llegue a él y deje a `INV-03` sin datos. Lo que sí se sigue perdiendo son fichas y setups, que es `PC-9` |
| **MF-06** | No reconocer las condiciones de terminación (12,4 %) | El Escaletador sigue planificando escenas después del clímax, o el Auditor no detecta que la obra ya cerró sus arcos | `INV-12` es de nivel obra y queda fuera de la v1 |

### B · Desalineación entre agentes

| ID | En qué consiste | Cómo se manifestaría aquí | Detecta |
| --- | --- | --- | --- |
| **MF-07** | Rellenar el hueco en vez de pedir aclaración | El recorte deja fuera la ficha de Marta; el Escritor le inventa unos rasgos físicos y se los atribuye. En el capítulo siete tendrá otros | — Nada falla en el momento. `INV-06` lo vería al final, y es de nivel obra |
| **MF-08** | Descarrilamiento de la tarea | Se pide una escena de transición con un `cambio_de_valor` previsto de conocimiento; el Escritor entrega el clímax, con un cambio de valor en el eje de vida | — **Nadie compara el cambio de valor previsto en la escaleta con el que declara el delta.** `INV-01` solo comprueba que no sea nulo |
| **MF-09** | Retención de información entre agentes | El Juez detecta un problema, lo menciona en su puntuación y no emite el `Hallazgo` correspondiente; la escena avanza sin rastro | — Una puntuación con la lista de hallazgos vacía es esquema válido. `VER-40` detecta que el Juez **no funciona**, no que se calle algo |
| **MF-10** | Ignorar la aportación de otro agente | El Consolidador aplica el delta con un hallazgo `bloqueante` abierto de la puerta anterior | `VER-10`, `VER-11` |
| **MF-11** | Desconexión entre razonamiento y acción | El texto narra que Marta sale de la casa por la ventana; el delta que acompaña no registra el movimiento. El estado del mundo la deja dentro y la escena siguiente la hace hablar en la cocina | `VER-39` **parcialmente**: caza el delta que habla de quien no aparece, no el que se calla lo que sí ocurre |

### C · Verificación de tareas

Es la categoría donde MAST más insiste, y la que este documento ya tenía como
eje: *"los agentes verificadores hacen comprobaciones superficiales"*.

| ID | En qué consiste | Cómo se manifestaría aquí | Detecta |
| --- | --- | --- | --- |
| **MF-12** | Terminación prematura | El trabajo se marca completado con la escena en `generada`, sin haber pasado la puerta | `VER-28` sobre el modelo declarado. Una ruta que escriba el estado directamente en la base no la ve nadie: es `PC-1` |
| **MF-13** | Verificación nula por clasificación errónea de la propia regla | `INV-01` está implementada como `mayor` en vez de `bloqueante`; la escena sin cambio de valor avanza y tres validadores están en verde | `VER-38` |
| **MF-14** | Verificación incorrecta por salida válida y vacía | El Juez devuelve una lista de hallazgos vacía por un timeout mal capturado, y se lee como "todo bien" | `VER-40` |

### D · Consistencia narrativa (ConStory-Bench)

Aquí el fallo es **del producto**, no del sistema, así que quien detecta es casi
siempre una invariante de `Docs/definitions.md` y no una fila `VER`.

| ID | Categoría | Cómo se manifestaría aquí | Detecta |
| --- | --- | --- | --- |
| **MF-15** | Cronología y trama | La escena 12 narra el hallazgo del cuerpo; la escena 9, anterior en discurso y posterior en fábula, describe a la víctima viva sin que la analepsis esté declarada | `INV-08`, de nivel capítulo y fuera de la v1 |
| **MF-16** | Caracterización | Marta pierde sus muletillas y su sintaxis y pasa a hablar como los demás personajes a partir del capítulo cinco | — `INV-15` mide la deriva **global** frente a las anclas de estilo. **No hay ninguna invariante de voz por personaje** |
| **MF-17** | Construcción de mundo | La casa tenía una sola salida en la escena 4 y en la 11 aparece una puerta trasera que nadie plantó | — `EstadoDelMundo` guarda ubicaciones y posesiones, **no la topología de un lugar**. `INV-06` solo actúa si alguien lo declaró como `HechoCanonico` |
| **MF-18** | Factual | El texto dice que Marta coge el cuchillo y el delta registra que lo coge Luis | — `VER-39` no lo ve: los dos nombres aparecen en el texto. Es exactamente `PC-5` |
| **MF-19** | Estilo narrativo | La prosa se aplana hacia la media del modelo: frases de longitud uniforme, menos densidad sensorial, el registro de terror se diluye | `INV-15`, **cuando tenga umbral**. Hoy es `VER-32`, no verificable |

**Las cuatro observaciones metodológicas de ConStory-Bench son más útiles que su
taxonomía**, y ninguna está aprovechada todavía:

- **Los errores se concentran hacia la mitad de la narración.** Si hay que
  muestrear para una revisión cara, el centro rinde más que los extremos.
- **Aparecen en segmentos de mayor entropía por token.** Es una **señal lateral
  barata**: se puede calcular sin juez y sin leer, y apunta dónde mirar.
- **Ciertos tipos co-ocurren.** Encontrar uno es razón para buscar su pareja, no
  para dar la escena por revisada.
- **Los factuales y temporales dominan.** Son también los dos que más se prestan
  a comprobación determinista, que es una coincidencia afortunada.

### E · Fallos silenciosos de producción

Lo que los une: **todos dejan los detectores en verde**.

| ID | En qué consiste | Cómo se manifestaría aquí | Detecta |
| --- | --- | --- | --- |
| **MF-20** | Completado parcial | El Consolidador aplica tres de las cinco entradas del delta, falla en la cuarta sin transacción, y la escena queda `consolidada` con el estado a medias | `VER-42` |
| **MF-21** | Completado alucinado | El Resumidor devuelve un resumen bien formado que menciona un hecho que la escena no contiene. Ese resumen entra en el contexto de las escenas siguientes como si fuera canon | — `VER-39` compara el **delta** con el texto, no el **resumen** con la escena |
| **MF-22** | Desbordamiento de contexto | El contador del ensamblador dice 98.000 y el del proveedor 102.000; la llamada se rechaza, o peor, se trunca por el final sin avisar | `VER-05` con referencia externa (Regla 3) y `VER-41` |
| **MF-23** | **Falso positivo del validador** | `VER-46` marca como defecto la prosa de este documento que explica el defecto, porque no distingue una cita de una demostración | — Es el validador el que falla, y **ningún validador vigila a los validadores**. Ya ocurrió: ver "Lo que se aprendió al implementar", F-15 |
| **MF-24** | **Criterio de salida colgante**: un validador cuyo criterio remite a algo que no está escrito en ninguna parte. No falla, no avisa, y **cuenta como cobertura** | `VER-06` decía *"el orden de recorte respeta la prioridad declarada"* y esa prioridad no estaba declarada en ningún documento. `VER-23` dice *"el conjunto de identificadores solo crece"* sin decir **respecto a qué**, así que el criterio lo eligió quien lo implementó | — Ver `PC-13`. Es hermano de `MF-23` y su contrario exacto: aquel es el validador que marca lo correcto, este es el que **no puede marcar nada** |

## Estado de los nueve modos que no tenían cobertura

**Ninguno se queda sin estado.** Un modo no cubierto y no reconocido es el peor
de los tres estados posibles, así que cada uno acaba como fila `VER` o como punto
ciego asumido. El criterio: si admite comprobación determinista razonable, es
validador; si solo se puede mirar con un juez caro, es punto ciego.

| Modo | Estado | Con qué |
| --- | --- | --- |
| **MF-01** | **Validador** | `VER-47` compara el `pov_usado` declarado con el asignado; `VER-48` comprueba que el texto lo honre |
| **MF-04** | **Validador** | `VER-49`, idempotencia por intento registrado |
| **MF-07** | **Punto ciego** | `PC-9`: distinguir "lo sabía" de "se lo inventó" exige un juez. La traza registra qué fichas se recortaron, que acota el daño |
| **MF-08** | **Validador** | `VER-47` (b), desde que `SPEC-03` puso `cambio_de_valor` en el delta. Ver abajo |
| **MF-09** | **Validador** | `VER-50`, coherencia entre puntuación y hallazgos |
| **MF-16** | **Validador** | `VER-51`, deriva de voz por personaje |
| **MF-17** | **Validador** | `VER-54`, desde que `SPEC-03` convirtió los accesos de un `Lugar` en referencias. `PC-10` queda cerrado |
| **MF-21** | **Validador** | `VER-53`, desde que `SPEC-03` convirtió `hechos_clave` en identificadores. `PC-11` queda cerrado |
| **MF-23** | **Punto ciego** | `PC-12`, y no se resuelve con una capa que vigile validadores |

### `MF-08` resistió, y lo que lo destrabó fue cambiar el dominio

Durante un tiempo fue el único modo que no cabía ni en validador ni en punto
ciego, y el motivo no estaba en la verificación: **`DeltaDeEscena` declaraba
muertes, movimientos, revelaciones, setups pagados, cambios de posesión y
deterioros, y nada más.** Sin `cambio_de_valor` en el delta no había contra qué
comparar lo que la escaleta pidió.

`SPEC-03` lo resolvió por la raíz, y de paso dejó tres cosas que conviene
retener:

- **La persona narrativa y el tiempo verbal no fueron al delta.** El delta es el
  diff del mundo y la superficie del texto no cambia el mundo: `pov_usado` vive
  en `Borrador`, junto a `modelo` y `prompt_hash`.
- **La correspondencia entre ejes y campos del delta contrasta, no deriva.**
  Ningún campo del delta lleva signo y cuatro de los seis ejes solo tienen campo
  para uno, así que el eje se declara y la tabla lo comprueba. Si se pudiera
  derivar, la comprobación sería el propio dato mirándose al espejo: la Regla 3
  otra vez.
- **Quedaron dos huecos del modelo escritos en `Docs/definitions.md`**:
  sobrevivir no deja rastro, y olvidar o descubrir que lo que sabías era falso no
  tiene campo. Son cosas que la novela puede hacer y el sistema no puede
  representar.

### Los tres parciales que conviene no dar por cubiertos

**MF-05** se detecta tarde y con la llamada ya pagada. **MF-11** y **MF-18** los
estrecha `VER-39` sin cerrarlos, que es lo que dice `PC-5`.

## Lo que tenemos y las taxonomías publicadas no

Cuatro modos que ninguna de las tres rejillas recoge, y salen de decisiones de
arquitectura propias:

1. **El delta como fuente de verdad divergiendo del texto** (`MF-11`, `MF-18`).
   MAST tiene *desconexión entre razonamiento y acción*, pero ahí el desajuste
   muere con el turno. Aquí el delta **se consolida en el estado del mundo** y
   contamina todas las escenas siguientes. Es la diferencia entre un error y un
   error que hereda.
2. **El recorte de contexto como causa de un fallo de dominio** (`MF-05`). MAST
   tiene *pérdida de historial*, pero como accidente. Aquí el recorte es una
   **decisión de diseño con un orden de prioridad declarado**, así que el fallo
   es predecible y atribuible a una regla concreta.
3. **La clasificación de la propia regla como modo de fallo** (`MF-13`). MAST
   habla de verificación incorrecta; esto es anterior: la regla está bien
   ejecutada y **mal etiquetada**.
4. **El falso positivo del validador** (`MF-23`). Las tres rejillas miran fallos
   del sistema que genera. Ninguna mira fallos de la capa que verifica, y esa
   capa también falla: aquí ya lo hizo.

## Relación con los puntos ciegos

**Un punto ciego es un modo de fallo que sabemos que no vemos.** Las dos listas
no se duplican: `MF-xx` dice **qué puede salir mal**; `PC-xx` dice **qué parte de
eso hemos decidido no mirar, y por qué**. Se apuntan entre sí:

| Punto ciego | Modo de fallo al que corresponde |
| --- | --- |
| `PC-1` — el análisis estático no ve la ejecución | `MF-12`: la terminación prematura por una ruta que escribe el estado a mano |
| `PC-2` — nadie comprueba que quien acepta sea una persona | No tiene `MF` propio porque no es un fallo del sistema sino de su uso. **Es el único `PC` sin modo asociado** |
| `PC-3` — la fiabilidad del Juez no está medida | `MF-09` y `MF-14`: lo que el Juez calla y lo que devuelve vacío |
| `PC-4` — los resúmenes pueden crecer hasta reconstruir la obra | Adyacente a `MF-21`: el mismo agente, un fallo de tamaño en vez de contenido |
| `PC-5` — la comprobación de menciones es léxica, no semántica | `MF-11` y `MF-18`, que son su enunciado en positivo |
| `PC-6` — el identificador del hallazgo existe pero puede ser el equivocado | Adyacente a `MF-13`: los dos son metadatos de la regla, no su ejecución |
| `PC-7` — la migración existe pero puede estar vacía | Sin `MF`: es un fallo del proceso de cambio, no de la ejecución del sistema |
| `PC-8` — el contador se valida contra el proveedor, no contra la verdad | `MF-22` |
| `PC-9` — nadie ve la invención que rellena un recorte | `MF-07` |
| ~~`PC-10`~~ — cerrado por `SPEC-03` | `MF-17`, ahora cubierto por `VER-54` |
| ~~`PC-11`~~ — cerrado por `SPEC-03` | `MF-21`, ahora cubierto por `VER-53` |
| `PC-12` — nadie vigila a los validadores | `MF-23` |
| `PC-13` — un criterio puede remitir a algo que no existe | `MF-24`, **materializado**: ver `F-16` |

Tres lecturas útiles de esa tabla. **`PC-2` y `PC-7` no tienen modo de fallo
asociado** porque no son fallos del sistema en marcha: uno es de uso y otro de
proceso. **Los cuatro puntos ciegos nuevos sí lo tienen**, porque nacieron
precisamente de cerrar modos que no estaban ni cubiertos ni reconocidos. Y **ya
no queda ningún modo sin estado**: los veintitrés acaban en validador o en punto
ciego, salvo el núcleo de `MF-08`, que está bloqueado por una decisión de
dominio y consta como tal.

## Relación con lo que se aprendió al implementar

Varios de los quince hallazgos son **instancias concretas de modos genéricos**, y
conviene que se apunten entre sí en vez de leerse como anécdotas:

| Hallazgo | Modo del que es un caso |
| --- | --- |
| `F-15` — los validadores prohíben citar el defecto | `MF-23`, y es su única instancia observada |
| `F-1` — `VER-38` no puede contrastar la severidad | `MF-13`: la clasificación de la regla es verificable a medias |
| `F-8` — `VER-23` se salta en vez de fallar cuando no hay historial | `MF-14`: un validador que aparece en verde sin haber comprobado nada es verificación incorrecta, y aquí el que la sufre es el propio harness |
| `F-12` — `VER-44` estaba quemado y `VER-23` no lo habría cazado | `MF-14` otra vez, en su forma más incómoda: el validador declaró su punto ciego y el punto ciego se materializó |
| `F-9` — no se pudo comprobar que el nivel del agente cuadre con el de la invariante | `MF-06`: el Auditor no sabe cuándo le toca, porque nadie declara su nivel |
| `F-13` — la columna "Dónde vive" es un plan y el documento no lo dice | `MF-01` aplicado a la documentación: el documento incumple su propia especificación implícita |

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
libro son los validadores ciegos a la ejecución: hay **doce**, los que lista
`PC-1`, y comparten el mismo límite, así que el decimotercero no taparía nada.
Un validador que no puede
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
| **Modos de fallo catalogados** | **24** (`MF-01`…`MF-24`), ninguno sin estado y dos sin validador por construcción |
| **Validadores definidos** | **55** (`VER-01`…`VER-56`, con `VER-44` quemado: ver `PC-4`) |
| **De ellos, no verificables hoy** | 6 (`VER-32`…`VER-37`) |
| **Validadores implementados** | **0** |
| **Escritos y retirados a modo de prueba** | 5 — `VER-23`, `VER-28`, `VER-38`, `VER-45`, `VER-46` |
| **Bloqueados por falta de código de producción** | 43 |
| **Implementables hoy y sin implementar** | 1 — `VER-56`, que solo necesita los documentos y el repositorio |
| **Puntos ciegos asumidos** | **11 activos**, más `PC-10` y `PC-11` cerrados por `SPEC-03` |

**Caduca con:** `backend/` — los recuentos de esta tabla y los dos párrafos siguientes
dejan de ser ciertos el día que exista esa carpeta.

**Cero implementados, y conviene decirlo en voz alta: una lista más larga no es
más cobertura.** Este documento ha pasado de 37 filas a 55 y la cifra que mide
fiabilidad sigue siendo cero. Cuarenta y tres esperan a `backend/`, `frontend/` o
CI, seis esperan una medición o una decisión, y **una —`VER-56`— no espera a nada**: solo
necesita los documentos y el repositorio, que ya existen.

Lo que sí ha cambiado son dos cosas. **Ya no hay ningún modo de fallo sin
estado**: antes había nueve que no estaban ni cubiertos ni reconocidos, que es el
peor de los tres porque no aparece en ninguna lista. Y **`SPEC-03` cerró dos
puntos ciegos cambiando el dominio en vez de añadir validadores**: cuando el dato
deja de ser prosa y pasa a ser una referencia, la comprobación deja de ser léxica
y empieza a tener punto ciego propio, que es lo que la Regla 2 exige para
admitirla.

Cinco se escribieron de verdad, con su caso negativo, para comprobar si el
documento aguantaba al llevarlo a código, y se retiraron después: la entrega de
esta fase es este documento y la spec del backend. **Lo que se aprendió
escribiéndolos está recogido más abajo**, porque es lo único que no se
reconstruye releyendo.

**`VER-45` y `VER-46` existen porque eran las dos únicas clases de defecto con
historial real en este repositorio** —setenta y tres referencias rotas tras dos
renombrados, y el diagrama de ciclo de vida con los estados en PascalCase— y
cuarenta y tres validadores no cubrían ninguna de las dos.

## Semilla de contexto

| Documento | Qué afirmaciones aporta |
| --- | --- |
| `CLAUDE.md` | Stack, presupuesto de 100.000 tokens y su reparto, reglas de Pydantic y enumeraciones, reglas de persistencia |
| `AGENTS.md` | Precedencia entre documentos, reglas de uso del modelo de dominio, estabilidad de identificadores |
| `Docs/definitions.md` | Las dieciséis invariantes con su nivel y severidad, los vocabularios controlados, la política de casos negativos |
| `Docs/domain-knowledge.md` | La máquina de estados de la escena y la secuencia de generación |
| `Docs/architecture.md` | Reglas de dependencia entre features, contrato de los agentes, cola de trabajos, reglas de presentación del frontend, y **la estructura de carpetas contra la que `VER-45` resuelve las rutas** |
| `specs/SPEC - Backend.md` | El orden de recorte de §2.4 y el límite de `RF-26`, de los que dependen `VER-06` y el estado de `MF-05`; §2.5, que sostiene `PC-2`; y §2.2.1, que es el caso negativo de `VER-46` |

Si la semilla cambia, este plan cambia. Una fila cuyo origen desaparezca del
documento de partida se marca obsoleta, no se borra.

---

## Nivel artefacto — ¿es correcto el código?

Ninguna fila lleva columna de estado: **todas están pendientes**. Ver "Estado de
implantación".

| ID | Afirmación | Clase | Metodología | Criterio de salida | **Punto ciego** | Dónde vive |
| --- | --- | --- | --- | --- | --- | --- |
| VER-01 | Los esquemas Pydantic y las fichas de clase de `Docs/definitions.md` tienen exactamente los mismos campos, **en los dos sentidos** | A | static analysis | El comprobador recorre los esquemas contra las fichas y las fichas contra los esquemas: cero campos de más y cero campos de menos | Ve **nombres**, no tipos ni valores: un campo `severidad: str` donde debería haber un `Enum` pasa | `commons/dominio/tests/` |
| VER-02 | Un valor fuera de un vocabulario controlado es error de validación, y **cada `Enum` tiene exactamente los valores de su tabla** | T | unit testing | Cada enumeración rechaza un valor inventado, **y** su número de miembros coincide con el de la tabla de vocabularios | Compara cardinalidad y pertenencia, no **uso**: un campo tipado `str` que nunca toca el `Enum` pasa | `commons/dominio/tests/` |
| VER-03 | El endpoint de generación no bloquea: devuelve un identificador de trabajo | T | integration testing | La respuesta llega antes de que termine la generación y trae un identificador consultable | No comprueba que el trabajo **llegue a ejecutarse**: un worker parado deja `202` y trabajos eternos | `features/generacion/tests/` |
| VER-04 | Un trabajo encolado sobrevive a un reinicio del servidor | T | integration testing | Se encola, se mata el proceso, se levanta, y el trabajo sigue ahí y se completa | **No comprueba unicidad**: el trabajo puede completarse habiendo llamado al modelo dos veces | `commons/trabajos/tests/` |
| VER-05 | Ninguna llamada al modelo supera los 100.000 tokens, salida incluida, **medido con un contador independiente del ensamblador** | T | property-based testing | El contexto ensamblado más la reserva de salida cabe en el límite **según el `usage` que devuelve el modelo o un segundo tokenizador**, no según el contador de producción (Regla 3) | Mide el **techo**, no el **contenido**: un contexto de 3.000 tokens que dejó fuera al protagonista pasa | `features/contexto/tests/` |
| VER-06 | Cuando no cabe, se recorta en el orden declarado, y por debajo del **tercer bloque** se falla en vez de generar | T | property-based testing | Ningún recorte parte un bloque; el orden es el de las filas de `SPEC-01` §2.4 —condensaciones, fichas y setups, escena anterior— y si aún no cabe, el trabajo falla sin tocar el bloque 4.º (**estado del mundo y registro de conocimiento**), la reserva de salida ni el nivel inmutable. **El caso negativo obligatorio es el recortador que itera por niveles de `CLAUDE.md` en vez de por bloques**: se lleva el registro de conocimiento con las fichas y deja `INV-03` sin datos | Comprueba que el **orden** se respeta, no que lo que queda **baste**: un contexto recortado correctamente, que conserva el estado y el registro de conocimiento pero se quedó sin la ficha del protagonista, pasa. Eso es `PC-9` | `features/contexto/tests/` |
| VER-07 | Nunca se manda el texto completo de la obra al modelo | T | unit testing | Con una obra de muchas escenas, el contexto no contiene el texto de ninguna escena salvo la anterior | Mira **texto de escena**, no **volumen equivalente**: resúmenes que crecen hasta reconstruir la obra pasan | `features/contexto/tests/` |
| VER-08 | El texto completo de una escena se guarda pero no se recupera por similitud | T | integration testing | La búsqueda vectorial solo devuelve fichas, resúmenes y presagios | Comprueba el **índice**, no el **camino de lectura**: leer el texto por clave primaria lo esquiva *(lo cubre `VER-07`)* | `commons/db/tests/` |
| VER-09 | El estado del mundo se reconstruye acumulando deltas en orden, **contrastado con una implementación de referencia** | T | property-based testing | Reconstruir con el aplicador de producción y con un **aplicador de referencia ingenuo escrito solo para la prueba** da el mismo estado (Regla 3) | Comprueba que el estado **se construye bien desde el delta**, no que el **delta sea cierto** *(lo cubre parcialmente `VER-39`)* | `features/consolidacion/tests/` |
| VER-10 | Ninguna escena pasa a `consolidada` sin su delta aplicado (`INV-05`) | T | unit testing | Intentar consolidar sin delta aplicado falla; la escena siguiente no se puede generar | Comprueba que el delta **se aplicó**, no que se aplicara **entero** *(lo cubre `VER-42`)* | `features/consolidacion/tests/` |
| VER-11 | `bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y dejan seguir, y un `mayor` abierto impide cerrar el capítulo | T | unit testing | Un hallazgo de cada severidad produce exactamente el comportamiento declarado, **incluida la diferencia entre `mayor` y `menor` en la puerta de cierre de capítulo** (`SPEC-04` C-2) | Comprueba el comportamiento **dada** una severidad, no que la **asignada sea la correcta** *(lo cubre `VER-38`)* | `commons/invariantes/tests/` |
| VER-12 | Todo hallazgo cita su invariante **y el verificador que lo levantó**, los dos por identificador y nunca por descripción | A | static analysis | Todo `Hallazgo` construido lleva un identificador del registro `INV-xx` **y un `verificador` no vacío**. En las invariantes que comprueba más de un agente —`INV-13`, incremental y de barrido— dos hallazgos de la misma invariante levantados por agentes distintos tienen `verificador` distinto | Comprueba que los dos ids **existen** y que **se distinguen entre sí**, no que sean los **correctos**: un verificador copiado que no cambió ninguno de los dos sigue pasando | `commons/invariantes/` |
| VER-13 | Una feature nunca importa de otra feature, salvo `orquestacion/` | A | static analysis | El comprobador de importaciones falla el build ante cualquier import cruzado no autorizado | Estático: no ve importación dinámica ni acoplamiento por datos compartidos | CI |
| VER-14 | `commons/` nunca importa de una feature | A | static analysis | Mismo comprobador; la flecha va en un solo sentido | El mismo que `VER-13` | CI |
| VER-15 | Los `Enum` de los vocabularios controlados viven solo en `commons/dominio/` | A | static analysis | No hay ninguna definición de `Enum` de dominio fuera de esa carpeta | **Sin punto ciego relevante**: regla estructural sobre artefacto estático. El único escape sería crear un `Enum` en tiempo de ejecución a propósito | CI |
| VER-16 | El frontend nunca accede a la base de datos ni calcula estado de dominio | A | static analysis | El frontend no depende de ningún cliente de base de datos | Comprueba **dependencias**, no **lógica**: deducir el estado de una escena a partir de campos sueltos pasa | CI |
| VER-17 | Un módulo del frontend solo importa de capas FSD estrictamente inferiores | A | static analysis | El comprobador de FSD pasa sin violaciones | Comprueba **capas**, no **responsabilidades**: lógica de negocio dentro de `shared/` pasa | CI |
| VER-18 | Una escena nunca se muestra sin su estado y sus hallazgos abiertos | T | unit testing | El componente no renderiza texto si falta el estado o la lista de hallazgos | Comprueba el **componente**, no la **API**; y presencia, no que sean los de estado `abierto` | `frontend/.../tests/` |
| VER-19 | Un dato sin medir se muestra "sin medir", nunca como cero | T | unit testing | Con el valor ausente la interfaz pinta "sin medir"; con cero, pinta cero | Comprueba la **presentación**, no el **origen**: si el backend devuelve `0` donde no midió, la interfaz acierta y el dato miente | `frontend/.../tests/` |
| VER-20 | El Escritor devuelve texto y delta en la misma respuesta | T | contract testing | Una respuesta sin delta, o con delta fuera de esquema, se rechaza sin llegar a las puertas | Comprueba **forma**, no **correspondencia con el texto** *(lo cubre parcialmente `VER-39`)* | `features/generacion/tests/` |
| VER-21 | Todo cambio de un atributo obligatorio en `Docs/definitions.md` lleva su migración en el mismo commit | A | CI/CD integration | Un commit que toque un atributo obligatorio sin añadir migración falla en CI | Comprueba que la migración **existe**, no que sea **correcta**: una migración vacía pasa | CI |
| VER-22 | Cada invariante `INV-01`…`INV-16` tiene un caso negativo **que de verdad la caza** | A | mutation testing | **Se desactiva la comprobación de la invariante y su caso negativo tiene que fallar.** Si sigue pasando, el caso no estaba probando nada | Prueba la **eficacia del caso**, no su **representatividad**: un solo caso negativo no cubre todas las formas de violar la invariante | CI |
| VER-23 | Ningún identificador publicado se reutiliza ni se renumera | A | static analysis | El conjunto de identificadores solo crece; lo retirado queda marcado obsoleto | Ve el **conjunto**, no el **significado**: cambiar el enunciado de `INV-14` manteniendo el número pasa | CI |
| **VER-38** | La severidad, el nivel y el tipo declarados en el código para cada invariante coinciden con la tabla de `Docs/definitions.md` | A | static analysis | Se parsea la tabla de invariantes y se compara con el registro de `commons/invariantes/`: identificador, nivel, severidad y tipo, los cuatro iguales | Compara **declaración contra declaración**: no comprueba que el verificador respete la severidad que declara *(lo cubre `VER-11`)* | `commons/invariantes/tests/` |
| **VER-39** | Toda entidad que el delta declara aparece mencionada en el texto de la escena, y todo personaje mencionado está en `personajes_presentes[]` | T | contract testing | Por cada entrada del delta, su `nombre_canonico` o algún `alias` aparece en el texto; y ningún nombre del texto queda fuera de `personajes_presentes[]` | **Compara superficie léxica, no sentido**: un delta equivocado sobre alguien que **sí** está mencionado pasa | `features/consolidacion/tests/` |
| **VER-42** | Aplicar un delta es atómico: o entran todas sus entradas o ninguna | T | integration testing | Se fuerza un fallo a mitad de la aplicación y el estado queda exactamente como antes; el número de cambios aplicados coincide con el de entradas del delta | Cuenta **entradas aplicadas**, no la **corrección de cada una** *(lo cubre parcialmente `VER-39`)* | `features/consolidacion/tests/` |
| **VER-43** | Una escena no supera un número acotado de ciclos de regeneración | T | unit testing | Con un tope configurado, la escena número `tope+1` se detiene y se marca en vez de volver a generarse. **El valor del tope sale de medir, no se fija aquí** | Cuenta **ciclos**, no **diagnostica la causa**: detecta que gira, no por qué | `features/orquestacion/tests/` |
| **VER-45** | Toda ruta citada en un documento **existe tal cual está escrita, o encaja en la estructura declarada de `Docs/architecture.md`** | A | static analysis | Se recorren las rutas entre acentos graves de todos los documentos del proyecto. Cada una existe en disco **o** corresponde a una carpeta del árbol de `Docs/architecture.md`, resuelta contra su raíz declarada `backend/app/`. Cero rutas que no cumplan ninguna de las dos. Se eximen solo las ignoradas por git | Ve **existencia y forma**, no **corrección**: una ruta que existe, o que encaja en el árbol, pero que no es donde vive de verdad ese test, pasa igual. Y sigue sin comprobar que el documento citado diga lo que el citante cree | `harness/documentos/` |
| **VER-46** | Todo literal de enumeración citado en un documento se escribe como en la tabla de `Docs/definitions.md` | A | static analysis | Se normalizan los tokens con forma de identificador —minúsculas, sin tildes, sin guiones bajos— y se comparan con los valores de la tabla: si dos normalizan igual y se escriben distinto, es una variante | No ve los valores que son **palabras sueltas y comunes** (`obra`, `escena`, `regla`, `vivo`): comprobarlas daría ruido sin señal, así que `nivel_de_evaluacion`, `severidad` y `tipo_de_verificador` quedan fuera de alcance | `harness/documentos/` |
| **VER-56** | Ninguna afirmación marcada con una condición de caducidad tiene su condición ya cumplida | A | static analysis | Se recorren las marcas `Caduca con:` de todos los documentos. Para cada una, la ruta **no** existe en disco, o la sección citada sigue diciendo lo que la marca supone. Cero marcas con su condición cumplida. **Falla el build**: un aviso que nadie mira es el mismo problema con otra cara | **Ve la condición, no el argumento.** Que `backend/` no exista no garantiza que la afirmación siga siendo cierta por el motivo que declara. Y **no detecta una afirmación condicional sin marcar**, que sigue siendo lectura humana: es `PC-13` | `harness/documentos/` |
| **VER-47** | La escena entregada es la que la escaleta pidió | T | contract testing | Tres comparaciones, las tres exactas: **(a)** toda entidad que el delta toca está entre los `personajes_presentes` declarados; **(b)** el `cambio_de_valor` del delta es el que la escaleta previó, par `{eje, signo}` contra par; **(c)** el `pov_usado` del borrador coincide en `persona` y `tiempo_verbal` con el `pov` asignado | Compara **lo que el agente declara**, no lo que el texto hace. Un Escritor que declare el POV correcto y escriba otro pasa: para eso está `VER-48` | `features/generacion/tests/` |
| **VER-53** | Todo hecho que un resumen cita fue establecido o revelado en la escena que resume | T | contract testing | `Resumen.hechos_clave` es una lista de identificadores de `HechoCanonico`: la intersección con los que la escena estableció o reveló tiene que ser total | Ve **identificadores citados**, no un resumen que **parafrasee** un hecho sin citarlo. Ese punto ciego es distinto del léxico de `VER-39`, que es lo que permitió admitirlo | `features/consolidacion/tests/` |
| **VER-54** | Los accesos de un `Lugar` no cambian sin que un `HechoCanonico` lo establezca | T | integration testing | `Lugar.accesos_y_salidas` es una lista de referencias: cualquier diferencia entre dos momentos `t` exige un `HechoCanonico` con su `escena_de_establecimiento` | Ve el **conjunto declarado**, no el texto: una puerta que la prosa describe y que nadie declaró sigue sin verse | `features/consolidacion/tests/` |
| **VER-49** | Un trabajo produce como máximo una llamada al modelo por intento registrado | T | integration testing | El intento se registra **antes** de llamar; al reanudar tras un reinicio, un intento ya registrado no vuelve a llamar. Se cuenta llamadas por `(trabajo, intento)` y nunca hay dos | Depende de que el registro **preceda** a la llamada. Si alguien invierte el orden, el validador deja de ver justo el caso que existe para cazar | `commons/trabajos/tests/` |
| **VER-52** | Todo recuento de hallazgos se expresa también como densidad por diez mil palabras | T | unit testing | Ninguna respuesta de la API que devuelva un recuento de hallazgos lo hace sin su densidad al lado | Normaliza por **longitud**, no por **dificultad**: un capítulo de acción y uno de transición no son comparables aunque tengan la misma densidad | `features/lectura/tests/` |

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
| VER-29 | Ninguna ruta del worker lleva una escena a `aceptada` **ni un capítulo a `cerrado`** | A | static analysis | El worker no tiene ninguna ruta de código que produzca ninguna de las dos transiciones, **ni ninguna que devuelva un capítulo de `cerrado` a `abierto`** (`RF-30`: esa transición no existe) | Comprueba que **el worker no puede**, no que quien firma sea **una persona**: sin autenticación, un script llama al endpoint igual. Vale para las dos puertas | `features/orquestacion/tests/` |
| VER-30 | El Escritor no viola las reglas de la amenaza bajo los prompts adversarios del corpus | T | red-teaming / adversarial testing | El corpus adversario se ejecuta en CI y ningún caso conocido vuelve a fallar | Cubre lo que **ya está en el corpus**: no inventa ataques nuevos, para eso sigue haciendo falta una persona | `harness/adversarial/` |
| VER-31 | Los cambios generados por agente pasan por la misma tubería que los escritos a mano | A | CI/CD integration | No hay ninguna ruta que publique cambios saltándose CI | Comprueba que **se pasa** por CI, no que CI **compruebe algo útil** | CI |
| **VER-40** | El Juez caza el defecto conocido del canario en cada lote de verificación | T | guardrails | Cada lote incluye una escena con un defecto plantado; si el Juez no lo señala, el lote se marca como no fiable | Detecta que el Juez **funciona**, no que **acierte**. Y un canario fijo puede acabar acertándose por memorización | `harness/evals/` |
| **VER-41** | `tokens_estimados` y `tokens_declarados` de la traza coinciden, **y son dos campos con caminos de escritura distintos** | T | runtime observability / tracing | La diferencia entre lo trazado y el `usage` de la respuesta es cero para toda llamada | Valida el contador **contra el proveedor**, no contra la verdad: si el `usage` del proveedor es incorrecto, los dos coinciden en el error | `commons/modelo/` |
| **VER-48** | El texto generado usa de hecho la persona y el tiempo verbal que el borrador declara | T | property-based testing | Señal morfológica sobre el texto —proporción de terminaciones de pasado frente a presente, marcas de primera frente a tercera— **contrastada contra el `pov_usado` que declara el `Borrador`**. Las dos fuentes son independientes: una es el texto, otra la declaración del agente (Regla 3). **La serie se registra desde el primer día; el umbral sale de medirla** | Sigue siendo una **heurística, no un análisis gramatical**: una escena con mucho diálogo en presente dentro de una narración en pasado puede dar falso positivo, y un narrador que cita mucho lo diluye | `features/verificacion/tests/` |
| **VER-55** | Ningún tic prohibido por la `GuiaDeEstilo` aparece en el texto generado | T | unit testing | `tics_prohibidos` es una lista de cadenas literales: ninguna aparece en el texto de ningún borrador | Busca **cadenas exactas**: una variante morfológica del tic —el mismo giro en otro tiempo verbal— no la ve. Es el precio de que la comprobación cueste una línea | `features/verificacion/tests/` |
| **VER-50** | La puntuación del Juez y su lista de hallazgos son coherentes entre sí | T | guardrails | Si la puntuación no es el nivel máximo de su `Rubrica`, la lista de hallazgos no puede estar vacía | **Confía en que la puntuación sea honesta.** Un Juez que puntúa alto y se calla el problema pasa: detecta la incoherencia, no la connivencia | `features/verificacion/tests/` |
| **VER-51** | La deriva de voz se mide **por personaje**, no solo globalmente | T | evals | Las mismas cuatro métricas de estilo —longitud media de frase, ratio de diálogo, densidad de adverbios, riqueza léxica— se calculan agrupadas por hablante, y la **distancia entre personajes** se registra por escena. **El mínimo sale de medir la serie, no se fija aquí** | Depende de **atribuir el diálogo** a su hablante. Un narrador que parafrasea en vez de citar no deja diálogo que medir, y ahí la voz puede derivar sin que nadie la vea | `harness/evals/` |

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
| VER-35 | Cuando el Juez marca `INV-03` y la regla de continuidad no ve nada, gana el correcto | Solo la decisión de quién gana. **Ya no es hipotética**: con `SPEC-04`, `INV-03` es de tipo `regla` y el Juez es su desempate, así que las dos comprobaciones se ejecutan sobre la misma escena y la discrepancia se puede contar desde el primer día | `Docs/definitions.md` → "Desempate juez vs. regla" |
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
| **PC-1** | **Ninguna comprobación que no ejecute el sistema ve la ejecución.** Doce validadores lo comparten —nueve de análisis estático, `VER-28` de *model checking* y `VER-21` y `VER-31` de integración en CI—: `VER-01`, `VER-12`, `VER-13`, `VER-14`, `VER-15`, `VER-16`, `VER-17`, `VER-21`, `VER-23`, `VER-28`, `VER-31`, `VER-38` | Un script de mantenimiento hace `UPDATE escena SET estado='consolidada'` y salta la máquina de estados entera | Taparlo pide auditoría en tiempo de ejecución sobre la base. No es caro, pero no hay base todavía. **Caduca con:** `backend/app/commons/db/` |
| **PC-2** | **Nadie comprueba que quien acepta una escena sea una persona.** `VER-29` solo comprueba que el worker no puede | Un script llama a `POST /escenas/{id}/aceptar` en bucle y consolida la obra entera sin que nadie la lea | `SPEC-01` §2.5 excluye la autenticación de la v1. Sin identidad no hay nada que comprobar. **Caduca con:** `SPEC-01` §2.5 |
| **PC-3** | **La fiabilidad del Juez no está medida**, y `VER-26` en verde significa "se midió", no "es fiable" | Tras `SPEC-04` **ninguna invariante `bloqueante` es de tipo `juez_llm`**: la única que queda del Juez es `INV-10`, de severidad `mayor`. El Juez ya no detiene una escena por sí solo | **Encogido dos veces, no cerrado.** `SPEC-03` hizo escribible la parte determinista de `INV-03`; `SPEC-04` la reclasificó a `regla` y dejó al Juez como desempate. Siguen abiertas dos vías por las que un modelo sin fiabilidad medida decide: **(a)** el desempate de `INV-03` es una decisión abierta, y si el veredicto del Juez cuenta, sigue deteniendo escenas `bloqueante`; **(b)** `SPEC-04` le dio una consecuencia nueva a `mayor`, así que `INV-10` —del Juez— ahora **bloquea el cierre de capítulo**, que es una puerta humana. Esta segunda vía no existía antes: parte del punto ciego encogió y otra parte se movió una puerta más arriba. Cierra cuando `VER-26` y la medida de estabilidad den un número |
| **PC-4** | **Los resúmenes pueden crecer hasta reconstruir la obra.** Se propuso un validador de ratio de compresión —al que `REV-02` llegó a dar el número **`VER-44`**— y **se rechazó por la Regla 2**: su punto ciego, mide longitud y no calidad, ya lo tienen seis validadores. **`VER-44` queda quemado**: el identificador está publicado y no se reutiliza | El Resumidor devuelve resúmenes casi tan largos como la escena. `VER-07` está en verde porque no hay texto de escena en el contexto, y el contexto lleva la obra entera de todos modos | Se asume hasta encontrar una comprobación con un punto ciego propio |
| **PC-5** | **`VER-39` compara léxico, no sentido.** Estrecha `BC-4` —que nada contrasta el delta con el texto— pero **no lo cierra**, y es fácil darlo por resuelto | El delta dice que Marta coge el cuchillo y en el texto lo coge Luis. Los dos nombres están mencionados, así que `VER-39` pasa. El hueco de `BC-4` sigue abierto para todo delta que se equivoque sobre alguien **sí** mencionado | La comprobación semántica exige un juez, y un juez sin fiabilidad medida no mejora esto |
| **PC-6** | **`VER-12` comprueba que el identificador existe, no que sea el correcto** | Se copia un verificador y no se cambia el id: todos los hallazgos salen como `INV-01` y el recuento por invariante miente | `VER-38` valida el registro, no qué id usa cada verificador al construir el hallazgo |
| **PC-7** | **`VER-21` comprueba que la migración existe, no que sea correcta** | Se añade un atributo obligatorio y se commitea una migración vacía. CI verde y la columna no existe | Validar que una migración hace lo que dice exige ejecutarla contra un esquema de referencia |
| **PC-8** | **`VER-41` valida el contador contra el proveedor, no contra la verdad** | El `usage` del proveedor es incorrecto: el contador propio y el del proveedor coinciden en el mismo error | Se acota, no se cierra: **la factura mensual del proveedor es una tercera fuente independiente y es gratis**. No prueba que el `usage` por llamada sea correcto, pero si el total facturado se aleja del total trazado, algo miente. Cuadrar los dos totales una vez al mes cuesta una resta |
| **PC-9** | **Nadie detecta que un agente rellene con invención lo que el recorte dejó fuera** (`MF-07`) | El ensamblador recorta la ficha de Marta; el Escritor le atribuye unos rasgos físicos que nunca estuvieron en el canon. En el capítulo siete tendrá otros | Distinguir *"lo sabía"* de *"se lo inventó"* exige comparar la prosa con la ficha, y eso es un juez. **Lo que sí se hace y acota el daño: la traza de `VER-24` registra qué fichas quedaron fuera**, así que el fallo pasa de invisible a atribuible |
| ~~**PC-10**~~ | ~~El delta no puede expresar un cambio de topología~~ | ~~La casa tenía una sola salida en la escena 4 y en la 11 aparece una puerta trasera que nadie plantó~~ | **CERRADO por `SPEC-03`.** `Lugar.accesos_y_salidas` pasó a ser una lista de referencias, así que el cambio de topología es una diferencia de conjuntos. Lo comprueba `VER-54`. El identificador no se reutiliza |
| ~~**PC-11**~~ | ~~Nada contrasta un resumen con la escena que resume~~ | ~~Un resumen bien formado menciona un hecho que la escena no contiene y entra en el contexto como si fuera canon~~ | **CERRADO por `SPEC-03`.** `Resumen.hechos_clave` pasó a ser una lista de identificadores, así que la comprobación es una intersección de conjuntos y tiene punto ciego propio —no ve la paráfrasis sin cita—, que es lo que la Regla 2 exigía. Lo comprueba `VER-53` |
| **PC-12** | **Un validador puede marcar como defecto lo que es correcto, y ningún validador vigila a los validadores** (`MF-23`) | `VER-46` marcó como defecto la prosa de este documento que explicaba el defecto, porque no puede distinguir una cita de una demostración | **No se resuelve con una capa que vigile a los validadores, y conviene dejarlo escrito antes de que alguien lo intente: esa capa también fallaría, y la siguiente, y no hay torre que aguante.** Lo que lo contiene es el **caso negativo obligatorio**: si cada validador demuestra que falla cuando debe, su comportamiento está acotado por abajo sin necesidad de ninguna capa encima. Un validador sin caso negativo es el que de verdad deja `MF-23` suelto |
| **PC-13** | **Un criterio de salida puede remitir a algo que no existe, y no hay forma automática razonable de detectarlo** (`MF-24`) | `VER-23` dice *"el conjunto de identificadores solo crece"* y no dice respecto a qué. El validador se implementa, pasa, y la fila cuenta como cobertura de algo que nunca se acordó | **Se evaluó el validador y se rechazó por ruido.** La comprobación automatizable —*todo criterio cita al menos una referencia que resuelve*— marcaría **32 de los 54 criterios**, y casi todos son prosa perfectamente anclada: *"se encola, se mata el proceso, se levanta"* no cita nada y no le hace falta. Lo que distingue un criterio colgante es que usa un artículo definido sin antecedente —*"la prioridad declarada"*, *"solo crece"*— y eso es una propiedad del lenguaje, no de los tokens. **Lo que sí lo contiene es la lista de comprobación de la revisión**, que es como se encontraron los dos casos: una persona leyendo. Se añade allí *"ningún criterio remite a algo que no esté escrito"* |

---

## Juicio que en realidad es una comparación

`Docs/definitions.md` clasificaba cuatro invariantes como `juez_llm` y este
documento tenía dos validadores etiquetados como juicio. Al revisarlos, varios
resultaron ser aritmética disfrazada. **`SPEC-04` reclasificó tres de las cuatro
invariantes**, así que hoy solo queda `INV-10` de tipo `juez_llm`.

| Caso | Qué dice que es | Qué es en realidad | Estado |
| --- | --- | --- | --- |
| **`VER-29`** | `human-in-the-loop review` | Análisis estático: *"el worker no tiene ninguna ruta de código"* | **Corregido en este documento** |
| **`VER-30`** | Inspección (clase `I`) | Regresión sobre un corpus, que es un test | **Corregido en este documento** |
| **`INV-14`** — *"cada deterioro es monótono, o su reversión está justificada"* | `juez_llm` | `Deterioro.serie_por_escena` es una serie numérica: la monotonía es una comparación. Solo la cláusula de la justificación necesita criterio | **Aplicado por `SPEC-04` C-4**: `tipo = regla`, con juez de desempate solo ante una reversión |
| **`INV-11`** — *"el grado de explicación acumulado no supera el fijado"* | `juez_llm` | Un conteo: cuántos `HechoCanonico` sobre la amenaza están revelados al lector frente a `grado_de_explicacion_permitido`. Solo lo implícito necesita juez | **Aplicado por `SPEC-04` C-5**: `tipo = regla`, con juez de desempate para las revelaciones implícitas |
| **`INV-03`** — *"ningún personaje actúa sobre un hecho que no conoce en `t`"* | `juez_llm` | Comparación de identificadores contra el registro de conocimiento en `t`, más el orden de `t_fabula` frente a `escena_de_establecimiento`. Solo decidir que el personaje **actúa sobre** el hecho se ve leyendo | **Aplicado por `SPEC-04` C-6**: `tipo = regla`, **severidad `bloqueante` intacta**, con juez de desempate |
| **`VER-26`** | `evals` con persona | La **estabilidad** del Juez se mide sin nadie: misma escena N veces, varianza del veredicto. Un juez que se contradice consigo mismo se descarta sin corpus | **Pendiente**: no cambia la fila, añade un paso previo |

`INV-10` admite un filtro determinista previo —comprobar si el delta registra
el coste de invocación cuando la escena invoca la amenaza— pero conserva una
parte central que solo el juez resuelve, así que sigue siendo `juez_llm` con
razón. `SPEC-04` la dejó fuera a propósito: no es una comparación disfrazada.

**Reclasificar no es ablandar.** `INV-03` conserva su severidad `bloqueante`.
Lo que cambió es **quién decide**, no **cuánto pesa**: sigue deteniendo la
escena en la puerta, y lo que ya no hace es detenerla apoyándose en un modelo
cuya fiabilidad nadie ha medido. Leer la reclasificación como una rebaja es el
error fácil, y sería el camino corto al anti-patrón de bajar una `bloqueante`
para desatascar.

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
| VER-06 | Un recortador que recorre los seis niveles del presupuesto en vez de los bloques de `SPEC-01` §2.4 | Falla: el registro de conocimiento desaparece junto a las fichas, y con él la entrada de `INV-03` |
| VER-07 | Una obra con cuarenta escenas consolidadas | El contexto no contiene el texto de la escena 3 |
| VER-08 | Una consulta de similitud cuyo vecino más próximo sea un texto completo | La consulta no puede devolverlo: no está indexado |
| VER-09 | Una secuencia de deltas con un movimiento y una muerte en el mismo `t` | El aplicador de producción y el de referencia coinciden |
| VER-10 | Consolidar una escena cuyo delta no se ha aplicado | La transición se rechaza |
| VER-11 | Un hallazgo `mayor` en una escena por lo demás correcta | La escena sigue; el hallazgo queda abierto y visible |
| VER-12 | El Auditor levanta un `INV-13` con el `verificador` del Verificador incremental | Falla: el recuento por agente mentiría y nadie se enteraría |
| VER-18 | Una respuesta de la API sin la lista de hallazgos | El componente no renderiza el texto |
| VER-19 | Un contador de tokens ausente frente a uno con valor cero | "sin medir" en el primero, `0` en el segundo |
| VER-20 | Una respuesta del Escritor con texto y sin delta | Se rechaza antes de las puertas |
| VER-24 | Una llamada que falla con excepción | También deja traza |
| VER-25 | Un contexto de Juez al que se le cuela el prompt del Escritor | El test lo detecta |
| VER-26 | Una escena mala que el Escritor considera buena | Se mide si el Juez la aprueba |
| VER-27 | Una salida del modelo con un campo de más | Se rechaza y se registra |
| VER-29 | Una ruta del worker que intente llevar una escena a `aceptada` | El comprobador estático la encuentra |
| VER-29 | Una ruta que devuelva un capítulo `cerrado` a `abierto` | El comprobador estático la encuentra: `estado_de_capitulo` no tiene esa transición |
| **VER-30** | Un prompt adversario del corpus que ya hizo fallar al Escritor una vez | Vuelve a comprobarse en cada ejecución de CI |
| **VER-39** | Un delta que declara una muerte de un personaje que no aparece en el texto | La comprobación de menciones falla |
| **VER-40** | Un Juez que devuelve lista vacía | El canario no aparece señalado y el lote se marca |
| **VER-41** | Una traza que registra el presupuesto planificado en vez del consumido | La diferencia con el `usage` no es cero |
| **VER-42** | Un fallo forzado a mitad de aplicar un delta de tres entradas | El estado queda como antes; no hay una entrada aplicada |
| **VER-43** | Una escena que falla la misma invariante `tope+1` veces | Se detiene y se marca en vez de regenerarse |
| **VER-45** | Un documento que cita la ruta del modelo de dominio con el typo que ya ocurrió —*defintions*, sin la segunda i— junto a la ruta correcta | El validador marca la rota y deja pasar la buena |
| **VER-46** | Un diagrama que escribe los estados en PascalCase, y una fuente del miedo escrita con tilde donde la tabla la tiene sin ella | El validador los marca y dice cuál es la escritura de la tabla |
| **VER-47** | Un delta que declara la muerte de un personaje que la escaleta no puso entre los presentes de esa escena | La comparación de alcance falla |
| **VER-48** | Una escena escrita en presente cuando la guía de estilo asignó pasado | La proporción de terminaciones se aleja de la serie registrada |
| **VER-49** | Matar el worker después de registrar el intento y antes de recibir la respuesta | Al reanudar no vuelve a llamar: el intento ya está registrado |
| **VER-50** | Una respuesta del Juez con puntuación intermedia y la lista de hallazgos vacía | La incoherencia se detecta y el lote se marca |
| **VER-51** | Dos personajes cuyas cuatro métricas de estilo convergen escena a escena | La distancia entre hablantes cae en la serie, aunque la deriva global de `INV-15` no se mueva |
| **VER-52** | Un informe que da un recuento de hallazgos sin su densidad al lado | El informe se rechaza |
| **VER-53** | Un resumen que cita un `HechoCanonico` que su escena ni estableció ni reveló | La intersección no es total |
| **VER-54** | Un `Lugar` que gana un acceso entre dos momentos `t` sin `HechoCanonico` que lo establezca | La diferencia de conjuntos se detecta |
| **VER-55** | Un texto que contiene una de las cadenas de `tics_prohibidos` | La búsqueda literal la encuentra |

> **Convención que imponen `VER-45` y `VER-46`, y que conviene conocer antes de
> editar este documento:** los acentos graves significan *"este es el literal"*.
> Una ruta rota o un literal mal escrito **no se citan entre acentos graves**,
> porque entonces el validador los lee como una cita y los marca. Para hablar de
> una escritura equivocada se usa cursiva o prosa. Los ejemplos concretos van en
> los ficheros de caso negativo del harness, que quedan fuera del alcance de los
> dos validadores precisamente por esto. Ver "Lo que se aprendió al implementar".

---

## Lo que se aprendió al implementar

Cinco validadores —`VER-23`, `VER-28`, `VER-38`, `VER-45`, `VER-46`— se
escribieron de verdad, con su caso negativo, y después se retiraron: la entrega
de esta fase es este documento y la spec, no el harness. **Lo que aprendieron sí
se queda**, porque es lo único de todo esto que no se puede reconstruir
leyendo.

### La convención de los acentos graves

Lo más práctico que salió, y afecta a cualquiera que edite este documento.

Al añadir las filas de caso negativo de `VER-45` y `VER-46`, **los dos
validadores fallaron contra la prosa de este mismo documento**: los ejemplos
rotos estaban citados entre acentos graves, y el acento grave significa *"este es
el literal"*.

No tiene arreglo técnico: **un validador que comprueba literales citados no puede
distinguir una cita de una demostración.** De ahí la convención —un literal
equivocado se escribe en cursiva o en prosa, nunca entre acentos graves— y de ahí
que los ejemplos concretos vivan en los ficheros de caso negativo, fuera del
alcance de los validadores. Conviene saberlo porque **el fallo aparece en un sitio
que no es el que se ha tocado**.

### `VER-45` y `VER-46` cazaron dos defectos reales en su primera ejecución

Se abrieron porque eran las dos únicas clases de defecto con historial en este
repositorio. Encontraron dos el primer día:

| Validador | Qué encontró | Estado |
| --- | --- | --- |
| `VER-45` | Una referencia a la carpeta de revisiones en su ubicación antigua, que quedó colgando al moverla de `specs/` a `Docs/` en el commit anterior | **Corregido**. Es exactamente la clase de defecto que el validador existe para cazar, y ocurrió otra vez mientras se escribía |
| `VER-45` | Una ruta de la columna "Dónde vive" que no corresponde a ninguna carpeta del árbol de `Docs/architecture.md` | Falla: no existe en disco y tampoco encaja en la estructura, que es justo el hueco por el que pasaban las rutas mal escritas |
| `VER-46` | El diagrama de §2.2.1 de `SPEC-01`, que sigue escribiendo los estados en PascalCase | **Abierto**: es `D1-2` de `REV-01` y su corrección va junto con la decisión `C-1`, así que no tocaba arreglarlo |
| `VER-56` | Se crea `backend/` con una afirmación marcada `Caduca con:` `backend/` todavía en pie | Falla: la condición que sostenía la afirmación ya se cumplió |

### Lo que el documento no aguantó al llevarlo a código

Quince hallazgos. Los que siguen abiertos son decisiones pendientes sobre este
documento, no sobre el código.

| # | Hallazgo | Estado |
| --- | --- | --- |
| F-1 | **`VER-38` no puede contrastar la severidad**, que es un tercio de su enunciado: solo existe en `Docs/definitions.md`, no hay segunda fuente. Se implementó cruzando nivel y tipo, y comprobando la severidad contra su propio vocabulario | Abierto |
| F-2 | El "Dónde vive" de `VER-01` y `VER-38` apuntaba a `harness/esquema/`, que no era ninguna carpeta de la estructura del harness | **Cerrado por `SPEC-06`.** `VER-01`, `VER-38` y `VER-22` se movieron al backend y a `CI`. Al reubicar las seis restantes salió la causa real: **no existía ninguna estructura declarada del harness**, se borró con la carpeta, así que ninguna ruta bajo `harness/` se podía juzgar. `Docs/architecture.md` § "El harness" la declara ahora —`documentos/`, `evals/`, `adversarial/`— con el criterio que decide si un validador va al backend o al harness |
| F-3 | **`VER-01` no se puede implementar ni a medias**: compara esquemas Pydantic con fichas de clase y sin `backend/` falta la mitad de la comparación | Abierto |
| F-4 | No había fila para "las rutas citadas existen" | **Cerrado**: es `VER-45` |
| F-5 | No había fila para "los literales citados son los de la tabla" | **Cerrado**: es `VER-46` |
| F-6 | **`VER-28` no dice de qué documento sale la máquina de estados.** Está en la tabla de `Docs/architecture.md` y en el diagrama de `Docs/domain-knowledge.md`; se eligió la tabla, y la eligió el implementador | Abierto |
| F-7 | **`VER-23` no dice contra qué compara.** Se eligió el commit anterior, con un agujero conocido: un borrado en dos commits ya no se ve | Abierto |
| F-8 | **`VER-23` se salta en vez de fallar cuando no hay historial**, así que puede aparecer en verde sin haber comprobado nada. El documento no dice qué hacer | Abierto |
| F-9 | No se pudo escribir la comprobación de que el nivel del agente cuadre con el de la invariante: `Docs/architecture.md` no declara el nivel de cada agente, y decidirlo es de dominio. Sigue asignando invariantes de obra al Verificador de reglas | Abierto |
| F-10 | **Los datos normativos en prosa se rompen al editar.** La skill `harness-invariantes` afirma el reparto de tipos en letra; es parseable y cualquier reescritura del párrafo lo rompe | Abierto |
| F-11 | **El escape de guion bajo de las tablas markdown es una trampa**: en una tabla y en el texto son cadenas distintas para la misma cosa, y todo comparador tiene que normalizarlo antes | Abierto |
| F-12 | **`VER-44` estaba quemado y casi se reutiliza.** `REV-02` se lo asignó al validador de ratio de compresión que luego se rechazó. **`VER-23` no lo habría cazado**: su punto ciego es que ve el conjunto de identificadores, no su significado | Cerrado por el número elegido |
| F-13 | **La columna "Dónde vive" es un plan, no una referencia**, y el documento no lo dice en ninguna parte. Un lector razonable toma esas rutas por existentes | Abierto |
| F-14 | **`VER-46` no ve los valores que son palabras comunes.** Si alguien escribe la severidad con mayúscula inicial en un documento, no lo detecta | Abierto, y consta como punto ciego de la fila |
| F-15 | **Los validadores prohíben citar el defecto** (ver arriba) | Cerrado por convención |
| F-16 | **`MF-24` se materializó en `VER-45`, y lo hizo al revés de como lo esperábamos.** No fue un criterio que remitiera a algo inexistente, sino una **exención** que lo era: *"se eximen las de la columna «Dónde vive», que son planes por construcción"*. La exención era cierta —`features/` y `commons/` no existen en la raíz— y la conclusión no: acabó tapando diecisiete rutas mal escritas que el validador existe para cazar, incluidas las nueve de `F-2`. Un criterio que no puede marcar nada está verde por construcción, y eso no se distingue de estar verde por mérito | Cerrado: la exención se eliminó y `VER-45` resuelve contra la raíz declarada en `Docs/architecture.md` |

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
- [x] ~~Cómo se comprueba que el cambio de valor entregado es el planificado~~
      — **cerrada por `SPEC-03`**: el delta lo declara y la tabla de
      correspondencia lo contrasta.
- [x] ~~Si `hechos_clave` de un `Resumen` son identificadores o texto libre~~
      — **cerrada por `SPEC-03`**: son identificadores.
- [x] ~~Reclasificar `INV-03` de `juez_llm` a `regla` con juez de desempate~~
      — **cerrada por `SPEC-04` C-6**. Conserva la severidad `bloqueante`.
- [ ] **Los umbrales de `VER-48` y `VER-51`.** Las dos series se registran desde
      el primer día; los números salen de mirarlas, como en `VER-32`.
- [x] ~~Bajar `INV-14` a `regla` y `INV-11` a `regla` con juez de desempate~~
      — **cerradas por `SPEC-04` C-4 y C-5**.
