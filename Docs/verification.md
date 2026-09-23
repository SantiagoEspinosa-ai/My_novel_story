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
sistema que medir. **Caduca con:** `backend/app/features/orquestacion/`.

ConStory-Bench mide **densidad de errores por diez mil palabras**. Es una métrica
que no tenemos y que conviene adoptar cuando haya texto: sin denominador, contar
hallazgos no dice si la obra mejora o solo se alarga. **Caduca con:** `backend/app/features/orquestacion/`, que es lo que produce texto.

## Cómo leer la tabla

Un modo entra **solo si se puede escribir cómo se manifestaría en una novela de
terror generada por este sistema**. *Alucinación* no es un modo de fallo, es una
categoría; *el delta declara un movimiento que el texto no narra* sí lo es.

**Un modo de fallo tiene tres destinos, no dos.** Los dos primeros se conocían: se **tapa**
con un validador, o se **asume** como punto ciego escrito. El tercero apareció al aplicar
`SPEC-14`: **deja de ser posible porque cambió lo que lo producía**. `MF-25` —el interbloqueo
del presupuesto— salía de cruzar la reserva de `P-2` con la exclusividad de `P-5`; al
retirar la reserva no quedó nada que retener, y el modo desapareció con su causa en vez de
taparse.

Y **lo destapó una prueba que dejó de tener sentido, no una relectura**:
`test_el_presupuesto_se_libera_tambien_cuando_falla` se quedó sin objeto al quitar la
reserva, y preguntarse qué la sustituía fue lo que llevó a ver que no la sustituía nada. Un
modo retirado se marca tachado y su identificador no se reutiliza, igual que uno cubierto:
lo que cambia es que no deja hueco detrás.

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
| **MF-16** | Caracterización | Marta pierde sus muletillas y su sintaxis y pasa a hablar como los demás personajes a partir del capítulo cinco | — `INV-15` mide la deriva **global** frente a las anclas de estilo. **No hay ninguna invariante de voz por personaje**. **`SPEC-10` añadió `FraseRecurrente`**, que guarda la frase, desde qué capítulo y cuántas veces ha aparecido: es la señal que detecta la muletilla **entre** capítulos, donde `INV-15` no llega porque mide deriva global. Queda abierto si esa señal se convierte en invariante o se queda como material para el Revisor |
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
| ~~**MF-25**~~ | ~~Interbloqueo del presupuesto por un trabajo que no vuelve~~ | ~~El worker muere con una llamada del Escritor en vuelo y el techo se queda retenido~~ | **RETIRADO por `SPEC-14` C-1.** Salía de cruzar `P-2` —el presupuesto se libera al volver— con `P-5` —la llamada del Escritor es exclusiva—. Sin reserva **no hay nada que retener**, así que el interbloqueo desaparece con su causa. El identificador no se reutiliza. Lo sustituye nada: es un modo de fallo que **dejó de ser posible**, no uno que se tape |

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

**Y su reverso, que costó una novela descubrir.** La Regla 2 dice que dos
validadores con el mismo punto ciego no suman. La otra mitad es que **repartir
toda la auditoría entre validadores de juicio deja fuera lo que ninguno mira**, y
el hueco no se ve hasta que pasa.

Ocurrió en la rama `main`, generando la primera novela de verdad —terror, tres
capítulos, rango configurado de 1.200 a 2.200 palabras—. El capítulo 1 dio esta
secuencia:

| Intento | Palabras | Continuidad | Género | Estilo |
| --- | --- | --- | --- | --- |
| 1 | 1.574 | PASA | FALLO: *"el capítulo es largo para el género, condensa"* | FALLO |
| 2 | **944** | PASA | **PASA** | FALLO |

El escritor obedeció la pega de longitud y sobrecorrigió hasta **944 palabras,
256 por debajo del mínimo configurado**. El validador de género, que en el intento
anterior había pedido acortar, **aprobó la nueva longitud sin decir nada**. Los
otros dos tampoco la mencionaron: no es su trabajo.

El diagnóstico de `DECISIONES.md` es el que importa: *"el spec repartió toda la
auditoría entre tres validadores y dio por hecho que un capítulo fuera de rango lo
cazaría el de género. Es una suposición razonable y resultó ser falsa: el
validador de género juzga **ritmo**, y un capítulo corto puede tener buen ritmo."*

Si ese capítulo hubiera acabado aceptado por puntuación, **habría entrado corto en
el manuscrito con los tres validadores conformes**. La longitud es un número, y
pedirle a un juez que compruebe un número es lo que dejó el hueco. Es la misma
lección que la Regla 3 por otra puerta: lo que se puede contar, se cuenta.

### Regla 4 — Una violación de contrato se detecta en la frontera, no en la puerta

**Si llega a la puerta, la puerta juzga lo que puede y se equivoca de diagnóstico.**

Se midió en la primera generación real. El delta volvió con frases donde el dominio quiere
identificadores —`{"sujeto": "casa familiar", "hecho": "el reloj de pared funciona sin que
nadie le haya dado cuerda"}`— y `INV-03` levantó tres `bloqueante` diciendo que **un
personaje actúa sobre un hecho que no conoce**. Es lo único que esa invariante sabe decir, y
la causa era otra: el delta no usaba referencias.

Las consecuencias se acumulan:

- **El hallazgo describe mal el defecto**, así que quien lo lea busca donde no es.
- **Hereda la severidad de la puerta**, no la del defecto real. Un fallo de formato pasa a
  ser `bloqueante`.
- Y como una `bloqueante` **no admite rendición**, eso **detiene la novela** por una causa
  que el hallazgo no nombra.

**Es la misma lección que el bug de `is`** (`F-19`): un dato que entra al dominio sin pasar
por su frontera hace que algo más adentro falle o acierte por accidente. `SPEC-03` decidió
*"referencias, no prosa"* para el dominio; la frontera que lo hace cumplir es el **contrato**,
no la invariante.

**Y el contrato no basta solo.** Si el prompt no dice qué identificadores existen, se está
pidiendo lo imposible y el rechazo es merecido pero inútil. Las dos mitades: el prompt lleva
los identificadores disponibles y el contrato comprueba que la respuesta los use, porque
**un prompt bien construido no garantiza una respuesta bien formada.**

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

### Regla 5 — Un contrato que no dice qué significan sus campos no es un contrato

**Fija una forma y deja el significado a la intuición de quien responde. Cuando las dos
intuiciones coinciden, funciona y nadie se entera; cuando divergen, las dos partes cumplen el
contrato y el sistema está roto**, sin error, sin excepción y sin nada que falle.

Es la clase de fallo que explica por qué `F-31` sobrevivió tanto. El prompt le daba al modelo
la **forma** de `revelaciones` —`[{"sujeto": ..., "hecho": ...}]`— y nunca su **significado**.
El modelo dedujo lo único que puede deducir cualquiera de la palabra *revelación*: el momento
en que alguien se entera. El código de la puerta suponía lo contrario: que el sujeto ya lo
sabía y estaba obrando. **Las dos partes cumplían el contrato** —identificadores bien
formados, esquema correcto, nada que rechazar— y el sistema estaba muerto: ningún personaje
podía llegar a saber nada nunca.

