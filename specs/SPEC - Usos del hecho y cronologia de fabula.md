---
id: SPEC-21
titulo: Los usos de un hecho y la cronología de la fábula
estado: aprobada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-21 — Los usos de un hecho y la cronología de la fábula

> **Qué cuenta como aprobación aquí.** La instrucción literal del autor: *«Sigue hasta
> tenerlas pobladas de verdad y usadas por quien las necesita. Decide tú el esquema, los
> índices y cómo se rellenan al escribir cada capítulo»*, con una sola reserva —qué
> significa que un capítulo usa un hecho— que `C-2` resuelve dejándola **parametrizable**
> en vez de fijándola.

## Qué problema resuelve

Dos relaciones que el dominio necesita y **ninguna tabla guarda**, y de las que cuelgan
cuatro capacidades que hoy no se pueden construir.

- **Dónde se usa un hecho.** `HechoCanonico.escena_de_establecimiento` dice **dónde nace**
  un hecho. No dice dónde se vuelve a usar, y son dos preguntas distintas: un hecho se
  establece una vez y se usa muchas. Sin la segunda no hay enlaces de ficha de personaje al
  capítulo, ni regeneración selectiva, ni comprobación de que un elemento pedido por el
  lector llegue al texto, ni fichero Lean.
- **La cronología de la fábula.** `EventoCronologico` está definido en `docs/definitions.md`
  desde el primer día —**id**, **t_fabula**, participantes[], consecuencias[]— y **no lo
  implementa nadie**. `MomentoNarrativo` es atributo obligatorio de `Escena` y la tabla
  `escena` no tiene ninguna de sus tres columnas. Así, las tres afirmaciones que un
  validador formal tendría que demostrar —orden temporal, edad coherente con la fecha de
  nacimiento y que nadie esté en dos lugares a la vez— **no son ni siquiera expresables**.

Hay además un hueco de estructura que bloquea la primera: **la relación `contiene`
Capitulo→Escena no existe en la base.** `escena` no tiene columna `capitulo`, y
`orquestacion/router.py` resuelve las escenas de un capítulo llamando a una consulta que
filtra por `obra`. Funciona sólo mientras obra y capítulo coincidan. La pregunta «¿en qué
capítulos se usa este hecho?» no tiene respuesta hasta que esa columna exista.

---

## C-1 · La relación `contiene` se materializa en `escena.capitulo`

`Escena` gana el atributo `capitulo` → `Capitulo`.

Es la relación `contiene` de la tabla de relaciones, que estaba declarada y no
implementada. Se materializa en la escena y no como lista dentro de `Capitulo` porque
todas las consultas van en esa dirección: dado un hecho, dado un personaje o dada una
escena, se quiere saber **su** capítulo.

**Ninguna consulta puede volver a suplir el capítulo con la obra.** Cuando el dato falte,
la respuesta lo dice; no cae a la obra en silencio.

---

## C-2 · «Usar un hecho» son cuatro relaciones, y cuál cuenta lo decide cada consumidor

Nace el vocabulario controlado `tipo_de_uso_de_hecho`, con cuatro valores. **No se
colapsan en uno**, porque tienen condiciones de verdad distintas, consumidores distintos y
distinto origen:

| Valor | Qué afirma | De dónde sale |
| --- | --- | --- |
| `establece` | El texto de esa escena hace verdadero el hecho por primera vez | `revelaciones` del delta |
| `menciona` | El enunciado del hecho aparece léxicamente en el texto | **Lo calcula el código** sobre el borrador aceptado |
| `depende` | Alguien obró sirviéndose del hecho: si el hecho fuera falso, la escena no se sostiene | `acciones` del delta (`SPEC-16` C-1) |
| `contradice` | La escena afirma algo incompatible con el hecho | Nadie todavía: se puede escribir y **no se deduce solo** |

`contradice` **no es un uso** y se guarda en la misma tabla a propósito: es la misma
arista del grafo con distinto signo, y separarla en otra tabla obligaría a unir las dos en
cada consulta para responder «¿qué relación tiene este capítulo con este hecho?». Lo que
**no** puede hacer es contar como aparición ni arrastrar regeneración hacia adelante.

