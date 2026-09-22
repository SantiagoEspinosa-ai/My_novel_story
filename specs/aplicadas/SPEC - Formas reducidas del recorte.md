---
id: SPEC-12
titulo: El recorte deja de elegir qué se pierde y pasa a elegir cuánto se conserva
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: 46d7bc8
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-12 — Formas reducidas del recorte

Reescribe §2.4 de `SPEC-01`, que está **aprobada**. Sale de `REV-03`, hallazgos `A`, `B`,
`C` y `G`.

> `SPEC-11` queda reservada para los cinco huecos de arquitectura que inventarió `SPEC-10`.
> Su tabla está publicada en una spec aplicada, y los identificadores publicados no se
> reutilizan.

## Qué problema resuelve

§2.4 no estaba mal escrita: estaba escrita con lo que sabíamos. La rama `main` contiene un
ensamblador que se ejecutó durante días, y enseñó cuatro cosas que nuestro orden no previó.

**La de fondo es que nuestro recorte es binario.** Un bloque entra o no entra, así que
recortar es *elegir qué se pierde*. El suyo **degrada en dos de sus tres pasos** —un resumen
baja a su primera frase, el capítulo anterior baja a su resumen— así que recortar es
*elegir cuánto se conserva de cada cosa*. No es un matiz: son dos diseños distintos, y el
segundo pierde menos por cada token que recupera.

## Qué tiene que ser verdad al terminar

### C-1 · Cada bloque declara su forma reducida, y el recorte las agota antes de tirar nada

§2.4 gana una columna. Cada fila dice **qué queda del bloque cuando se reduce**, y el
recorte recorre **dos vueltas**: primero reduce todo lo reducible en orden, y solo después
empieza a eliminar bloques enteros, también en orden.

**Un bloque sin forma reducida lo declara**, y ese dato vale por sí solo: un bloque
irreducible solo se puede perder entero, y saber cuáles son cambia el orden. La reserva de
salida es el caso claro — reducirla no es recortar contexto, es **truncar la escena**.

### C-2 · Dentro de un bloque puede haber cosas de dos durabilidades

El primer recorte de `main` no es un bloque: es **la mitad efímera de uno**. Los hechos
permanentes no se tocan nunca; los efímeros se van antes que nada.

Es la lección de `P-A` en otro bloque. Allí el registro de conocimiento tuvo que salir de
`Recuperado` porque sin él `INV-03` no es peor, es **imposible**. Aquí: dentro del estado
del mundo hay hechos que sostienen la continuidad para siempre y hechos que importan tres
escenas.

**Los seis bloques se revisan uno a uno con la pregunta** *"¿hay aquí dos clases de cosa con
distinta durabilidad?"*. Donde la haya, la forma reducida del bloque es quedarse con la
duradera.

### C-3 · Estimar, reservar y registrar son tres números con tres nombres

§2.4 dice hoy cuándo recortar y no dice con qué cuenta. `main` lo resolvió y escribió el
motivo: `CARACTERES_POR_TOKEN = 4`, porque *"sin el tokenizador del proveedor no hay cuenta
exacta, y no la necesitamos: esto solo decide cuándo recortar, y para eso basta una
estimación conservadora"*.

| Pregunta | Qué necesita | Quién la hace |
| --- | --- | --- |
| **¿Recorto ya?** | Rápido y conservador. Una estimación con margen declarado | El ensamblador, en cada vuelta del bucle |
| **¿Me he pasado del límite?** | Exacto y **con segunda fuente** | `VER-05` y `VER-41`, después |

**No son dos números: son tres, y mezclar dos cualesquiera rompe la Regla 3.**

| Número | Quién lo calcula | Para qué | Cuándo |
| --- | --- | --- | --- |
| `tokens_para_recortar` | El ensamblador | Decidir si hay que recortar otra vuelta | En cada iteración del bucle |
| `tokens_reservados` | El control de presupuesto | Apartar el techo por `P-2` | Una vez, antes de salir |
| `tokens_estimados` | El contador propio | Reconciliar contra el `usage` del proveedor (`SPEC-08`) | Una vez, al registrar la traza |

