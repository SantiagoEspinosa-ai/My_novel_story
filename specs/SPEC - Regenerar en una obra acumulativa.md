---
id: SPEC-23
titulo: Qué es regenerar en una obra cuya continuidad es acumulativa
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-23 — Regenerar en una obra acumulativa

## La tensión de fondo

Dos frases. Las dos son verdad hoy en este repositorio, y **puede que no quepan juntas**.

> **La función que se promete.** El lector selecciona un fragmento, pide un cambio, y el
> sistema **regenera solo los capítulos afectados** sin romper la continuidad de la obra.

> **El modelo que tenemos.** *El estado del mundo se reconstruye acumulando los deltas de
> escena en orden* (`Docs/architecture.md`, `CLAUDE.md`, y `VER-09` lo comprueba contra una
> implementación de referencia). Cada escena se escribe contra el estado que dejaron **todas**
> las anteriores.

Si el estado en el que se escribe la escena `n` depende de los deltas `1..n-1`, entonces tocar
el delta de la escena 7 cambia el estado sobre el que se escribieron la 8, la 9 y todas las
demás. **«Solo los capítulos afectados» y «la continuidad no se rompe» tiran en direcciones
opuestas**, y cuál gana depende de qué se acepte llamar *afectado*.

**Esta spec no elige.** Nombra la tensión, enseña dónde está exactamente, enumera las salidas
con lo que cuesta cada una —incluida la de que no se pueda sin cambiar el modelo— y deja la
decisión escrita para que se tome antes de prometer la función. Prometerla primero y descubrir
esto después es el orden que el proyecto ya decidió no seguir.

---

## Es una pregunta, no cuatro huecos

`SPEC-22` levantó cuatro carencias del backend y las listó por separado. Son la misma:

| Hueco de `SPEC-22` | Qué preguntaba en realidad |
| --- | --- |
| `G-05` · el `DeltaDeEscena` no se guarda | Con qué se calcula qué cambió |
| `G-06` · no existe la relación hecho → capítulos | **Qué significa que un capítulo dependa de algo** |
| `G-07` · la obra no tiene versión | Respecto a qué se compara *lo anterior* |
| `G-08` · una escena `consolidada` no tiene salida | Qué pasa con lo que venía después |

Las cuatro se responden solas en cuanto se responda **qué es regenerar aquí**. Por separado,
cada una admite una respuesta razonable que contradice a las otras tres.

## Qué es verdad hoy en el código

Comprobado, no supuesto:

- **El delta se aplica y se tira.** `SPEC-01` §3.2.2 lo declara *fuente de verdad del estado*
  y no hay ninguna tabla que lo guarde. Lo que se conserva es su **efecto** —entidades, sus
  ubicaciones, el registro de conocimiento—, no lo que cada escena aportó.
- **De `consolidada` no sale ninguna transición.** `rechazada` vuelve a `generada`; una escena
  consolidada no tiene camino de vuelta en `Docs/architecture.md`.
- **`RF-19` e `INV-05`** prohíben generar la escena siguiente mientras la anterior no esté
  consolidada. La generación está pensada como una sola pasada hacia delante.
- **Un capítulo `cerrado` no se reabre** (`RF-30`): dos valores y una sola transición.
- **El texto de cada intento sí se conserva**, por escena y por versión, con su modelo y su
  `prompt_hash`. De todo lo que falta, **esto no falta**.

## Por qué la promesa ingenua es falsa tal como está escrita

*«Los capítulos que usan ese hecho»* suena a un conjunto pequeño y localizado. No lo es, y la
razón no es de implementación:

1. Se regenera la escena 7 y devuelve un texto nuevo **y un delta nuevo** (`RF-09`). Si el
   delta nuevo difiere del viejo, el estado del mundo a partir de `t7` es otro.
2. Las escenas 8 en adelante se escribieron contra el estado viejo. Su texto no cambia solo
   por eso —ahí sigue, palabra por palabra—, pero **lo que ese texto supone cierto puede haber
   dejado de serlo**.