**Cuál de los cuatro cuenta lo declara cada consumidor, no esta spec.** Cada capacidad
publica su conjunto con nombre propio, y cambiarlo es editar una constante: no hay
migración, porque las cuatro filas ya están escritas. Los valores de partida son:

| Consumidor | Tipos que cuenta | Por qué |
| --- | --- | --- |
| Elemento personalizado que debe aparecer | `menciona` | Lo pedido es que **aparezca**, no que la trama dependa de ello |
| Regeneración selectiva | `establece`, `depende`, **y `menciona` pendiente de medida** | Ver abajo: la decisión es que entre, y el número que la confirma no se ha tomado todavía |
| Enlaces de la ficha de personaje | `establece`, `menciona`, `depende` | La ficha enlaza a donde el lector encontrará algo |
| Fichero Lean | los cuatro | Un demostrador necesita el grafo entero, incluida la arista negativa |

### `menciona` en la regeneración selectiva: entra, pendiente de medida

La primera versión de esta spec excluyó `menciona` del conjunto de la regeneración razonando
que *«reescribir lo que sólo lo nombra de pasada reescribe media novela por nada»*. **Ese
argumento no se sostiene, por dos motivos.**

El primero es de criterio: `menciona` es **el único de los cuatro tipos que mide el código**.
Excluirlo elige el fallo silencioso —se omite un capítulo que sí usaba el hecho y nadie lo
marca— precisamente en el eje donde el dato es más fiable, y este proyecto ha preferido tres
veces el fallo ruidoso al silencioso (`SPEC-10` C-2, `SPEC-18` C-3, `RF-26`).

El segundo es de método: **era una intuición de coste, y el coste se puede medir gratis.**
Excluir algo por lo que costaría, sin haber comprobado nunca lo que cuesta, es exactamente
el tipo de decisión que este proyecto no acepta en ningún otro sitio.

**La decisión es que entre, y la medida es la que lo confirma.** No se toma antes de tenerla:

- **Qué se mide.** `consultas.arrastre_de_incluir_mencion(con, hechos)`, sobre la siguiente
  generación real. Devuelve cuántos capítulos arrastra hoy el conjunto declarado, cuántos
  arrastraría añadiendo `menciona`, y el detalle por hecho.
- **Qué se cuenta.** Capítulos **que se añaden**, no menciones. Un capítulo que ya entraba por
  `depende` y además nombra el hecho no es trabajo nuevo, y contarlo haría parecer caro justo
  lo que no lo es.
- **Qué se hace con el resultado.** Si el arrastre crece en unos pocos capítulos, `menciona`
  entra sin más discusión. Si crece en decenas, se decide **con el número delante** y no antes.

Mientras tanto `PARA_REGENERACION` se queda en `(establece, depende)`, que es el estado
*pendiente de medida* y no una elección: cambiarlo es añadir un valor a la constante.

**Cada fila dice quién la afirmó** (`origen_de_uso`: `regla`, `delta`, `juez_llm`,
`humano`). Una fila calculada por código es un dato medido; una declarada por un modelo es
una afirmación no verificada, y un demostrador formal no puede tratarlas igual.

**El origen forma parte de la clave, y al implementar se vio que no lo era.** La primera
versión identificaba una fila por `(hecho, escena, tipo)`, de modo que un `depende`
**observado** y uno **declarado** sobre el mismo par no cabían a la vez: el segundo pisaba
al primero y cuál sobrevivía dependía del orden de escritura. Eso borra en silencio la
distinción que `origen_de_uso` existe para guardar, y deja una fila creíble en su lugar.

