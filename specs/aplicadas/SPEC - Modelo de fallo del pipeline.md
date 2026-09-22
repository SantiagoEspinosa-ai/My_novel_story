---
id: SPEC-07
titulo: Qué pasa cuando algo falla — modelo de fallo del pipeline
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: 4115f7a
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-07 — Modelo de fallo del pipeline

## Qué problema resuelve

**`Docs/architecture.md` describe únicamente el camino feliz.** Una búsqueda de `reintent`,
`timeout`, `a medias`, `parcial` y `expira` sobre sus 466 líneas no devuelve ninguna
aparición en ese sentido. El documento dice qué pasa cuando todo va bien y no dice nada
sobre qué pasa cuando no.

Eso no sería urgente si no fuera porque **`SPEC-01` ya se apoya en un modelo de fallo que
no existe**:

- **`O-3`** fija un tope de reintentos y una espera, y su §5.2 reconoce que el número sigue
  sin decidirse.
- **`RF-24`** promete que todo trabajo es consultable «con su estado, sus intentos
  consumidos y **el motivo del último fallo**». Ni los intentos ni el motivo están
  definidos en ninguna parte.

Aprobar `SPEC-01` sobre eso es aprobar una suposición. Por eso esta spec va antes.

Hay además una obligación que el propio documento se creó y no cumplió: **`A-05` eligió una
tabla de trabajos en SQLite frente a `BackgroundTasks` porque «un reinicio pierde el trabajo
en silencio»** — y después no dice qué pasa con un trabajo que un worker tomó y no terminó,
que es exactamente el caso del reinicio. La decisión resuelve la mitad del problema que
usa para justificarse.

## Qué tiene que ser verdad al terminar

### C-1 · La llamada al modelo falla: de qué estado sale la escena

Hoy la tabla de transiciones no tiene ninguna salida desde `planificada` ni desde
`generada` si la llamada falla. La escena se queda en un estado del que nadie la saca.

Hay que decidir **una** de estas formas, y la spec no la elige por su cuenta:

| Forma | Qué implica |
| --- | --- |
| **El fallo vive en el trabajo, no en la escena** | La escena se queda en `planificada` y el `Trabajo` pasa a un estado de fallo. `estado_de_escena` no cambia. No hay valor nuevo que añadir al dominio |
| **El fallo vive en la escena** | `estado_de_escena` necesita un valor nuevo, y eso es `Docs/definitions.md`, con su migración |

La primera parece más limpia porque `Trabajo` ya existe para esto, pero la decisión tiene
consecuencia en el frontend: `RF-23` dice que una escena se muestra siempre con su estado,
y si el fallo no está en el estado de la escena, hay que decir de dónde lo saca la interfaz.

### C-2 · Quién reintenta y con qué tope

Qué hay que fijar:

- **Quién decide reintentar**: el worker por su cuenta, el Orquestador, o una persona.
- **El tope**, que `O-3` deja abierto a la espera de «observar la tasa real de fallos
  transitorios» — y esa observación necesita que exista el sistema, así que o se fija un
  número provisional declarado como tal, o `O-3` no se puede implementar.
- **Qué se reintenta**: la llamada al modelo sola, o el trabajo entero desde el ensamblado
  del contexto. No es lo mismo: el contexto pudo cambiar entre medias.
- **Qué fallos se reintentan.** Un timeout de red y un delta fuera de esquema no son el
  mismo suceso. Reintentar el segundo repite el error.

### C-3 · El trabajo que un worker tomó y no terminó

La obligación que crea `A-05`. Qué hay que fijar:

- **Cómo se detecta.** Un trabajo tomado y sin terminar solo se distingue de uno en curso
  por el tiempo. Eso implica marcar cuándo se tomó y fijar a partir de cuándo se considera
  abandonado.
- **Quién lo recupera** al arrancar: el worker, un barrido aparte, o una persona.
- **Si se reintenta o se marca fallido.** Un trabajo abandonado pudo haber llamado al
  modelo y haber cobrado; reintentarlo a ciegas paga dos veces.
- **Si cuenta contra el tope de `C-2`.**

### C-4 · El delta aplicado a medias

El peor de los cuatro, porque corrompe el estado en vez de detener el trabajo.

