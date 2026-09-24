---
id: SPEC-29
titulo: Observabilidad en Langfuse, y qué sube y qué no
estado: aprobada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-23
fecha: 2026-09-23
version: 2
---

> **Historial.** v1: redactada con la respuesta del autor sobre el límite de lo
> que sube (2026-09-23), con `O-1` a `O-3` abiertas. v2: el autor elige la nube,
> confirma `O-2` y `O-3` y que los prompts vienen del repositorio. Sin cuestiones
> abiertas.

# SPEC-29 — Observabilidad en Langfuse

> **De dónde sale la decisión central**, en palabras del autor: *«Los prompts del
> sistema sí se versionan en Langfuse — el enunciado lo exige explícitamente y no
> son datos personales. Lo que queda fuera es el contenido de las respuestas y
> cualquier dato del destinatario. Así se cumple el enunciado sin romper el
> borrado de `SPEC-25`.»*

## Qué problema resuelve

`EXAMEN.md` §6 pide que cada novela sea una traza en Langfuse, con sesiones,
spans por rol y por tool, tokens, coste y latencia, scores de todos los
validadores y prompts versionados; §3 y §7 lo repiten para el coste y para las
coincidencias de palabras vetadas. Hoy **ninguna línea del código habla con
Langfuse**, y las specs que lo rozan lo dejan fuera (`SPEC-25`, `SPEC-26`): es
`EX-02` de `docs/cobertura-examen.md`.

La traza propia del backend (`docs/architecture.md` § "La traza de una llamada
al modelo") ya guarda tokens, modelo y resultado de cada llamada, y el sobre de
`claude -p` trae el coste real. Lo que falta es enviarlo, y decidir **qué no se
envía**.

## El límite: qué sube y qué no

| Sube a Langfuse | No sube |
| --- | --- |
| **Los prompts del sistema como plantilla**: el texto sin rellenar de cada rol y su versión | **El prompt tal como se envió**, porque lleva la ficha rellenada |
| Nombres de rol, de tool y de validador | **El contenido de las respuestas**: capítulos, planes, deltas, resúmenes, justificaciones del Editor, turnos de la entrevista |
| Tokens, coste, latencia y modelo de cada llamada | **Cualquier dato del destinatario**: nombre, edad, rasgos, recuerdos, texto libre, hechos propuestos |
| Identificadores opacos: obra, capítulo, escena, versión, trabajo | **Las vetadas por novela**, que las define el cliente y pueden ser el nombre de una persona |
| El resultado de cada validador: número o categoría | El fragmento que disparó un hallazgo, y los argumentos y la salida de una tool |
| Para una vetada: su **nivel** y un identificador, nunca el término si no es de la lista global | |

**Por qué.** `SPEC-25` `RF-21` borra la ficha al entregar la novela, y `VER-69`
declara su punto ciego: *lo que ya salió del proceso —las trazas de Langfuse—
no lo borra nadie*. Así que todo lo que sube tiene que ser algo que **no haga
falta borrar**. Una plantilla de prompt no lleva datos de nadie; un prompt
rellenado sí. La justificación del Editor cita el capítulo, y el capítulo lleva
al destinatario dentro: se queda en la base, y a Langfuse va la nota.

Consecuencia que conviene ver antes de aprobar: en Langfuse **no se podrá leer
qué escribió el modelo**. Para eso está la base, mientras la novela no se haya
entregado.

## Qué tiene que ser verdad al terminar

- **RF-01.** Una **sesión** de Langfuse por novela, que agrupa la entrevista, la
  generación y las regeneraciones posteriores.
- **RF-02.** Cada generación es una **traza**. Cada rol —entrevistador,
  planificador, revisor del plan, escritor, editor, resumidor— y cada llamada a
  una tool (`SPEC-28`) aparece como **span** con nombre identificable.
- **RF-03.** Tokens, coste y latencia **por llamada**, y agregados **por
  capítulo y por novela**. El coste es el que declara el sobre de cada llamada,
  no una estimación. **Un dato que no llegó se envía como ausente, nunca como
  cero**: un cero se lee como un dato y un hueco no.
- **RF-04.** El resultado de **cada validador** se envía como **score** asociado
  a su traza, con el nombre del validador (`INV-17`, `INV-21`…`INV-25`, schema,
  cada criterio del Editor, Lean). Un resultado «sin veredicto» —el `2` de Lean—
  se distingue de un aprobado.
- **RF-05.** Los prompts del sistema se **versionan en Langfuse**, y cada span
  dice qué versión de prompt lo produjo, de forma que la iteración de tuning
  (`SPEC-31`) pueda mostrar qué versión dio cada resultado.
- **RF-06.** Cada coincidencia de una palabra vetada queda en el audit log y en
  Langfuse, dentro del límite de arriba.
- **RF-07.** **El límite es comprobable.** Una prueba con datos de destinatario
  inventados recorre todo lo que se enviaría a Langfuse y no encuentra ninguno,
  igual que `VER-69` recorre las tablas. Un límite que solo está escrito no
  protege nada.
- **RF-08.** Las credenciales viven en `.env` y nunca en el repositorio;
  `.env.example` lista las variables.
- **RF-09.** Si Langfuse no responde, **la generación sigue** y la pérdida queda
  registrada. La observabilidad no puede tumbar una novela.

### Resuelto por el autor (v2)

- **RF-10 (antes `O-1`). Langfuse en la nube.** No había instancia; crearla es
  un paso del plan, con sus claves en `.env` (`RF-08`).
- **RF-11 (antes `O-2`). Los spans los envía el backend**, con los datos del
  sobre de cada `claude -p`. La exportación OTEL propia de Claude Code queda
  apagada; si algún día se enciende, su configuración tiene que respetar el
  límite, y eso se comprueba mirando Langfuse, no leyendo variables desde un
  subproceso.
- **RF-12 (antes `O-3`). La sesión la identifica un valor que nace con la
  entrevista** y que la obra hereda, porque la entrevista empieza antes de que
  exista la obra.
- **RF-13. La fuente de los prompts es el repositorio**, y Langfuse recibe cada
  versión. Lo contrario haría que el código dependiera de un servicio externo
  para arrancar.

## Qué queda explícitamente fuera

- **TLC**, que según el enunciado se ejecuta en desarrollo y no en cada
  generación.
- Paneles, alertas y retención dentro de Langfuse.
- Qué tools existen: es `SPEC-28`. Esta spec solo dice cómo se ven.

## Lo que la gobierna

`EXAMEN.md` §3, §5, §6 y §7; `SPEC-25` `RF-21` y `VER-69`; `SPEC-14` (los
agentes se ejecutan por delegación); `A-03`; y la traza de `docs/architecture.md`,
con sus dos campos de tokens (`VER-41`).