No es un detalle de esquema. `SPEC-23` `S-5` compara las dos formas de saber de qué depende
una escena —**observada**, de lo que el ensamblador metió en el prompt, que sobre-aproxima y
**falla ruidoso**; **declarada**, de lo que el modelo dice que usó, que se ajusta más y
**falla en silencio**— y deja escrito que, si hubiera que elegir, la correcta es la
observada, porque el proyecto ya prefirió tres veces el fallo ruidoso (`SPEC-10` C-2,
`SPEC-18` C-3, `RF-26`). **Mientras las dos filas quepan, esa elección sigue siendo editar
una constante.** Sin la clave ampliada, dejaría de serlo.

**Y eso deja el conjunto de la regeneración selectiva a la espera.** Los valores de partida
—`establece` y `depende`— salen **los dos del delta**, es decir, son declarados: con ellos
solos, la regeneración selectiva hereda el modo de fallo silencioso. Cuando exista una
fuente observada (`SPEC-23` la está construyendo, y escribe con `origen_de_uso = regla`),
incluirla es añadirla al conjunto. Qué conjunto queda es decisión del autor, no de esta
spec; lo que esta spec garantiza es que la decisión siga siendo barata.

---

## C-3 · La cronología es de eventos, y su eje es una fecha absoluta

Nace la tabla del `EventoCronologico` que el dominio ya definía, con dos atributos nuevos
—`lugar` y `capitulo`— y la participación como relación aparte.

**La unidad es el evento y no el capítulo**, y esto no es un detalle de grano: un capítulo
es un intervalo, no un instante. Con un instante por capítulo, *«nadie está en dos lugares
a la vez»* es **falsa por construcción** en cuanto un capítulo dure lo bastante para que
alguien viaje. Una escena aporta su evento por defecto; el delta puede declarar más.

**`t_fabula` es una fecha absoluta ISO-8601.** Es la única forma de que las tres
afirmaciones sean demostrables a la vez: el orden se compara, la ubicuidad necesita
intervalos y **la edad sólo se puede restar de algo absoluto**. Un desplazamiento relativo
obligaría a fijar además el día cero, es decir, a tener una fecha absoluta de todos modos,
escondida en otro sitio.

`Personaje` gana `fecha_de_nacimiento`, **opcional**. Obligatoria rompería todas las obras
ya generadas; y como es opcional, **quien no la tenga no pasa la comprobación de edad: la
salta, y lo dice.** Un dato ausente no es un verde.

**Presente y mencionado no son lo mismo**, y la participación lo distingue con
`tipo_de_presencia`. Un personaje del que se habla en un evento no está en el evento, y
confundirlos convierte la invariante de ubicuidad en una fábrica de falsos positivos.

---

## C-4 · Se puebla al consolidar cada escena, dentro de su transacción

Las filas se escriben en el mismo punto en que hoy se marca `escena_de_establecimiento`, y
**dentro de la transacción de la consolidación**. Fuera de ella, un delta que falle a
medias dejaría usos registrados de una escena que no ocurrió: el estado a medias que
`INV-05` no sabe clasificar, por otra puerta (`SPEC-07`).

Escribir es **idempotente**: reconsolidar no duplica. Una escena ya consolidada no vuelve a
pasar por aquí, pero la idempotencia no se apoya en esa garantía, porque apoyarse en ella
la convierte en la única que sostiene la tabla.

---

## Qué queda explícitamente fuera

- **Las cuatro capacidades que consumen esto.** Esta spec entrega las tablas, la escritura
  y las consultas parametrizadas. La ficha de personaje, la regeneración selectiva, el
  validador de elementos personalizados y el generador Lean son suyas.
- **Poblar `contradice`.** El valor existe y la tabla lo admite. Deducirlo exige decidir
  antes qué invariante lo detecta, y eso es otra spec.
- **Una invariante nueva.** `INV-08` ya cubre la monotonía de `t_fabula`. Las
  comprobaciones de edad y de ubicuidad se exponen como consultas; convertirlas en `INV-19`
  e `INV-20` es una decisión de catálogo que no se toma aquí.
- **Tocar `prompts/` o los subagentes.** Nada de lo que aquí se puebla lo necesita: los tres
  tipos que se rellenan solos salen del delta que ya existe o del texto que ya está escrito.