3. Y sus puertas ya pasaron. `INV-02`, `INV-03` e `INV-06` se evaluaron contra el estado
   viejo: **su verde es de otra obra**. Nada lo marca, nada lo recalcula y nadie se entera.

El punto 3 es el que hace que esto no sea una función más: **el fallo no da error**. Es la
misma familia que `MF-11` y `MF-18` —el texto y el estado divergen y ningún validador lo ve— y
la razón por la que la respuesta no puede ser *«que el frontend liste los capítulos que
mencionan el hecho»*.

**El conjunto afectado no es «los que usan el hecho»: es «aquellos cuyo contexto ha
cambiado».** Y en un modelo acumulativo, el contexto de todo lo posterior ha cambiado, aunque
sea poco. Esa es la tensión, dicha con precisión.

## El verde heredado, que es lo peor de todo esto — `MF-26`

Va aparte porque **no es una consecuencia de elegir mal entre las salidas: pasa con todas**, y
porque es peor que el coste de regenerar de más.

> Una escena posterior pasó `INV-02`, `INV-03` e `INV-06` **contra un estado del mundo que ya
> no existe**. Su verde sigue ahí, guardado, indistinguible de uno que sí vale. **No es una
> comprobación que falle: es una comprobación que dejó de significar lo que dice, y que nadie
> ha invalidado.**

Regenerar de más cuesta dinero y se ve en la factura. Esto no cuesta nada y no se ve en ningún
sitio: la obra se firma con parte de sus puertas evaluadas sobre otra obra, y el cierre de
capítulo de `RF-28` —que mira si quedan hallazgos abiertos— da por buenos unos resultados cuya
premisa cambió debajo. Es verificación que ya no verifica.

La causa de fondo es que **un resultado de verificación no guarda contra qué estado se
evaluó**. Sin ese dato no hay forma de caducarlo, ni siquiera de saber cuáles habría que mirar:
`Hallazgo` cita su invariante y su verificador, y nada dice en qué mundo se levantó. Por eso
no es un defecto de la regeneración —la regeneración solo lo **destapa**— sino un hueco del
modelo de verificación que estaba ahí desde el principio, esperando a que algo moviera el
estado hacia atrás.

Queda catalogado como **`MF-26`** en `Docs/verification.md`, en la tabla de los fallos
silenciosos, y es hoy **el único modo de fallo sin ningún validador que lo mire**. Nombrarlo no
lo arregla; lo que hace es que la elección de salida se tome sabiendo que ninguna lo cierra
sola:

- `S-1` lo evita **por fuerza bruta**: si se reescribe todo lo posterior, todo vuelve a pasar
  por la puerta y no queda ningún verde viejo.
- `S-2` lo ataca de frente y es lo que la hace interesante: reverificar **es** invalidar el
  verde heredado, y además es barato porque son reglas y no llamadas al modelo. Lo que no
  alcanza es la prosa, que nunca se reverifica contra nada.
- `S-3` lo evita porque el estado no se mueve; el verde sigue siendo del mundo en que se
  evaluó.
- `S-5` decide **cuántos** verdes hay que invalidar, no si hay que hacerlo.

Y deja una pregunta que sobrevive a esta spec: si un resultado de verificación supiera contra
qué estado se evaluó, **caducaría solo** —la misma forma que las marcas `Caduca con:`, una
condición comprobable en lugar de una nota que alguien tiene que acordarse de revisar—. Eso es
un cambio del modelo de verificación y no se decide aquí: queda **abierta como decisión
propia** en `Docs/verification.md` § Decisiones abiertas, con lo que habría que elegir —qué
identifica un estado, y qué se hace con un verde caducado—. Es la única forma conocida de que
`MF-26` deje de ser silencioso.

## Una pieza que no es una decisión

**El delta hay que guardarlo se elija lo que se elija** (`G-05`). Las cinco salidas de abajo lo
necesitan: sin él no se puede saber qué aportó la escena 7, ni comparar el delta viejo con el
nuevo, ni recalcular el estado desde un punto. Además `SPEC-01` §3.2.2 ya lo declaraba y
`VER-09` lo da por hecho. No abre ninguna pregunta: es trabajo pendiente, y es el único de los
cuatro que se puede empezar sin haber decidido nada.

