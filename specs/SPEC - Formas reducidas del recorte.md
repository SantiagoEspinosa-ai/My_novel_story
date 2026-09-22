---
id: SPEC-12
titulo: El recorte deja de elegir qué se pierde y pasa a elegir cuánto se conserva
estado: en_revision
aprobada_por:
fecha_aprobacion:
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

### C-3 · Estimar para decidir y medir para verificar son dos números con dos nombres

§2.4 dice hoy cuándo recortar y no dice con qué cuenta. `main` lo resolvió y escribió el
motivo: `CARACTERES_POR_TOKEN = 4`, porque *"sin el tokenizador del proveedor no hay cuenta
exacta, y no la necesitamos: esto solo decide cuándo recortar, y para eso basta una
estimación conservadora"*.

| Pregunta | Qué necesita | Quién la hace |
| --- | --- | --- |
| **¿Recorto ya?** | Rápido y conservador. Una estimación con margen declarado | El ensamblador, en cada vuelta del bucle |
| **¿Me he pasado del límite?** | Exacto y **con segunda fuente** | `VER-05` y `VER-41`, después |

Los dos números **tienen nombres distintos** o alguien los reconciliará creyendo que son el
mismo. Un ensamblador que cuenta exacto para decidir si recorta paga el tokenizador en cada
iteración y no gana nada: lo que decide es *"me paso o no"*, no *"por cuánto"*.

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
| 1 | ¿Cuál es la forma reducida de cada bloque? | Ver la tabla de abajo. Es la pregunta gorda y la respuesta define la spec |
| 2 | `RF-26` falla hoy *"tras recortar los tres primeros bloques"*. Con dos vueltas, ¿dónde está ahora el límite? | Tras agotar **todas** las formas reducidas y eliminar los tres primeros bloques. Es más tarde que antes, y a propósito: con degradación se llega más lejos perdiendo menos |
| 3 | ¿El número que estima el ensamblador es el mismo que reserva el presupuesto por `P-2`? | **No.** Si la reserva usara la estimación barata, reservaría mal; si el ensamblador contara exacto, pagaría el tokenizador en cada vuelta. Son dos números y el segundo se calcula una vez, al final |
| 4 | `C-4`: ¿los problemas del intento anterior son un bloque nuevo o entran en uno existente? | Bloque nuevo, y **de los últimos en recortarse**: si se van, la reescritura repite el error que la motivó. Meterlos en `Local` los haría caer con la escena anterior |
| 5 | `C-2`: ¿se parte `Estado actual` en permanente y efímero ahora, o se declara la pregunta y se responde al implementar? | Ahora. `main` lo sufrió y nosotros tenemos `HechoCanonico.certeza` —`establecido`, `implicito`, `disputado`—, que **no es lo mismo que durabilidad**. Hace falta decidir cuál manda |

### Propuesta para la pregunta 1

| Orden | Bloque | Forma reducida | Irreducible |
| --- | --- | --- | --- |
| 1.º | Condensaciones de capítulo y de parte | Solo las de capítulo; se van las de parte | No |
| 2.º | Fichas de entidad y setups pendientes | Solo las entidades **presentes** en la escena; se van las mencionadas | No |
| 3.º | Escena anterior completa y resumen de las tres previas | **La escena anterior baja a su `Resumen`** | No |
| 4.º | Estado del mundo en `t` **y registro de conocimiento aplicable** | Solo los hechos duraderos (`C-2`) | No |
| 5.º | Reserva de salida | — | **Sí.** Reducirla no es recortar contexto, es truncar la escena |
| 6.º | Premisa, guía de estilo, reglas del mundo, anclas | — | **Sí.** Sin esto no estás generando esta novela, estás generando otra |
| **Nuevo** | **Problemas del intento anterior** | Solo los de severidad `bloqueante` y `mayor` | No |

La del 3.º es la que copia directamente a `main` y la que más recupera: el bloque que más
ocupa deja de desaparecer y baja un escalón.