**Esto es exactamente lo que alguien unifica al refactorizar creyendo que simplifica**, y
por eso se escribe con los tres nombres. Si el ensamblador y la reserva comparten número, la
reserva hereda el margen de una estimación barata. Si la reserva y la traza lo comparten,
`VER-41` compara un número consigo mismo y vuelve a ser el eco que `SPEC-08` cerró. Tres
fuentes, tres nombres, y ningún atajo.

Un ensamblador que cuenta exacto para decidir si recorta paga el tokenizador en cada
iteración y no gana nada: lo que decide es *"me paso o no"*, no *"por cuánto"*.

### C-3 bis · Ninguna forma reducida se lleva lo que lee una `bloqueante` de escena

> **La forma reducida de un bloque nunca puede llevarse lo que lee una invariante
> `bloqueante` de nivel escena.** Si lo hace, la puerta sigue en pie y ya no puede decidir.

**De dónde salió**, porque el motivo no se entiende sin la historia: al corregir la forma
reducida del bloque 4.º se vio que no podía llevarse el registro de conocimiento, porque
`INV-03` sin él no es peor, es **imposible**. Al escribir `SPEC-13` se vio que **ese
argumento no era solo del registro**: `ubicaciones` es efímera por naturaleza —la primera
candidata a irse— pero `INV-02` es `bloqueante` y comprueba que un personaje presente sea
**accesible**, cosa que sin ubicaciones no se puede saber. Dos casos con el mismo patrón
son una regla.

**Es comprobable desde `SPEC-13`**, que añadió a la tabla de invariantes la columna «Qué
lee». Sin ella la regla sería una intención. Lo comprueba `VER-59`.

**Destapó un conflicto con la tabla de la pregunta 1, y así se resolvió.** La forma
reducida del 2.º decía *"solo las entidades presentes"*, pero `INV-02` lee
`Lugar.accesos_y_salidas` y **un lugar del camino entre dos lugares no es una entidad
presente**. Se resuelve como el 4.º: **partiendo el bloque por lo que lo hace irreducible,
no declarando irreducible el bloque entero.** La forma reducida conserva **el grafo de
accesos y nada más**.

Eso parte `Lugar` por la mitad, y es la partición correcta: `accesos_y_salidas` es el único
campo suyo que lee una `bloqueante`. La atmósfera, las reglas locales y el tipo son material
para el **escritor**, no para la **puerta**. Son dos usos distintos del mismo objeto, y el
recorte tiene derecho a distinguirlos.

### El patrón, que ya no es casualidad

**Los bloques del contexto se definen por procedencia; las invariantes leen por necesidad.
Las dos particiones no coinciden.** Un bloque agrupa lo que viene del mismo sitio —del plan,
del estado, de la recuperación por similitud, de los resúmenes—; una invariante toma lo que
necesita para decidir, venga de donde venga. Cada vez que las dos líneas se cruzan, hay que
partir algo.

Van tres:

| Dónde | Qué se partió | Quién lo obligó |
| --- | --- | --- |
| `P-A` de `SPEC-01` | `Recuperado`: el registro de conocimiento se separó de las fichas y los setups | `INV-03` |
| `SPEC-13` | `Estado actual`: los hechos permanentes se separaron de los efímeros | El recorte, y `INV-02` por detrás |
| Esta spec | **`Lugar`**: el grafo de accesos se separó del resto de la ficha | `INV-02` |

**La tercera enseña algo que las dos primeras no:** la partición **no se detiene en el
borde de un bloque**. Puede entrar dentro de una clase y cortarla, porque lo que decide no
es de dónde viene el dato sino quién lo lee.

**Quien diseñe el cuarto bloque debería verlo venir en vez de descubrirlo.** La pregunta que
hay que hacerse al definir un bloque no es *"¿qué cosas vienen de aquí?"* sino *"¿qué de lo
que hay aquí lo lee una puerta?"*.