---

## Las salidas

Cinco, y no son excluyentes entre sí del todo: `S-4` es ortogonal y se combina con cualquiera.

### `S-1` · Cascada: se regenera desde el punto tocado hasta el final

Lo honesto y lo trivialmente correcto. Se regenera la escena 7 y **todo lo posterior**, en
orden, como en la pasada original.

- **Qué garantiza:** la continuidad entera, con la misma fuerza que la primera escritura. No
  hay verdes heredados.
- **Qué cuesta:** una delegación por escena regenerada, más sus jueces. **Cuántas son no está
  medido**, y depende de dónde caiga el cambio: un hecho del capítulo 1 rehace el libro.
- **Qué rompe de la promesa:** *«solo los capítulos afectados»*. Aquí afectado es *todo lo que
  viene después*, y eso hay que decírselo a quien lo pide **antes** de aceptar.
- **Qué cambia del modelo:** nada. Es el modelo actual aplicado dos veces.
- **Efecto no obvio:** los capítulos que el lector no quería tocar **cambian igual**, porque la
  generación no es determinista. Se pierde texto que estaba bien.

### `S-2` · Se regenera lo que usa el hecho y **se reverifica** el resto

Se regeneran solo las escenas que usan el hecho, se recalcula el estado del mundo desde ahí, y
sobre las escenas posteriores **no se vuelve a escribir: se vuelven a pasar las puertas**. Las
que ahora fallen levantan `Hallazgo` y una persona decide.

- **Qué garantiza:** lo que las reglas deterministas ven. `INV-02` e `INV-03` se recalculan
  contra el estado nuevo, y una contradicción declarada aparece.
- **Qué cuesta:** reverificar es **código, no llamadas al modelo** (`RF-12`), así que la parte
  cara es solo la regeneración de las escenas elegidas. Es, con diferencia, la salida más
  barata de las que ofrecen alguna garantía.
- **Qué no ve, y hay que declararlo:** las puertas leen el **delta**, no la prosa. Un texto que
  contradice el estado nuevo sin que su delta lo diga pasa entero. Es `PC-5` y `MF-18` otra
  vez: el punto ciego no es de esta spec, es del sistema de puertas.
- **Qué cambia del modelo:** nada del dominio, pero sí una capacidad que hoy no existe —
  reverificar una escena ya consolidada—, y con ella la pregunta de en qué estado queda una
  escena cuya puerta vuelve a abrirse (`G-08`).

### `S-3` · Solo se aceptan los cambios que no mueven el estado

La petición del lector se acepta si el borrador nuevo trae **el mismo delta** que el viejo:
prosa, tono, descripción, ritmo. Si el delta cambia, no es una corrección local y se escala a
`S-1` o se rechaza.

- **Qué garantiza:** que nada posterior queda inválido, por construcción. La continuidad no se
  toca porque el estado no se toca.
- **Qué cuesta:** el texto y el delta vienen en la misma respuesta (`RF-09`), así que **hay que
  generar para saber si valía**: una delegación gastada por cada petición rechazada. Y hay que
  decidir qué se le enseña al lector cuando se rechaza.
- **Qué rompe de la promesa:** acota lo que se puede pedir. *«Que la casa sea de piedra»* pasa;
  *«que el hermano no muera»* no, y eso es justo lo que alguien querrá pedir.
- **Qué cambia del modelo:** nada. Necesita comparar dos deltas, que es `G-05`.

### `S-4` · La regeneración produce una versión nueva de la obra, no una edición de la vieja

Ortogonal a las tres anteriores: dice **dónde cae el resultado**, no qué se regenera. La obra
`v1` queda congelada y completa; la petición produce `v2`, que comparte por referencia los
capítulos que no cambiaron.

- **Qué resuelve:** `G-07` y `G-09` de golpe. *«Se conserva la versión anterior»* sale gratis,
  y un capítulo `cerrado` no necesita reabrirse porque **no se toca**: se escribe otro en la
  versión nueva. `RF-30` se queda como está.