`INV-05` exige que el delta esté aplicado antes de generar la escena siguiente, y
`Docs/architecture.md` dice que ahí es «donde se corta la propagación del error». Pero si
el Consolidador falla a mitad, el estado queda entre dos mundos y **`INV-05` lo dará por
aplicado o por no aplicado según cómo se mire**, que es justo lo que la invariante existe
para impedir.

Qué hay que fijar: si la aplicación del delta es atómica —una transacción, y entonces hay
que decirlo aquí porque es arquitectura y no detalle—, o si se admite aplicación parcial y
entonces hace falta un mecanismo de reparación y una forma de detectar el estado a medias.

## Qué queda explícitamente fuera

- **Los números**: tope de reintentos, tiempo de espera, tiempo tras el cual un trabajo se
  considera abandonado. Salen de medir, y no hay nada que medir todavía.
- **Reintentos del lado del cliente HTTP.** Esta spec es sobre el worker y la cola.
- **Qué pasa si el modelo devuelve algo sintácticamente válido y semánticamente inútil.**
  Eso no es un fallo del pipeline: lo cazan las puertas.
- **Los `RF` y endpoints que esto genere en `SPEC-01`.** Vienen después, como con `SPEC-04`.

## Qué gobierna esto

`A-05` (cola en tabla de SQLite, y la obligación que crea), `INV-05` (el delta aplicado
antes de seguir), `O-3` y `RF-24` de `SPEC-01`, y `RF-23` para la parte de `C-1` que toca
al frontend.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | `C-1`: ¿el fallo vive en el `Trabajo` o en la escena? | En el `Trabajo`. `Trabajo` ya existe para esto y no toca el dominio ni pide migración. A cambio hay que decir de dónde saca el frontend el motivo del fallo |
| 2 | `C-2`: ¿quién decide reintentar? | El worker, y solo para fallos de transporte —timeout, corte, límite de tasa—. Un delta fuera de esquema no se reintenta: se marca fallido y lo ve una persona |
| 3 | `C-2`: ¿tope provisional, o `O-3` se queda sin implementar? | Tope provisional **declarado como provisional**, con su marca `Caduca con:` de `SPEC-05`. Un número sin medir que no se declara es lo que esa spec existe para impedir |
| 4 | `C-3`: ¿un trabajo abandonado se reintenta o se marca fallido? | Se marca fallido y no se reintenta solo. Pudo haber llamado al modelo y cobrado, y reintentar a ciegas paga dos veces sin saberlo |
| 5 | `C-4`: ¿la aplicación del delta es atómica? | Sí, y se escribe en `Docs/architecture.md`. Sin atomicidad, `INV-05` no significa nada: un delta a medias es un estado que la invariante no sabe clasificar |
| 6 | `RF-24` promete "el motivo del último fallo": con varios trabajos fallidos por escena, ¿devuelve el último o todos? | **El último fallo más el recuento de intentos.** El historial completo queda en los trabajos para quien lo necesite, pero la respuesta por defecto no lo arrastra |

Las seis se respondieron con la propuesta el 2026-09-22, al aprobar.

# 5. Qué se tocó al aplicarla

Solo `Docs/architecture.md`, que gana la sección "Cuando algo falla" con sus tres
subsecciones. **No se tocó `Docs/definitions.md`**, y esa es la confirmación literal de la
respuesta 1: al comprobarlo se vio que **la tabla de trabajos no es una clase del dominio**
—no aparece en `definitions.md` y vive en `commons/trabajos/`—, así que poner el fallo ahí
no añade ningún valor de enumeración ni pide migración. Tampoco gana filas la tabla de
transiciones: un fallo no es una transición del dominio, es un intento que no produjo nada.

## Lo que la spec no previó

**Los dos números quedan sin fijar, y se declara.** `C-2` decía que los números quedaban
fuera de alcance y la respuesta 3 pedía un tope provisional: las dos cosas no caben juntas.
Se resolvió separando el mecanismo del valor —`Docs/architecture.md` decide que el tope
**existe** y que es provisional declarado, y el número se fija en el plan con su marca
`Caduca con:`—. Lo mismo para el margen a partir del cual un trabajo se considera
abandonado, que la spec ni siquiera mencionaba como número y lo es.
