---
id: SPEC-21
titulo: Qué es regenerar en una obra cuya continuidad es acumulativa
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-21 — Regenerar en una obra acumulativa

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

`SPEC-20` levantó cuatro carencias del backend y las listó por separado. Son la misma:

| Hueco de `SPEC-20` | Qué preguntaba en realidad |
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

Nada del reparto. **Decide que la decisión existe, que es previa a `SPEC-20` `C-9` y que se
toma con estas cinco salidas delante.** Al aprobarla tiene que quedar escrito:

1. Cuál de las salidas se toma, y con qué combinación (`S-4` se combina con cualquiera).
2. **Qué se promete exactamente al lector** cuando pide un cambio, dicho en una frase que no
   contenga la palabra *afectado* sin definirla.
3. **Cuál es el punto ciego de lo elegido**, escrito, como cada validador escribe el suyo.
4. Qué pasa con las escenas posteriores: se regeneran, se reverifican o se dejan, y en qué
   estado quedan.

Y una cosa que no depende de la elección: **guardar el delta** (`G-05`) se hace igual.

## Qué queda explícitamente fuera

- **La interfaz.** Qué se le enseña al lector y cuándo es de `SPEC-20`, y depende de lo que se
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
`RF-30` y §3.2.2 de `SPEC-01`; `SPEC-20` `C-9` y sus huecos `G-05`…`G-09`; `MF-11`, `MF-18`,
`PC-5` y `VER-09` de `Docs/verification.md`; las **Reglas 4 y 5**; y el criterio de
`SPEC-10` C-2, `SPEC-18` C-3 y `RF-26`: entre fallar ruidoso y fallar en silencio, el
proyecto ya ha elegido tres veces.

## Preguntas que hay que responder antes de aprobar

| # | Pregunta | Por qué bloquea |
| --- | --- | --- |
| 1 | **¿Qué salida se toma?** | Es lo único que esta spec pide |
| 2 | **¿Qué se le promete al lector?** ¿«Reescribimos lo que dependía de esto» o «reescribimos de aquí al final»? | `S-1` y `S-3` prometen cosas distintas y las dos son defendibles. La promesa se escribe antes de construirla |
| 3 | **¿Se acepta un verde heredado?** Una escena posterior cuyas puertas pasaron contra el estado viejo, ¿sigue valiendo? | Si la respuesta es que no, `S-2` es el mínimo y `S-3` deja de bastar |
| 4 | **¿Una obra puede quedar en dos versiones vivas, o la nueva sustituye a la vieja?** | Es `S-4`, y también decide qué significa «se conserva la versión anterior» |
| 5 | **¿Cuánto arrastra un cambio medio?** No está medido y se puede medir con una obra ya generada, sin pagar ninguna generación nueva | Es el número que hace barata o ruinosa a `S-1`, y hoy se está eligiendo a ciegas |