- **Qué cuesta:** una noción de versión de obra y saber qué capítulos comparte con la anterior.
  El almacenamiento no es el problema: el texto de una novela es pequeño al lado de lo que ya
  guardamos.
- **Qué no resuelve:** nada de la tensión. Hay que elegir igual entre `S-1`, `S-2` y `S-3`.

### `S-5` · No se puede como está: el delta dice qué **escribe** una escena y nada dice qué **lee**

La salida que reconoce que el modelo es el que impide la función. Hoy `DeltaDeEscena` declara
lo que la escena **cambia**; **ninguna clase declara lo que la escena da por cierto**. Por eso
*afectado* no se puede calcular: falta la mitad de la relación.

Si cada escena declarara su conjunto de lecturas —qué hechos, qué entidades, qué estado
supone—, entonces *afectado* deja de ser una intuición y pasa a ser una intersección: una
escena está afectada **si y solo si** lo que lee corta con lo que el cambio movió. La promesa
del examen se vuelve **verdad**, no aproximación.

Dos formas de conseguir ese conjunto, y no cuestan lo mismo:

| | **Observado** | **Declarado** |
| --- | --- | --- |
| De dónde sale | De lo que el ensamblador metió en el prompt. La traza ya guarda fichas, presagios y resúmenes; faltarían los hechos y el registro de conocimiento | Del agente, en su respuesta, como ya declara el delta y el `pov_usado` |
| Qué cuesta | Poco, y es trabajo de código. No toca el dominio ni los prompts | El contrato del Escritor, el prompt que lo pide (`Regla 4`: las dos mitades o ninguna) y decir **qué significa** cada entrada (`Regla 5`) |
| Cómo se equivoca | **Sobre-aproxima**: marca como afectadas escenas que solo tenían el dato delante | **Se ajusta más y puede mentir**: el modelo omite lo que sí usó |
| Cómo falla | **Ruidoso**: se regenera de más, se paga de más, se ve | **Silencioso**: queda una contradicción que nadie marca |

**Esa asimetría es un criterio de decisión, no un detalle.** El proyecto ya eligió tres veces
el fallo ruidoso sobre el silencioso —`SPEC-10` C-2, el `sin_veredicto` de `SPEC-18` C-3,
`RF-26` fallando en vez de generar—, y `SPEC-16` es la factura de un contrato que fijó forma
sin significado.

### Las dos no significan lo mismo, y van bajo el mismo tipo

`SPEC-21` guarda los usos de un hecho con un `tipo_de_uso_de_hecho` y un `origen_de_uso`, y
las filas observadas de `S-5` entran como `depende` con origen `regla`. **Eso deja dos
afirmaciones distintas bajo el mismo tipo**, y la frase que las separa tiene que estar escrita
o alguien las sumará:

| Fila | Qué afirma exactamente |
| --- | --- |
| `depende` con origen `delta` | **El modelo dice que se sirvió del hecho.** Es una afirmación suya, no verificada |
| `depende` con origen `regla` | **Al modelo se le ofreció el hecho en el contexto.** Es un dato medido por código, y no dice que lo usara |

No son lo mismo y no se suman: la segunda **contiene** a la primera casi siempre, y contarlas
juntas daría un número que no significa nada. Para la regeneración se quieren las dos juntas
—sobre-aproximar es la decisión—, pero para **medir cuánto se separan**, que es lo que hay que
saber antes de elegir entre `S-1` y `S-2`, hay que poder pedirlas por separado. `SPEC-21` lo
permite filtrando por origen.

Queda una pregunta que esta spec no resuelve: si «se le ofreció» merece un valor propio en
`tipo_de_uso_de_hecho` en vez de viajar como `depende` distinguido solo por su origen. Un
valor nuevo es un cambio del vocabulario controlado y va en su spec; mientras tanto, la
distinción vive en esta tabla y en el `origen_de_uso`, no en la intuición de quien consulte.