No se detectó antes porque **estaba tapado por otro fallo**: sin hechos declarados no había
revelaciones que comprobar, y sin revelaciones la contradicción no llegaba a manifestarse
(`F-29`). Un fallo que no produce error y además necesita que otro se arregle antes de poder
aparecer.

Es la **tercera mitad de la Regla 4**, que ya exigía dos: el prompt lleva los identificadores
disponibles y el contrato comprueba que la respuesta los use. Faltaba que el prompt dijera
**qué se está pidiendo con cada uno**. Un identificador bien formado en el campo equivocado
pasa las dos primeras mitades sin despeinarse.

---

## Estado de implantación

| | |
| --- | --- |
| **Modos de fallo catalogados** | **24 vigentes** (`MF-01`…`MF-25`, con `MF-25` retirado por `SPEC-14`: dejó de ser posible) |
| **Validadores definidos** | **60** (`VER-01`…`VER-63`, con `VER-44`, `VER-41` y `VER-57` quemados) |
| **De ellos, no verificables hoy** | 6 (`VER-32`…`VER-37`) |
| **Validadores implementados** | **0** |
| **Con su caso negativo escrito** | 19 — en las cuatro fases de `PLAN-01` |
| **Desbloqueados por `PLAN-01` completo** | 28 |
| **Escritos y retirados a modo de prueba** | 5 — `VER-23`, `VER-28`, `VER-38`, `VER-45`, `VER-46` |
| **Bloqueados por falta de código de producción** | 18 |
| **Implementables hoy y sin implementar** | 2 — `VER-56` y `VER-59`, que solo necesitan los documentos |
| **Puntos ciegos asumidos** | **14 activos**, más `PC-10`, `PC-11` y `PC-16` cerrados y `PC-14` quemado |

**Estos recuentos se revisan al cerrar cada fase de `PLAN-01`.** No llevan marca
`Caduca con:` a propósito: una marca avisa **una vez**, y una tabla de recuentos deja de ser
cierta **cada vez** que aterriza código. Ponerle una condición de caducidad la haría fallar
continuamente y dejaría de significar nada, que es el fallo que las marcas existen para
evitar.

**Cero implementados, y conviene decirlo en voz alta: una lista más larga no es
más cobertura.** Este documento ha pasado de 37 filas a 59 y la cifra que mide
fiabilidad sigue siendo cero. Dieciocho esperan a `frontend/`, a CI o a una ejecución real, seis esperan una medición o una decisión, y **dos —`VER-56` y `VER-59`— no esperan a nada**: solo
necesitan los documentos, que ya existen.