### C-3 ter · Lo que la regla ata de verdad

La regla suena amplia y **ata a dos invariantes**. De las cinco `bloqueante` de nivel
escena, solo dos leen bloques del contexto:

| | Qué lee | ¿Atada? |
| --- | --- | --- |
| `INV-01` | `Escena.cambio_de_valor` | No: campo de la propia escena |
| `INV-02` | `entidades_vivas`, `ubicaciones`, `Lugar.accesos_y_salidas` | **Sí** |
| `INV-03` | `RegistroDeConocimiento`, `t_fabula`, revelaciones del delta | **Sí** |
| `INV-04` | `Escena.pov` contra `Borrador.pov_usado` | No: compara la escena con su borrador |
| `INV-05` | `DeltaDeEscena`, `EstadoDelMundo` | No: mira después de generar |

**Esto se escribe para que nadie relaje la regla dentro de seis meses por miedo a un coste
que no existe.** Una regla que parece cara y no está medida se ablanda sola: alguien decide
que «conservarlo todo no cabe» sin haber mirado cuánto es todo. Son dos invariantes, y las
dos se concentran en los bloques 2.º y 4.º.

### C-4 · Los problemas del intento anterior entran en la ventana

`main` mete en la ventana del escritor los problemas del intento anterior. Ninguno de
nuestros seis bloques tiene sitio para eso, y **es el arreglo del hallazgo de las 944
palabras**: allí el aviso de longitud *"lo leía la sesión orquestadora y no el escritor"*,
así que en la reescritura siguiente el escritor no sabía nada de él.

Con `SPEC-10`, `Escena.intentos` cuenta y los hallazgos abiertos existen. Falta que lleguen
a quien tiene que corregirlos.

### C-5 · El orden se cambia por spec, nunca por configuración

`main` lo tiene en `config.json` (`contexto.orden_recorte`). **Aquí no**, y queda escrito
por qué:

- **Un orden configurable es un orden sin dueño.** Si alguien lo cambia para desatascar una
  generación, no queda rastro de por qué era el otro. El nuestro tiene razonamiento escrito
  por bloque, y eso es lo que permite discutirlo.
- **`VER-06` comprueba "el orden declarado".** Con configuración, pasaría a comprobar *"se
  respetó lo que dijera el fichero"*, que es un criterio que no puede marcar nada: `MF-24`
  otra vez.

Que el orden **se pueda cambiar** no está en discusión. Lo que se fija es por dónde: una
spec, con su razonamiento, no un parámetro que se ajusta sin revisarse.

## Qué queda explícitamente fuera

- **La tendencia de los recortes** (`REV-03` hallazgo `E`), que es el hueco 8 de `SPEC-11`.
  **Con una dependencia que conviene ver:** registrar si en la escena 40 hay recortes que no
  había en la 3 es lo único que dirá si este orden es el bueno. Hasta que exista, esta spec
  se aprueba por razonamiento, igual que la anterior.
- **El margen de la estimación de `C-3`.** Es un número y sale de medir.
- **Los hallazgos `D`, `E`, `F`, `H` e `I`** de `REV-03`: dos decididos en contra, dos en
  `SPEC-11` y uno que ya teníamos.
- **`RF-26` y el resto de `SPEC-01`** más allá de §2.4 y de lo que `C-4` obligue a tocar.

## Qué gobierna esto