- **Qué cuesta `S-5`:** es un cambio del dominio con su spec, su migración y su caso negativo,
  y en la variante declarada, además, un contrato de agente nuevo con el riesgo que eso ya
  costó una vez.
- **Qué compra:** que *«solo los capítulos afectados»* sea cierto en vez de ser una promesa
  con asterisco.

---

## Lo que cuesta cada una, junto

| | Llamadas al modelo | Cambia el dominio | Qué garantiza | Cómo falla | Cumple *«solo los afectados»* |
| --- | --- | --- | --- | --- | --- |
| **`S-1`** cascada | Una por escena desde el punto tocado hasta el final | No | Todo | Caro y visible | **No**: afectado = todo lo posterior |
| **`S-2`** reverificar | Solo las escenas elegidas | No, pero abre `G-08` | Lo que ven las reglas sobre el delta | Silencioso en la prosa (`PC-5`) | Parcial, con punto ciego declarado |
| **`S-3`** delta inmutable | Una por petición, incluso si se rechaza | No | Todo, por construcción | Visible: la petición se rechaza | Sí, a cambio de acotar qué se puede pedir |
| **`S-4`** versión nueva | Ninguna por sí sola | Sí: qué es una versión | Nada de la tensión; resuelve `G-07` y `G-09` | — | No aplica: es ortogonal |
| **`S-5`** declarar lecturas | Las de la salida con que se combine | **Sí, es el cambio de fondo** | La respuesta exacta a *qué está afectado* | Según variante: ruidoso u oculto | **Sí, y es la única que lo hace cierto** |

**Ninguna cifra de esta tabla está medida.** No se sabe cuántas escenas arrastra un cambio
medio porque no se ha ejecutado nunca una regeneración; lo que hay son unidades —una
delegación por escena— y de dónde sale cada coste.

## Qué decide esta spec

Nada del reparto. **Decide que la decisión existe, que es previa a `SPEC-22` `C-9` y que se
toma con estas cinco salidas delante.** Al aprobarla tiene que quedar escrito:

1. Cuál de las salidas se toma, y con qué combinación (`S-4` se combina con cualquiera).
2. **Qué se promete exactamente al lector** cuando pide un cambio, dicho en una frase que no
   contenga la palabra *afectado* sin definirla.
3. **Cuál es el punto ciego de lo elegido**, escrito, como cada validador escribe el suyo.
4. Qué pasa con las escenas posteriores: se regeneran, se reverifican o se dejan, y en qué
   estado quedan.

Y una cosa que no depende de la elección: **guardar el delta** (`G-05`) se hace igual.

## Lo que queda decidido

Tres de las cuatro preguntas están respondidas. **Ninguna dependía de la medida**, y por eso
se pudieron tomar antes de tenerla.

### `D-1` · Un verde heredado no vale (pregunta 3)

Una escena posterior cuyas puertas pasaron contra el estado viejo **deja de contar como
verificada**. Aceptarlo habría sido firmar una obra con parte de sus puertas evaluadas sobre
otra obra sin que nadie lo sepa, que es exactamente el silencio de `MF-26`.

Dos consecuencias:

- **El mínimo pasa a ser `S-2`.** La salida elegida tiene que invalidar o rehacer esos verdes:
  `S-1` los rehace escribiendo de nuevo, `S-2` los reverifica. No hay tercera forma.
- **Hay que construir la reverificación**, que hoy no existe, y **su valor no se agota en la
  regeneración**: es lo que permite **revalidar una obra entera después de cualquier cambio**.
  Eso la convierte de coste de esta función en capacidad del harness, y conviene dimensionarla
  como tal y no como un apaño de `S-2`.

### `D-2` · Dos versiones vivas, no sustitución (pregunta 4)

Se adopta `S-4`: la regeneración produce una versión nueva de la obra que comparte por
referencia los capítulos que no cambiaron, y la anterior sigue siendo navegable entera.