**Cero sigue siendo cero, y conviene no redondearlo hacia arriba.** La Fase A de `PLAN-01`
escribió veintiún tests que pasan, y **ninguno es un validador completo**. Tres escriben
*parte* de un caso negativo —`VER-38` tiene su gancho pero nadie parsea todavía la tabla del
documento; `VER-21` caza una versión repetida y un hueco, pero no cruza commits; `VER-11`
prueba los predicados de severidad, no la puerta—. Contarlos como implementados sería
exactamente la cobertura falsa que la Regla 2 persigue.

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
| **VER-58** | La longitud de la escena cae dentro de su `longitud_objetivo` (`INV-17`) | T | unit testing | Se cuentan las palabras del borrador y se comparan con el rango. Fuera de rango produce `Hallazgo` de severidad `mayor`, y por tanto impide cerrar el capítulo | Cuenta **palabras**, no **densidad**: una escena dentro de rango rellena de paja pasa. Y compara contra el rango **configurado**, no contra lo que el género pide |
| VER-03 | El endpoint de generación no bloquea: devuelve un identificador de trabajo | T | integration testing | La respuesta llega antes de que termine la generación y trae un identificador consultable | No comprueba que el trabajo **llegue a ejecutarse**: un worker parado deja `202` y trabajos eternos | `features/generacion/tests/` |
| VER-04 | Un trabajo encolado sobrevive a un reinicio del servidor | T | integration testing | Se encola, se mata el proceso, se levanta, y el trabajo sigue ahí y se completa | **No comprueba unicidad**: el trabajo puede completarse habiendo llamado al modelo dos veces | `commons/trabajos/tests/` |
| VER-05 | Ninguna llamada al modelo supera los 100.000 tokens, salida incluida, **medido con un contador independiente del ensamblador** | T | property-based testing | El contexto ensamblado más la reserva de salida cabe en el límite **según el `usage` que devuelve el modelo o un segundo tokenizador**, no según el contador de producción (Regla 3) | Mide el **techo**, no el **contenido**: un contexto de 3.000 tokens que dejó fuera al protagonista pasa | `features/contexto/tests/` |
| VER-06 | Cuando no cabe, se recorta en el orden declarado **en dos vueltas** —primero reducir, después eliminar—, y agotadas las formas reducidas y los tres primeros bloques se falla en vez de generar | T | property-based testing | Ningún recorte parte un bloque; **ninguna forma reducida se aplica fuera de orden ni se elimina un bloque con reducción pendiente**; el orden es el de las filas de `SPEC-01` §2.4 y si aún no cabe, el trabajo falla sin tocar el bloque 4.º (**estado del mundo y registro de conocimiento**), la reserva de salida ni el nivel inmutable. **El caso negativo obligatorio es el recortador que itera por niveles de `CLAUDE.md` en vez de por bloques**: se lleva el registro de conocimiento con las fichas y deja `INV-03` sin datos | Comprueba que el **orden** se respeta, no que lo que queda **baste**: un contexto recortado correctamente, que conserva el estado y el registro de conocimiento pero se quedó sin la ficha del protagonista, pasa. Eso es `PC-9` | `features/contexto/tests/` |
| **VER-59** | Ninguna forma reducida de `SPEC-12` §2.4 se lleva algo que la columna «Qué lee» asocie a una invariante `bloqueante` de nivel escena | A | static analysis | Se cruzan las formas reducidas declaradas contra lo que leen `INV-01`…`INV-05`. Cero solapamientos | **La columna «Qué lee» es una afirmación, no un hecho**, y lo será hasta que exista una implementación que pueda contradecirla. Compara declaración contra declaración: si la columna está incompleta o miente, el validador pasa igual. Es **el mismo punto ciego que `VER-38` con la severidad** —también compara un registro contra una tabla, sin nada que diga si el registro describe lo que el código hace—. Cerrarlo pide cruzar la columna contra las lecturas reales del verificador, y eso necesita código | `harness/documentos/` |
| VER-07 | Nunca se manda el texto completo de la obra al modelo | T | unit testing | Con una obra de muchas escenas, el contexto no contiene el texto de ninguna escena salvo la anterior | Mira **texto de escena**, no **volumen equivalente**: resúmenes que crecen hasta reconstruir la obra pasan | `features/contexto/tests/` |
| VER-08 | El texto completo de una escena se guarda pero no se recupera por similitud | T | integration testing | La búsqueda vectorial solo devuelve fichas, resúmenes y presagios | Comprueba el **índice**, no el **camino de lectura**: leer el texto por clave primaria lo esquiva *(lo cubre `VER-07`)* | `commons/db/tests/` |
| VER-09 | El estado del mundo se reconstruye acumulando deltas en orden, **contrastado con una implementación de referencia** | T | property-based testing | Reconstruir con el aplicador de producción y con un **aplicador de referencia ingenuo escrito solo para la prueba** da el mismo estado (Regla 3) | Comprueba que el estado **se construye bien desde el delta**, no que el **delta sea cierto** *(lo cubre parcialmente `VER-39`)* | `features/consolidacion/tests/` |
| **VER-61** | El contador de delegaciones **no está por debajo del suelo reconstruible** desde los artefactos de la obra | T | integration testing | Se reconstruye desde los artefactos cuántas delegaciones hicieron falta **como mínimo** y se compara con el contador. **Tres resultados con significado distinto**: contador > suelo es normal —hay reintentos sin artefacto—; contador = suelo es sospechoso en una obra con reescrituras; contador < suelo es **error**, se perdieron delegaciones que sí produjeron trabajo | **Compara contra un suelo, no contra una medida.** No ve las delegaciones que no dejaron ningún artefacto, y sin los intentos conservados en disco no puede calcular el suelo: entonces lo dice y no concluye, en vez de dar por bueno un suelo de cero | `commons/trabajos/tests/` |
| **VER-62** | El **conjunto** de modelos es estable entre las delegaciones de una misma obra | A | static analysis | Se recorren las trazas y se compara el conjunto canónico de cada una contra el de la primera que reportó algo. Cero discrepancias. **No se compara contra lo declarado**: el declarado es corto —`fable`— y el reportado canónico —`claude-fable-5-1`—, así que no coincidirían nunca. Las trazas **sin modelo registrado** se devuelven aparte: no cuentan como conformidad | **Vigila la estabilidad, no la identidad**: si toda la obra usa un conjunto equivocado pero el mismo, pasa. Y no ve el enrutado si la traza registra lo que se pidió en vez de lo que respondió. Entonces estaría en verde mientras el cambio ocurre, y sería un eco: la Regla 3 otra vez. Cerrarlo pide que el registro venga de la respuesta |
| **VER-60** | El texto de una escena en el manuscrito es byte a byte el del `Borrador` que se auditó | T | integration testing | Se ensambla un manuscrito con escenas `aceptada` y `aceptada_por_rendicion` y se compara cada una con su `Borrador`. Cero diferencias | Compara el **texto**, no el **orden ni lo que falta**: un manuscrito al que le falte una escena entera, o que las ponga desordenadas, pasa |
| VER-10 | Ninguna escena pasa a `consolidada` sin su delta aplicado (`INV-05`) | T | unit testing | Intentar consolidar sin delta aplicado falla; la escena siguiente no se puede generar | Comprueba que el delta **se aplicó**, no que se aplicara **entero** *(lo cubre `VER-42`)* | `features/consolidacion/tests/` |
| VER-11 | `bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y dejan seguir, y un `mayor` abierto impide cerrar el capítulo | T | unit testing | Un hallazgo de cada severidad produce exactamente el comportamiento declarado, **incluida la diferencia entre `mayor` y `menor` en la puerta de cierre de capítulo** (`SPEC-04` C-2) | Comprueba el comportamiento **dada** una severidad, no que la **asignada sea la correcta** *(lo cubre `VER-38`)* | `commons/invariantes/tests/` |
| VER-12 | Todo hallazgo cita su invariante **y el verificador que lo levantó**, los dos por identificador y nunca por descripción | A | static analysis | Todo `Hallazgo` construido lleva un identificador del registro `INV-xx` **y un `verificador` no vacío**. En las invariantes que comprueba más de un agente —`INV-13`, incremental y de barrido— dos hallazgos de la misma invariante levantados por agentes distintos tienen `verificador` distinto | Comprueba que los dos ids **existen** y que **se distinguen entre sí**, no que sean los **correctos**: un verificador copiado que no cambió ninguno de los dos sigue pasando | `commons/invariantes/` |
| VER-13 | Una feature nunca importa de otra feature, salvo `orquestacion/` | A | static analysis | El comprobador de importaciones falla el build ante cualquier import cruzado no autorizado | Estático: no ve importación dinámica ni acoplamiento por datos compartidos | CI |
| **VER-63** | Todo módulo de producción es **alcanzable desde alguna prueba**, directa o indirectamente | A | static analysis | Se recorre el árbol de importaciones desde los ficheros de prueba y se cierra transitivamente. Cero módulos fuera del alcance | **Alcanzable no es probado.** Un módulo importado para usar una constante queda contado y sin ejercitar: esto caza **código muerto**, no falta de cobertura. Y comparte `PC-1` con los otros doce: no ve la ejecución |
| VER-14 | `commons/` nunca importa de una feature | A | static analysis | Mismo comprobador; la flecha va en un solo sentido | El mismo que `VER-13` | CI |
| VER-15 | Los `Enum` de los vocabularios controlados **del dominio** viven solo en `commons/dominio/` | A | static analysis | No hay ninguna definición de `Enum` de dominio fuera de esa carpeta. Los vocabularios de infraestructura —hoy los estados de un trabajo, que `Docs/architecture.md` declara— viven con su infraestructura y no cuentan | **Sin punto ciego relevante**: regla estructural sobre artefacto estático. El único escape sería crear un `Enum` en tiempo de ejecución a propósito | CI |
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
| ~~**VER-57**~~ | ~~El presupuesto reservado por un trabajo que no vuelve se libera al expirar el margen~~ | — | — | **RETIRADO con `MF-25`** por `SPEC-14` C-1: comprobaba la liberación de una reserva que ya no existe. Identificador quemado | — | — |
| **VER-43** | Una escena no supera un número acotado de ciclos de regeneración | T | unit testing | Con un tope configurado, la escena número `tope+1` se detiene y se marca en vez de volver a generarse. **El valor del tope sale de medir, no se fija aquí** | Cuenta **ciclos**, no **diagnostica la causa**: detecta que gira, no por qué | `features/orquestacion/tests/` |
| **VER-45** | Toda ruta citada en un documento **existe tal cual está escrita, o encaja en la estructura declarada de `Docs/architecture.md`** | A | static analysis | Se recorren las rutas entre acentos graves de todos los documentos del proyecto. Cada una existe en disco **o** corresponde a una carpeta del árbol de `Docs/architecture.md`, resuelta contra su raíz declarada `backend/app/`. Cero rutas que no cumplan ninguna de las dos. Se eximen solo las ignoradas por git | Ve **existencia y forma**, no **corrección**: una ruta que existe, o que encaja en el árbol, pero que no es donde vive de verdad ese test, pasa igual. Y sigue sin comprobar que el documento citado diga lo que el citante cree | `harness/documentos/` |
| **VER-46** | Todo literal de enumeración citado en un documento se escribe como en la tabla de `Docs/definitions.md` | A | static analysis | Se normalizan los tokens con forma de identificador —minúsculas, sin tildes, sin guiones bajos— y se comparan con los valores de la tabla: si dos normalizan igual y se escriben distinto, es una variante | No ve los valores que son **palabras sueltas y comunes** (`obra`, `escena`, `regla`, `vivo`): comprobarlas daría ruido sin señal, así que `nivel_de_evaluacion`, `severidad` y `tipo_de_verificador` quedan fuera de alcance | `harness/documentos/` |
| **VER-56** | Ninguna afirmación marcada con una condición de caducidad tiene su condición ya cumplida | A | static analysis | Se recorren las marcas `Caduca con:` de todos los documentos **y del código**, **salvo las que están dentro de un bloque de código en un fichero Markdown**: ahí una marca es una demostración del formato, no una afirmación, y `SPEC-05` haría fallar el build por definir su propia convención. En un fichero de código fuente sí cuentan, que es donde viven las dos de `commons/config.py`. Para cada marca real, la ruta **no** existe en disco, o la sección citada sigue diciendo lo que la marca supone. Cero marcas con su condición cumplida. **Falla el build**: un aviso que nadie mira es el mismo problema con otra cara | **Ve la condición, no el argumento.** Que `backend/` no exista no garantiza que la afirmación siga siendo cierta por el motivo que declara. Y **no detecta una afirmación condicional sin marcar**, que sigue siendo lectura humana: es `PC-13`. En código tampoco ve una marca que un refactor separó de su valor: ve que la marca existe, no que siga pegada a lo que describe | `harness/documentos/` |
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
| ~~**VER-41**~~ | ~~Los tokens que registra la traza coinciden con los que declara el modelo~~ | — | — | **RETIRADO por `SPEC-14` C-2.** No hay `usage` que reconciliar: el harness delega en sesiones y los tokens los reporta quien delegó. **El identificador queda quemado** porque el validador que lo sustituye **afirma otra cosa** —que el contador no está por debajo del suelo reconstruible— y reutilizar el id haría mentir a su historial. Lo sustituye `VER-61` | — | — |
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
| VER-64 | **Con qué frecuencia `INV-03` bloquea una generación larga** | **Primer dato real, y no es una frecuencia.** Con `SPEC-15` y `SPEC-16` aplicadas, la generación bloqueó en la **primera** escena, con **tres** hallazgos `bloqueante` sobre `per-ana`. El mecanismo por fin se ejerció —antes bloqueó cero veces porque no había nada que comprobar (`F-29`, `F-30`)—, pero **`1 de 1` no mide nada** y además está sesgado: `F-32` dice que la primera escena de cualquier obra bloquea siempre, porque el registro de conocimiento arranca vacío. **Sigue sin dato utilizable** hasta que el conocimiento inicial se pueda declarar | Ninguna. Nace aquí |
| VER-37 | El reparto por niveles de `CLAUDE.md` basta para una escena real | **Medido tres veces, y las tres el contexto se quedó corto.** En la generación de seis escenas de `PLAN-01` F6: **1.300 tokens de contexto real** frente al techo de 100.000, y **ni un recorte**. Crece —las condensaciones fueron de 0 a 274— pero por dos órdenes de magnitud por debajo. Y ahora se sabe **por qué**: las fichas salieron vacías y el registro de conocimiento no creció, por el punto muerto de `F-29`. **La dependencia no era una obra larga: era que el material existiera.** **Cuarta medida, y tampoco cierra**: con `F-29` y `F-31` arreglados, la generación produjo **una sola escena** antes de pararse (`F-32`), y una escena no es una serie. El contexto real fue de **225 tokens** —176 de estado y conocimiento, 49 de inmutable—, y el `20.225` que imprimió el informe incluye 20.000 de reserva de salida que no es contexto y que `SPEC-14` había retirado (`F-35`). **Cerrarlo sigue dependiendo de que una generación llegue a la escena seis**, que es lo que ninguna ha hecho todavía | Ninguna. Nace aquí |

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
| **PC-1** | **Ninguna comprobación que no ejecute el sistema ve la ejecución.** Doce validadores lo comparten —nueve de análisis estático, `VER-28` de *model checking* y `VER-21` y `VER-31` de integración en CI—: `VER-01`, `VER-12`, `VER-13`, `VER-14`, `VER-15`, `VER-16`, `VER-17`, `VER-21`, `VER-23`, `VER-28`, `VER-31`, `VER-38` | Un script de mantenimiento hace `UPDATE escena SET estado='consolidada'` y salta la máquina de estados entera | Taparlo pide auditoría en tiempo de ejecución sobre la base. No es caro, pero **no hay estado del mundo que auditar todavía**: `commons/db/` existe desde `PLAN-01` A3, y su única migración crea el registro de versiones. **Caducó en `PLAN-01` C5**: `features/consolidacion/` escribe ya estado del mundo, así que **hay base que auditar y nadie la audita**. El punto ciego deja de ser condicional y pasa a ser un hueco activo |
| **PC-2** | **Nadie comprueba que quien acepta una escena sea una persona.** `VER-29` solo comprueba que el worker no puede | Un script llama a `POST /escenas/{id}/aceptar` en bucle y consolida la obra entera sin que nadie la lea | `SPEC-01` §2.5 excluye la autenticación de la v1. Sin identidad no hay nada que comprobar. **Caduca con:** `SPEC-01` §2.5 |
| **PC-3** | **La fiabilidad del Juez no está medida**, y `VER-26` en verde significa "se midió", no "es fiable" | Tras `SPEC-04` **ninguna invariante `bloqueante` es de tipo `juez_llm`**: la única que queda del Juez es `INV-10`, de severidad `mayor`. El Juez ya no detiene una escena por sí solo | **Encogido dos veces, no cerrado.** `SPEC-03` hizo escribible la parte determinista de `INV-03`; `SPEC-04` la reclasificó a `regla` y dejó al Juez como desempate. Siguen abiertas dos vías por las que un modelo sin fiabilidad medida decide: **(a)** el desempate de `INV-03` es una decisión abierta, y si el veredicto del Juez cuenta, sigue deteniendo escenas `bloqueante`; **(b)** `SPEC-04` le dio una consecuencia nueva a `mayor`, así que `INV-10` —del Juez— ahora **bloquea el cierre de capítulo**, que es una puerta humana. Esta segunda vía no existía antes: parte del punto ciego encogió y otra parte se movió una puerta más arriba. Cierra cuando `VER-26` y la medida de estabilidad den un número |
| **PC-4** | **Los resúmenes pueden crecer hasta reconstruir la obra.** Se propuso un validador de ratio de compresión —al que `REV-02` llegó a dar el número **`VER-44`**— y **se rechazó por la Regla 2**: su punto ciego, mide longitud y no calidad, ya lo tienen seis validadores. **`VER-44` queda quemado**: el identificador está publicado y no se reutiliza | El Resumidor devuelve resúmenes casi tan largos como la escena. `VER-07` está en verde porque no hay texto de escena en el contexto, y el contexto lleva la obra entera de todos modos | Se asume hasta encontrar una comprobación con un punto ciego propio |
| **PC-5** | **`VER-39` compara léxico, no sentido.** Estrecha `BC-4` —que nada contrasta el delta con el texto— pero **no lo cierra**, y es fácil darlo por resuelto | El delta dice que Marta coge el cuchillo y en el texto lo coge Luis. Los dos nombres están mencionados, así que `VER-39` pasa. El hueco de `BC-4` sigue abierto para todo delta que se equivoque sobre alguien **sí** mencionado | La comprobación semántica exige un juez, y un juez sin fiabilidad medida no mejora esto |
| **PC-6** | **`VER-12` comprueba que el identificador existe, no que sea el correcto** | Se copia un verificador y no se cambia el id: todos los hallazgos salen como `INV-01` y el recuento por invariante miente | `VER-38` valida el registro, no qué id usa cada verificador al construir el hallazgo |
| **PC-7** | **`VER-21` comprueba que la migración existe, no que sea correcta** | Se añade un atributo obligatorio y se commitea una migración vacía. CI verde y la columna no existe | Validar que una migración hace lo que dice exige ejecutarla contra un esquema de referencia |
| **PC-8** | **El contador se valida contra un suelo, no contra una medida** | Una delegación se emite, no deja ningún artefacto y no se anota. Es indistinguible de una que nunca ocurrió, así que el suelo no la ve y `VER-61` pasa | **Cambió de forma con `SPEC-14` C-2**, no desapareció. Antes era *"valida el contador contra el proveedor, no contra la verdad"*; con delegación no hay proveedor que declare nada. Se tapa en parte anotando **toda delegación emitida antes de interpretarla**, que es lo que `main` aprendió corrigiéndolo: su contador decía 59 donde habían sido 61 |
| **PC-9** | **Nadie detecta que un agente rellene con invención lo que el recorte dejó fuera** (`MF-07`) | El ensamblador recorta la ficha de Marta; el Escritor le atribuye unos rasgos físicos que nunca estuvieron en el canon. En el capítulo siete tendrá otros | Distinguir *"lo sabía"* de *"se lo inventó"* exige comparar la prosa con la ficha, y eso es un juez. **Lo que sí se hace y acota el daño: la traza de `VER-24` registra qué fichas quedaron fuera**, así que el fallo pasa de invisible a atribuible |
| ~~**PC-10**~~ | ~~El delta no puede expresar un cambio de topología~~ | ~~La casa tenía una sola salida en la escena 4 y en la 11 aparece una puerta trasera que nadie plantó~~ | **CERRADO por `SPEC-03`.** `Lugar.accesos_y_salidas` pasó a ser una lista de referencias, así que el cambio de topología es una diferencia de conjuntos. Lo comprueba `VER-54`. El identificador no se reutiliza |
| ~~**PC-11**~~ | ~~Nada contrasta un resumen con la escena que resume~~ | ~~Un resumen bien formado menciona un hecho que la escena no contiene y entra en el contexto como si fuera canon~~ | **CERRADO por `SPEC-03`.** `Resumen.hechos_clave` pasó a ser una lista de identificadores, así que la comprobación es una intersección de conjuntos y tiene punto ciego propio —no ve la paráfrasis sin cita—, que es lo que la Regla 2 exigía. Lo comprueba `VER-53` |
| **PC-12** | **Un validador puede marcar como defecto lo que es correcto, y ningún validador vigila a los validadores** (`MF-23`) | `VER-46` marcó como defecto la prosa de este documento que explicaba el defecto, porque no puede distinguir una cita de una demostración | **No se resuelve con una capa que vigile a los validadores, y conviene dejarlo escrito antes de que alguien lo intente: esa capa también fallaría, y la siguiente, y no hay torre que aguante.** Lo que lo contiene es el **caso negativo obligatorio**: si cada validador demuestra que falla cuando debe, su comportamiento está acotado por abajo sin necesidad de ninguna capa encima. Un validador sin caso negativo es el que de verdad deja `MF-23` suelto |
| **PC-13** | **Un criterio de salida puede remitir a algo que no existe, y no hay forma automática razonable de detectarlo** (`MF-24`) | `VER-23` dice *"el conjunto de identificadores solo crece"* y no dice respecto a qué. El validador se implementa, pasa, y la fila cuenta como cobertura de algo que nunca se acordó | **Se evaluó el validador y se rechazó por ruido.** La comprobación automatizable —*todo criterio cita al menos una referencia que resuelve*— marcaría **32 de los 54 criterios**, y casi todos son prosa perfectamente anclada: *"se encola, se mata el proceso, se levanta"* no cita nada y no le hace falta. Lo que distingue un criterio colgante es que usa un artículo definido sin antecedente —*"la prioridad declarada"*, *"solo crece"*— y eso es una propiedad del lenguaje, no de los tokens. **Lo que sí lo contiene es la lista de comprobación de la revisión**, que es como se encontraron los dos casos: una persona leyendo. Se añade allí *"ningún criterio remite a algo que no esté escrito"* |
| **PC-14** | *(quemado)* | Se propuso en sesión —«el Auditor solo ve resúmenes»— y **se retiró al comprobarlo**: `INV-09` compara filas de `Presagio`, no líneas de un resumen. El identificador no se reutiliza | — |
| **PC-15** | **Nadie comprueba el tope global de llamadas.** `SPEC-11` `C-1` lo declara y ningún validador lo mira | Un bucle mal cerrado encadena llamadas y el contador no frena porque nadie ha comprobado que se consulte antes de cada una | **Barato en cuanto exista la traza**: contar llamadas por escena y por obra y cruzarlas contra el tope. No se hace ahora porque no hay traza |
| ~~**PC-16**~~ | ~~Nadie comprueba que el modelo del Juez sea fijo dentro de una obra~~ | ~~El modelo cambia a mitad y las puntuaciones dejan de ser comparables~~ | **CERRADO por `VER-62`.** Dejó de ser opcional al elegir Fable como Escritor: **un modelo puede enrutar a otro por sus propias salvaguardas**, así que el cambio puede ocurrir dentro de una obra sin que nadie lo pida. Una regla que depende de que nadie la incumpla adrede no vale cuando el incumplimiento puede ser automático. El identificador no se reutiliza |
| **PC-17** | **Nadie comprueba que el Juez no vea las reglas del proyecto.** `SPEC-11` `C-4` lo declara, y es la regla que sostiene que su desempate valga algo | El prompt del Juez incluye los enunciados de las invariantes. Su veredicto pasa a confirmar lo que la regla ya dijo, y `VER-35` mide una concordancia que no significa nada | **No se puede comprobar hasta que haya un Juez.** Es el más caro de los tres y el que más sostiene: un desempate que ve lo mismo que la regla no desempata, confirma. **Y desde `SPEC-14` tiene un mecanismo concreto y frágil**: en esta arquitectura la regla se implementa con `omitClaudeMd: true` en la definición del subagente, que necesita una versión mínima de la herramienta y **lo que no reconoce lo ignora en silencio**. Una decisión de aislamiento que depende de una opción que puede fallar callando. **Y el mecanismo que se daba por hecho no funciona** (`F-20`): `omitClaudeMd` se ignora en silencio. El aislamiento pasa a conseguirse por directorio de trabajo, que sí se puede comprobar — pero nadie lo comprueba todavía, así que el punto ciego sigue abierto y ahora con un mecanismo distinto |
| **PC-18** | **El comprobador de `A-02` ve importaciones, no acoplamiento por datos** | Una feature lee la tabla de otra con un `JOIN` y no hay ningún `import` que delatarlo. Pasó en `PLAN-01` F3 (`F-28`) | Taparlo pide asociar cada tabla a su feature dueña y comprobar que nadie más la nombre en SQL. Es barato **en cuanto las tablas se declaren por feature**, y hoy cada repositorio crea las suyas sin decir de quién son |

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
| `VER-56` | El ejemplo del formato dentro del bloque de código de `SPEC-05` | **No** falla: es una demostración, no una afirmación |
| `VER-57` | Un worker muere con la reserva del Escritor tomada y otro trabajo esperando | El segundo no arranca hasta el margen; si arranca antes, el techo se repartió mal |
| `VER-58` | Una escena de 944 palabras con `longitud_objetivo` de 1.200 a 2.200 | Falla, aunque los jueces la aprueben: es el caso de la Regla 2 |
| `VER-59` | Una forma reducida del bloque de estado que retire `ubicaciones` | Falla: `INV-02` la lee y es `bloqueante` de escena |
| `VER-60` | Un ensamblador que normaliza comillas al montar el manuscrito | Falla: el informe describiría un texto que ya no es el entregado |
| `VER-61` | Una delegación que se emitió, dejó artefacto y no se anotó | Falla: el contador queda por debajo del suelo |
| `VER-62` | La escena 3 usa `{fable, haiku}` y la 40 usa `{opus}` | Falla: dos puntuaciones de conjuntos distintos no son comparables |
| `VER-63` | Un módulo nuevo que ninguna prueba importa ni directa ni indirectamente | Falla y lo nombra |

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
| F-15 | **Un validador que no distingue una cita de un uso marca el texto que explica el defecto.** Vale para los dos soportes, y se descubrió en cada uno por separado: en documentos son los **acentos graves** —un literal equivocado citado entre ellos lo marcan `VER-45` y `VER-46`, así que se cita en cursiva—; en código son los **docstrings** —la prueba que impide el eco de `VER-41` buscaba la cadena `tokens_declarados` y falló contra el docstring que explica por qué ese módulo no la escribe, así que busca **escrituras**—. Era un patrón, no una curiosidad del markdown | Cerrado por convención en los dos |
| F-29 | **La lista de identificadores se derivaba del registro de conocimiento, que solo crece revelando, que necesita la lista.** Un punto muerto que hizo `INV-03` inejecutable sin que nada fallara. Al arreglar `F-21` puse en el prompt `hechos = los del registro de conocimiento`, y el registro **arranca vacío**: el prompt decía *"hechos: (ninguno)"*, el modelo no citaba ninguno —correctamente—, no había revelaciones, y el registro seguía vacío. Seis escenas reales: **conocimiento 0, fichas 0**. Funcionó en `E5b` solo porque el fixture lo sembraba a mano. La causa de fondo es que **confundí "qué hechos existen" con "quién los sabe"**: lo primero lo declara el plan de la obra —los `HechoCanonico`— y lo segundo es lo que `INV-03` comprueba | Cerrado por `SPEC-15`: los hechos se declaran y el prompt los lleva. **El efecto todavía no se puede medir**, porque arreglarlo destapó `F-31` |
| F-30 | **Cero bloqueos no es una medida de cero.** La ejecución de seis escenas terminó sin que `INV-03` bloqueara ni una vez, y ese número **no vale**: el mecanismo nunca se ejerció, porque no hubo una sola revelación que comprobar (`F-29`). Apuntarlo como *"`INV-03` bloquea 0 de 6"* sería exactamente el verde falso que este documento persigue — **un validador que no puede dispararse no está midiendo cero** | Abierto: `VER-64` sigue sin dato |
| F-32 | **El registro de conocimiento arranca vacío, así que ninguna acción es posible en la primera escena de una obra.** Con `SPEC-16` aplicada, la generación real paró en `e1` con tres `bloqueante`: *"per-ana actua sobre hec-herencia y no consta que lo conozca en t"*, y lo mismo con `hec-sotano-cerrado` y `hec-llave-perdida`. **La mecánica es correcta y el bloqueo no lo es**: nadie sabe nada al empezar, así que cualquier personaje que obre en la primera escena bloquea, incluido el protagonista. Un personaje llega a la escena 1 **sabiendo cosas de antes del relato** —Ana sabe que heredó la casa— y no hay dónde declararlo: el plan declara qué hechos existen (`SPEC-15`) y no quién los sabe ya. **El punto muerto de `F-29` y `F-31` no ha desaparecido: se ha movido un paso más abajo**, y esta vez está en el estado inicial | Abierto: falta declarar el conocimiento inicial, y es decisión de dominio |
| F-33 | **El prompt pide exactamente el caso que la puerta bloquea, y lo escribí yo al aplicar `SPEC-16`.** El texto nuevo dice al modelo *"si se entera en esta escena y ademas obra con ello, van las dos cosas, cada una en su lista"*. Pero la puerta verifica **antes** de consolidar, así que la revelación de esta escena todavía no está en el registro cuando `INV-03` mira: aprender y actuar en la misma escena **bloquea siempre**. Y es el caso narrativo más común que existe —Marta encuentra la llave y abre el sótano— . El fondo es que `INV-03` dice *"no conoce en `t`"* y **`t` dentro de una escena no es un punto, es un intervalo**. Es la **Regla 5 dentro de su propio arreglo**: el campo ya dice qué significa y sigue sin decir *cuándo* | Abierto: en qué instante se evalúa `t` es decisión de dominio |
| F-34 | **La escena generada no era la planificada, y la invariante que debía verlo estaba inactiva por un campo ausente.** La escaleta pedía *"Marta recorre la casa heredada y cuenta los peldaños"* y el bloque inmutable exige *"tercera persona limitada sobre Marta"*. El modelo escribió **a Ana** heredando la casa y contando los peldaños, con Marta de secundaria. `INV-04` —el POV no cambia dentro de una escena— **no miró nada**, porque las escenas del fixture no declaran `pov` y la comprobación es condicional a que exista. **Una invariante que se salta en silencio cuando le falta un campo no está en verde: está ausente**, y desde fuera las dos se ven igual. Lo cazó `INV-03` de rebote, por un camino que no es el suyo | Abierto: falta decidir si un campo ausente es hallazgo o es salto legítimo |
| F-35 | **El número que el informe llama contexto no es contexto.** La ejecución reportó `20.225` tokens, de los cuales **20.000 son la reserva de salida**: el contexto real fueron **225**. Y la reserva no debería estar ahí — `SPEC-14` C-1 la retiró, y `features/orquestacion/bucle.py` lo dice por escrito. Pero `obra.generar_obra` sigue pasando `reserva_de_salida=20_000` por defecto y `ensamblado.tamanos` la inyecta en el total contra el que se compara el techo. **Dos módulos del mismo repositorio dicen lo contrario y ninguno falla**, porque el número resultante es plausible. Leer `20.225` como *"el contexto casi llega al techo"* sería exactamente el error que `VER-37` existe para no cometer | Abierto |
| F-31 | **El punto muerto tenía un gemelo un nivel más abajo, y `F-29` lo tapaba.** Arreglado `F-29` —los hechos los declara el plan y el prompt los lleva—, el modelo por fin puede revelar. Y entonces la puerta de `INV-03` bloquea **la primera revelación de la obra, sea cual sea**: trata toda entrada de `delta.revelaciones` como *actuar sabiendo ya*, y exige que el hecho conste en el registro de conocimiento **antes** de la escena. Pero el registro solo se escribe **desde** esas mismas revelaciones, en la consolidación, que ocurre **después** de la puerta. Nadie puede llegar a saber nada nunca. Las dos lecturas están escritas en el repositorio y se contradicen: `features/consolidacion/mundo.py` dice *"lo que el delta declara como revelación queda sabido a partir de esa escena"* —la revelación es el momento de **aprender**— y `features/verificacion/puertas.py` la trata como **actuar**. **Los dos fallos se tapaban mutuamente**: sin hechos en el prompt no había revelaciones, y sin revelaciones `INV-03` nunca se ejercitaba. Reproducido contra doble: escenas completas 0, parada en `e1`, *"per-marta actua sobre hec-llave y no consta que lo conozca en t"*. **Lo destapó una prueba, antes de pagar una generación real** | Cerrado por `SPEC-16`: revelar es aprender, `INV-03` deja de mirar las revelaciones y compara contra `acciones`, un campo nuevo del delta que significa obrar. La causa de fondo quedó como **Regla 5** |
| F-28 | **Dos features se pueden acoplar por la base de datos, y el comprobador de `A-02` no lo ve.** `features/consolidacion/memoria.py` hacía `JOIN escena` para saber el orden narrativo, y la tabla `escena` es de `features/escaleta/`. **No hay ningún `import`**, así que el comprobador —que hasta ahora es el que más ha encontrado— pasaba en verde sobre una dependencia real. Lo destapó su hermano: la prueba de `memoria` importó el repositorio de `escaleta` para sembrar escenas, y **eso** sí lo vio. Es el mismo límite que `PC-1` en otro eje: **el análisis de importaciones no ve el acoplamiento por datos** | Cerrado en el caso: el orden entra como parámetro y lo pasa `orquestacion/`. **El límite del comprobador sigue abierto**: ver `PC-18` |
| F-24 | **La primera vez que el sistema completo detecta el fallo para el que se construyó.** Todo lo anterior fueron validadores cazando **errores de construcción** —una importación cruzada, un módulo sin prueba, un tipo mal deserializado—. En la segunda ejecución real, `INV-03` levantó dos `bloqueante` con esta descripción: *"per-ana actua sobre hec-llave-perdida y no consta que lo conozca en t"*. El modelo hizo que un personaje revelara algo que **solo sabía su hermana**, el delta citaba identificadores válidos, y la invariante lo cazó. Eso es exactamente lo que `INV-03` existe para hacer, y es la primera vez que ocurre | **Sigue siendo una detección, y no se degrada a falso positivo.** Con `SPEC-16` revelar es aprender, así que ese caso ya no viola `INV-03` por la vía por la que se cazó. Pero el defecto no desaparece, **cambia de nombre**: no es actuar con conocimiento indebido, es **adquirir conocimiento sin fuente** —en terror, la diferencia entre un misterio y un agujero de guion—. Lo recoge la decisión abierta de `Docs/definitions.md` sobre `RegistroDeConocimiento.fuente`, que existe desde `SPEC-03` para esto y no comprueba nadie |
| F-25 | **El volumen no predice el coste, así que ningún razonamiento por tokens vale.** Medido en el ciclo completo: el Resumidor gastó **1.872** tokens y costó **0,0294 $**; el Juez gastó **1.567** y costó **0,0689 $** — más del doble con menos volumen. El precio del modelo pesa más que la cantidad. Se corrigió el razonamiento que veníamos heredando de `EJECUCION.md` de la otra rama —*"si los validadores gastan más tokens que el escritor, estás pagando la auditoría más cara que la novela"*—: **el coste se lee, no se deduce** | Cerrado: el coste sale de `total_cost_usd` por delegación |
| F-26 | **El aislamiento del Juez, decidido por corrección, resultó ser la partida más rentable del ciclo.** `SPEC-11` C-4 lo aisló para que su desempate no fuera un eco. Al medirlo: su directorio no tiene `CLAUDE.md`, así que crea **2.562** tokens de caché en vez de los **8.434** del Escritor, y cuesta **cuatro veces menos**. **El aislamiento no es solo rigor, es economía**, y eso lo hace mucho más fácil de defender el día que alguien quiera quitarlo para simplificar | — |
| F-27 | **El transporte impuso a todos la forma del Escritor, y el ciclo informó éxito habiendo tirado el juicio.** `_normalizar` devolvía `{texto, delta}`, que es el contrato del Escritor: el veredicto del Juez salió `None` y los `hechos_clave` del Resumidor se perdieron, **sin que nada fallara**. Es una instancia de la **Regla 4** —la forma de una respuesta es cosa del contrato de su agente, no del transporte— y del peor tipo: **un fallo que no produce error**. Lo destapó leer una salida, no una prueba | Cerrado: el transporte entrega lo que llegó y cada contrato impone su forma |
| F-23 | **Un módulo sin prueba no está verificado: está sin ejecutar.** `prompt.py` se quedó con un error de sintaxis y la suite siguió en verde, porque ningún test lo importaba. Lo cubre `VER-63`, y su primera versión **marcó cinco módulos que sí se ejecutan** —los de `features/brief/` entran por `app.main` cuando una prueba levanta el cliente HTTP—: hubo que cambiarla de *importación directa* a **alcanzabilidad transitiva**. Marcar código que se ejecuta es cobertura falsa al revés, y enseña a ignorar al validador | Cerrado por `VER-63` |
| F-21 | **El delta volvió en prosa, y `INV-03` lo denunció como otra cosa.** En la primera generación real el modelo devolvió `{"sujeto": "casa familiar", "hecho": "el reloj de pared funciona sin que nadie le haya dado cuerda"}` — **frases, no identificadores**. `INV-03` levantó tres `bloqueante` diciendo que un personaje actúa sobre un hecho que no conoce, y la causa real era que **el delta no usó referencias**. La puerta no puede distinguir una violación de continuidad de una violación de contrato: las dos producen el mismo hallazgo, con la severidad de la primera. `SPEC-03` decidió "referencias, no prosa" para el dominio y **nadie lo hace cumplir en la frontera del contrato** | Abierto |
| F-22 | **Una delegación usa más de un modelo, y ninguno se llama como el declarado.** `modelUsage` de la ejecución devolvió `["claude-fable-5-1", "claude-haiku-4-5-20251001"]` para una sola llamada con `--model fable`. `VER-62` compara un valor contra un valor: tal como está marcaría **todas** las delegaciones. Hay que decidir qué significa "el modelo fijo" cuando el transporte devuelve un **conjunto** | Abierto |
| F-20 | **`omitClaudeMd` se ignora en silencio, y era el mecanismo del aislamiento del Juez.** Comprobado con un control en la versión **2.1.274**, por encima de la mínima que pedía el hallazgo 3: con la opción a `false` el agente enumeró los seis niveles del presupuesto de contexto, exactos; **con la opción a `true`, exactamente lo mismo**. Y el cuerpo del agente **sí** se aplica —un marcador arbitrario apareció—, así que la definición se carga y es la opción la que no hace nada. Lo que sí aísla es el **directorio de trabajo**: la misma pregunta desde un directorio vacío devolvió *"NO LO SE"* | Cerrado: el transporte acepta `cwd` y el Juez se lanza desde un directorio sin `CLAUDE.md`. **Y no basta con eso**: el agente aislado ofreció ir a buscar el fichero, así que el aislamiento es directorio vacío **más** ninguna herramienta que lea el proyecto |
| F-19 | **Una enumeración que hereda de `str` hace que casi todo funcione, y por eso el fallo se esconde.** `"mayor" == Severidad.MAYOR` es cierto, `"mayor" in {Severidad.MAYOR}` es cierto y hasta los hashes coinciden — **solo `is` falla**. El repositorio devolvía severidades como cadenas y `impide_cerrar_el_capitulo` comparaba con `is`: **un `mayor` leído de la base no bloqueaba el cierre de capítulo**, y la puerta quedaba abierta sin que nada fallara. Las pruebas unitarias de la puerta no lo veían porque le pasaban miembros de la enumeración directamente; lo destapó la primera prueba que recorrió el camino entero, de la base al endpoint | Cerrado: **la deserialización es la frontera de validación de la base**, igual que Pydantic lo es de la API. Un dato que entra al dominio entra con el tipo del dominio |
| F-17 | **La primera vez que un validador encontró algo que nadie había visto.** El bucle de generación se escribió en `features/generacion/` e importaba de otras tres features, violando `A-02`. Lo cazó el comprobador de importaciones cruzadas de `B1`, **el más barato del proyecto**: diez líneas que recorren `features/`. Todos los hallazgos anteriores de esta sesión salieron de **cruzar documentos a mano**. Es el argumento de que una regla que nunca ha fallado en las pruebas no está verificada, sino declarada: **esa ya falló, contra su propio autor, y desde entonces vale** | Cerrado: el bucle vive en `features/orquestacion/`, la única autorizada a componer |
| F-18 | **Un doble que solo sabe portarse bien pasa contra sí mismo.** Es la Regla 3 aplicada a las pruebas: si el doble no puede producir lo que el real produce mal —un delta fuera de esquema, una respuesta muda, un texto corto—, el bucle pasa contra el doble y falla contra el proveedor, y la prueba habrá verificado su propia idea del mundo. El doble de `PLAN-01` E2 lleva un guion de comportamientos, y cuatro de los seis son malos | Cerrado por convención |
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

**Dos etiquetas, y la diferencia importa.** Las decisiones marcadas **«se contesta sola»**
esperan un dato y el dato las resuelve. Las marcadas **«deja de ser ciega»** esperan un dato
que las informa y **no las decide**: seguirán necesitando que alguien elija, solo que ya no
a oscuras. Estaban todas escritas en el mismo tono, y eso prometía que ejecutar las
resolvería todas — el día que llegue la primera traza, alguien miraría las segundas
esperando una respuesta que el dato no da.

- [ ] **Qué comprobador de importaciones** se usa para `VER-13`, `VER-14` y `VER-15`.
- [ ] **Qué herramienta de FSD** cierra `VER-17`.
- [ ] **Qué conjunto de escenas** sirve de corpus para los evals de `VER-26`.
- [ ] **Qué defecto planta el canario** de `VER-40`, y cada cuánto se cambia para
      que el Juez no acabe acertándolo por memorización.
- [ ] **Quién genera prompts nuevos** para el corpus de `VER-30` y cada cuánto.
- [ ] **Dónde viven las trazas** de `VER-24` y quién las mira. **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
- [ ] **El tope de ciclos de regeneración** de `VER-43`. Sale de observar cuántas
      veces regenera de verdad una escena problemática. **Se contesta sola** con una traza real.
- [ ] **Umbrales de `INV-15` e `INV-16`** (`VER-32`, `VER-33`). Es la misma
      decisión "Umbrales" de `Docs/definitions.md`: se cierran las tres a la vez. **Se contesta sola** con una traza real.
- [ ] **Coste por escena** (`VER-36`) y **suficiencia del reparto por niveles**
      (`VER-37`). Nacen aquí y hay que abrirlas en `Docs/architecture.md`. **Se contesta sola** con una traza real.
- [x] ~~Cómo se comprueba que el cambio de valor entregado es el planificado~~
      — **cerrada por `SPEC-03`**: el delta lo declara y la tabla de
      correspondencia lo contrasta.
- [x] ~~Si `hechos_clave` de un `Resumen` son identificadores o texto libre~~
      — **cerrada por `SPEC-03`**: son identificadores.
- [x] ~~Reclasificar `INV-03` de `juez_llm` a `regla` con juez de desempate~~
      — **cerrada por `SPEC-04` C-6**. Conserva la severidad `bloqueante`.
- [ ] **Si la condición de una marca `Caduca con:` puede dejar de ser una ruta.**
      **Dispararon por tercera vez en `PLAN-01` D2**, al crear
      `features/orquestacion/`, y las seis afirmaciones de medidas **siguen siendo
      ciertas**: hay máquina de estados y no hay ni una llamada al modelo.
      **No se han vuelto a reapuntar a propósito**: reapuntar por cuarta vez sería
      seguir fingiendo que una ruta puede expresar lo que no puede. Quedan apuntando a
      `features/orquestacion/` y **caducadas a sabiendas** hasta que esta decisión se
      cierre. Una ruta
      no puede expresar *"existe el dato"*, y siempre hay una carpeta antes que la primera
      medida: las marcas de medidas caducaron dos veces antes de tiempo, en `PLAN-01` A1 y
      B2. La salida sería una condición sobre datos —*"cuando exista una traza con
      `tokens_declarados`"*— y reapuntar solo acerca el proxy. **Se decide cuando haya
      dato**, que es dentro de poco. **Se contesta sola** con una traza real.
- [ ] **Los umbrales de `VER-48` y `VER-51`.** Las dos series se registran desde
      el primer día; los números salen de mirarlas, como en `VER-32`. **Se contesta sola** con una traza real.
- [x] ~~Bajar `INV-14` a `regla` y `INV-11` a `regla` con juez de desempate~~
      — **cerradas por `SPEC-04` C-4 y C-5**.