§2.4 y `RF-06`, `RF-07` y `RF-26` de `SPEC-01`; el presupuesto por niveles de `CLAUDE.md`;
`VER-05`, `VER-06` y `VER-41`; `INV-03` y la respuesta a `P-A`; `MF-24`; y de la rama
`main`, `src/contexto.py` y el hallazgo 11 de `DECISIONES.md`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿Cuál es la forma reducida de cada bloque? | **Contestada**: la tabla de abajo, con el 4.º corregido. Su reducción **conserva el registro de conocimiento entero**; si no cabe, el bloque es irreducible. Reducirlo «a los hechos duraderos» sin más se lo habría llevado, y eso es rehacer `MF-05` por otra puerta: `INV-03` sin registro no es peor, es imposible |
| 2 | **Contestada.** `RF-26` falla hoy *"tras recortar los tres primeros bloques"*. Con dos vueltas, ¿dónde está ahora el límite? | Tras agotar **todas** las formas reducidas y eliminar los tres primeros bloques. Es más tarde que antes, y a propósito: con degradación se llega más lejos perdiendo menos |
| 3 | **Contestada.** ¿El número que estima el ensamblador es el mismo que reserva el presupuesto? | **No, y son tres, no dos.** Ver `C-3`. Si la reserva usara la estimación barata, reservaría mal; si el ensamblador contara exacto, pagaría el tokenizador en cada vuelta; y si la reserva y la traza compartieran número, `VER-41` volvería a ser el eco que `SPEC-08` cerró |
| 4 | **Contestada.** ¿Los problemas del intento anterior son un bloque nuevo? | Sí, bloque nuevo, y **de los últimos en recortarse**: si se van, la reescritura repite el error que la motivó. Meterlos en `Local` los haría caer con la escena anterior |
| 5 | **Contestada.** ¿Se parte `Estado actual` ahora? | **Ahora, y `HechoCanonico` gana un atributo de durabilidad**, que va por `SPEC-13` porque toca `Docs/definitions.md`. Certeza y durabilidad son ejes independientes: un hecho `establecido` puede ser efímero y uno `implicito` puede ser permanente, así que derivar una de la otra confundiría cuánto sabemos de algo con cuánto dura. `main` lo sufrió y nosotros tenemos `HechoCanonico.certeza` —`establecido`, `implicito`, `disputado`—, que **no es lo mismo que durabilidad**. Hace falta decidir cuál manda |

### Propuesta para la pregunta 1

| Orden | Bloque | Forma reducida | Irreducible |
| --- | --- | --- | --- |
| 1.º | Condensaciones de capítulo y de parte | Solo las de capítulo; se van las de parte | No |
| 2.º | Fichas de entidad y setups pendientes | **El grafo de accesos entre lugares** (`Lugar.accesos_y_salidas`) y nada más: se van las fichas enteras y los setups | No |
| 3.º | Escena anterior completa y resumen de las tres previas | **La escena anterior baja a su `Resumen`** | No |
| 4.º | Estado del mundo en `t` **y registro de conocimiento aplicable** | **El registro de conocimiento entero**, más solo los hechos duraderos del mundo (`C-2`). Si eso no cabe, el bloque es **irreducible** | Condicional |
| 5.º | Reserva de salida | — | **Sí.** Reducirla no es recortar contexto, es truncar la escena |
| 6.º | Premisa, guía de estilo, reglas del mundo, anclas | — | **Sí.** Sin esto no estás generando esta novela, estás generando otra |
| **Nuevo** | **Problemas del intento anterior** | Solo los de severidad `bloqueante` y `mayor` | No |

**Las cinco están contestadas el 2026-09-22.** `SPEC-12` **no se puede aplicar todavía**:
su `C-2` depende de que `HechoCanonico` tenga durabilidad, y eso es `SPEC-13`.

La del 3.º es la que copia directamente a `main` y la que más recupera: el bloque que más
ocupa deja de desaparecer y baja un escalón.


# Qué se tocó al aplicarla

§2.4 de `SPEC-01` reescrita entera, con siete bloques en vez de seis y su columna de forma
reducida; `RF-06` y `RF-26` al día; `VER-06` con el criterio de las dos vueltas; `SPEC-01`
sube a versión 5.

## La reserva, escrita en la propia §2.4

Este orden **se eligió razonando, no midiendo**, igual que la primera versión. Lo que dirá
si es el bueno es la tendencia de los recortes, y ese registro no existe todavía: la sección
lleva su marca **`Caduca con:`** apuntando a `SPEC-11`, así que `VER-56` hará fallar el
build el día que esa spec se aplique y haya que releer el orden con datos delante.