Lo que lo cierra no es el coste, es que **elimina la contradicción con `RF-30` en vez de
gestionarla**: un capítulo `cerrado` no se reabre porque **no se toca**, se escribe otro en la
versión nueva. La enumeración `estado_de_capitulo` se queda como está, con sus dos valores y
su única transición.

Y trae su propio requisito: **«se conserva la versión anterior» solo es comprobable si las
versiones tienen identidad propia.** No es una opinión — `CE-5` de `specs/tla/` lo demostró:
con la versión representada como el conjunto de sus capítulos, regenerar y volver a aprobarlos
todos producía un valor **idéntico** al anterior, y la propiedad `VersionesSoloCrecen` pasaba
**por no poder distinguir nada**. El campo que le da identidad es lo que la hace violarse de
inmediato. Está registrado como `F-43` y se cruza con `G-07`, que llegó a lo mismo por el otro
lado.

### `D-3` · Lo que se le promete al lector, y el punto ciego dicho (pregunta 2)

La promesa es **«reescribimos lo que dependía de esto»**, y va con su punto ciego declarado
al lector: **si la prosa contradice sin que el delta lo declare, no se toca.**

Las otras dos promesas se descartan por lo que tendrían de falso:

- **Coherencia total** no se promete porque **no se puede cumplir**. Las puertas leen el
  delta, no la prosa (`PC-5`, `MF-18`).
- **«Nada más cambia»** no se promete porque obligaría a **rechazar peticiones legítimas**:
  *«que el hermano no muera»* es exactamente lo que alguien va a pedir.

El criterio que decide entre decir el punto ciego y callarlo: **un lector avisado puede
revisar; uno al que le prometes coherencia total y no se la das, no.** Un punto ciego dicho
sigue siendo utilizable; uno callado decide por su cuenta, que es lo mismo que ya se dijo de
un sesgo.

### Pendiente · La salida final, con el umbral fijado de antemano (pregunta 1)

Queda `S-1` contra `S-2`, y espera al arrastre medido. **El umbral está fijado antes de ver el
número**, y eso es parte de la decisión y no un comentario:

| Arrastre medio | Salida |
| --- | --- |
| ~2 capítulos | `S-1` es honesta y barata, y no hay más que hablar |
| ~8 capítulos | `S-1` significa reescribir la novela en cada petición; `S-2` es la única viable |

Fijarlo antes importa por una razón concreta y ya documentada: **el sesgo conocido de esta
medida apunta a la baja** —un registro incompleto produce arrastres pequeños— y un arrastre
pequeño recomienda justo la salida que menos trabajo cuesta. Con el umbral escrito de
antemano, el número decide; sin él, el número se interpreta.

## Qué queda explícitamente fuera

- **La interfaz.** Qué se le enseña al lector y cuándo es de `SPEC-22`, y depende de lo que se
  decida aquí, no al revés.
- **`G-01`** —que ninguna escena sepa a qué capítulo pertenece—. Es un defecto activo del
  cierre de capítulo, va por su cuenta y va antes.
- **Elegir ya una de las cinco salidas.** Esta spec se aprueba eligiendo; si trajera la
  elección hecha, no habría nada que aprobar.
- **Reescribir `RF-19`, `RF-30` o `INV-05`.** Varias salidas los tocan y ninguna los cambia
  aquí: el cambio va en la spec que aplique lo elegido.
- **La regeneración dirigida por calidad** —`en_revision` → `generada`, que ya existe—. Aquí se
  habla de regenerar **después de consolidar**, que es otra cosa.

## Qué gobierna esto

`CLAUDE.md` y `Docs/architecture.md` § Persistencia —*el estado del mundo se reconstruye
acumulando los deltas de escena en orden*— y su tabla de transiciones; `DeltaDeEscena`,
`Borrador`, `EstadoDelMundo`, `HechoCanonico`, `Capitulo` y `estado_de_escena` de
`Docs/definitions.md`; `INV-02`, `INV-03`, `INV-05`, `INV-06`; `RF-09`, `RF-12`, `RF-19`,
`RF-30` y §3.2.2 de `SPEC-01`; `SPEC-22` `C-9` y sus huecos `G-05`…`G-09`; `MF-11`, `MF-18`,
`PC-5` y `VER-09` de `Docs/verification.md`; las **Reglas 4 y 5**; y el criterio de
`SPEC-10` C-2, `SPEC-18` C-3 y `RF-26`: entre fallar ruidoso y fallar en silencio, el
proyecto ya ha elegido tres veces.

## Preguntas que hay que responder antes de aprobar

| # | Pregunta | Estado |
| --- | --- | --- |
| 3 | ¿Se acepta un verde heredado? | **Respondida: no** (`D-1`). El mínimo es `S-2` y hay que construir la reverificación |
| 4 | ¿Dos versiones vivas o sustitución? | **Respondida: dos vivas** (`D-2`). Elimina la contradicción con `RF-30` en vez de gestionarla |
| 2 | ¿Qué se le promete al lector? | **Respondida** (`D-3`): «reescribimos lo que dependía de esto», con el punto ciego dicho |
| 1 | **¿Qué salida se toma?** | **Pendiente del arrastre medido**, con el umbral ya fijado. Es lo único que falta para aprobar |
| 2 | **¿Qué se le promete al lector?** ¿«Reescribimos lo que dependía de esto» o «reescribimos de aquí al final»? | `S-1` y `S-3` prometen cosas distintas y las dos son defendibles. La promesa se escribe antes de construirla |
| 3 | **¿Se acepta un verde heredado?** Una escena posterior cuyas puertas pasaron contra el estado viejo, ¿sigue valiendo? | Si la respuesta es que no, la salida tiene que **invalidar o rehacer** los verdes posteriores: `S-1` los rehace y `S-2` los reverifica, así que el mínimo es `S-2`. `S-3` no hereda ninguno —el estado no se mueve— pero **no cubre la función**: en cuanto una petición mueva el estado hay que escalarla, así que no vale como salida única |
| 4 | **¿Una obra puede quedar en dos versiones vivas, o la nueva sustituye a la vieja?** | Es `S-4`, y también decide qué significa «se conserva la versión anterior» |
| 5 | **¿Cuánto arrastra un cambio medio?** No está medido, y **hoy no se puede medir aunque haya obra**: ver la nota de abajo | Es el número que hace barata o ruinosa a `S-1`, y hoy se está eligiendo a ciegas |

### Por qué la pregunta 5 todavía no se puede contestar

Esta spec dijo antes que bastaba con una obra ya generada. **Es falso**, y el motivo es de
construcción y no de calidad de la obra. Son dos cosas que se suman:

1. **El ensamblador trae los hechos por ámbito, no por escena.** La consulta que los reúne
   recibe el identificador del ámbito que se está generando —que en la generación real es el
   **capítulo**, no la obra— y devuelve todos los suyos. Dentro de un capítulo, todas las
   escenas ven el mismo conjunto: **no hay resolución por debajo del capítulo**.
2. **Y el guion que genera la obra declara la lista entera de hechos en cada capítulo.** No
   hay hechos propios de un capítulo: los diez se declaran diez veces. Así que tampoco hay
   resolución **entre** capítulos.

Juntas, las dos dejan el conjunto de lecturas observado de hechos **constante en toda la
obra**, y la fracción que mide la pregunta 5 sale **1,0 para cualquier hecho, por
construcción**. No es un número con ruido: es un número sin resolución.

**Ojo con el orden de los arreglos:** antes de cerrarse `F-39` —la clave global de
`HechoCanonico`— ese mismo guion dejaba nueve capítulos con la lista **vacía** y todos los
hechos atribuidos al último, de modo que sus prompts decían *«hechos: (ninguno)»*. Una medida
de arrastre sacada de esa base sale **baja**, y baja no significa *arrastra poco*: significa
*se registró poco*. Es exactamente el número que parecería un argumento para elegir `S-1`, y
sería un argumento falso. Si alguna vez se enseña un número salido de ahí, se enseña **marcado
como suelo en el mismo sitio en que se enseña**, no en una nota al pie.

**Y lo que lo hace peligroso no es que esté mal: es hacia dónde se equivoca.** Un defecto que
hace que se registre de menos produce números que recomiendan justo la salida que menos
trabajo cuesta. La coincidencia entre *lo que el dato roto sugiere* y *lo que apetece hacer*
es lo que convierte un número malo en un argumento convincente, y es la razón de que un sesgo
haya que declararlo **con su dirección** y no como una incertidumbre genérica: un sesgo
conocido y dicho sigue siendo utilizable; uno callado decide por su cuenta.

**Es el cero de `INV-03` con otra cara.** *«`INV-03` bloquea 0 de 6»* también se leía como una
medida y era la huella de que no había llegado a mirar (`F-30`, Regla 8). Allí el hueco se
disfrazaba de cero; aquí, de arrastre pequeño. Las dos veces el valor falso es el que
tranquiliza.

Tres consecuencias que conviene no confundir:

- **El registro no está mal.** `lectura_de_contexto` apunta fielmente lo que entró; lo que
  entró era todo. Tampoco lo corrompe `F-40` —el defecto del orden de escena—, porque los
  hechos y el registro de conocimiento no pasaban por el filtro de `orden` que aquel rompía:
  sus damnificados eran los resúmenes, las fichas y la escena anterior.
- **La mitad de conocimiento sí tiene señal.** El registro de conocimiento se lee tal como
  está en ese momento y crece al consolidar, así que varía escena a escena. Pero responde otra
  pregunta —qué se sabía ya cuando se escribió— y no de qué depende esta escena.
- **El lado declarado sí es por escena**, porque `acciones` lo es. De modo que, para
  *decidir qué regenerar*, el observado sigue siendo la dirección correcta; para *medir cuánto
  se separan el observado y el declarado*, hoy la comparación sería «todo» contra «lo que diga
  el modelo», que mide el techo y no la separación.

**Dónde sí está la medida.** No en el conjunto observado, sino en `menciona` de `SPEC-21`:
lo **calcula el código sobre el borrador aceptado**, así que es por escena, varía, y es un
dato medido y no una afirmación de un modelo. Con él, *«cuántos capítulos añade incluir este
hecho»* se responde por hecho y a granularidad de capítulo, que es justo la granularidad en la
que la función promete regenerar. `SPEC-21` ya expone esa consulta. **La pregunta 5 se
contesta por ahí, sobre la obra repetida con los arreglos, y sin pagar ninguna generación.**

Lo que el conjunto observado sigue aportando es otra cosa, y hay que no confundirla: es el
único registro de lo que se le **ofreció** al modelo. Sirve para la decisión de `S-5` —qué se
regenera— y para saber cuándo un hecho estuvo disponible y no se usó. No sirve para medir
alcance mientras se ofrezca todo a todos.

**Y lo que haría medible también el observado** es que el ensamblador deje de ofrecer todos los
hechos a todas las escenas. Esa noción ya está escrita en el proyecto: la forma reducida del
bloque del estado dice *«los hechos permanentes y cualquier hecho que el delta referencie»*.
Existe, está declarada, y **solo se aplica al recortar** — es decir, nunca, porque el contexto
real mide tres órdenes de magnitud menos que el techo. Es la misma decisión abierta que el
reparto por niveles: un mecanismo diseñado que no se ha ejercido ni una vez.

Eso tiene nombre desde que la sesión del backend lo bautizó: es la **Regla 8 a escala de
diseño**. La `8` dice que una rama que no se ejecuta no es una comprobación que pasa; esto es
el mismo fallo un nivel arriba —no una rama, un mecanismo entero declarado y no ejercido— y
con la misma apariencia desde fuera, que es **todo verde**. `MomentoNarrativo.t_discurso`,
definido, obligatorio, con columna desde `SPEC-21` y sin que nadie lo rellene, es otra
instancia. Conviene leerlo junto a `MF-26`: allí una comprobación dejó de significar lo que
dice porque el mundo se movió; aquí un mecanismo nunca llegó a significar nada porque no
corrió. **Las dos se ven igual desde fuera.**
