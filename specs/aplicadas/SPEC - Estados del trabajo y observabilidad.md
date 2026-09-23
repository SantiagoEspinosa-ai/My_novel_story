---
id: SPEC-08
titulo: Los estados de un trabajo, y la traza que VER-41 necesita para no ser un eco
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: e7f0bee
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-08 — Estados del trabajo y observabilidad

## Qué problema resuelve

Dos infraestructuras del worker que sostienen requisitos de `SPEC-01` y que **ningún
documento describe**. No son lo mismo, pero comparten dueño —`commons/trabajos/` y
`commons/modelo/`—, ninguna toca el dominio, y las dos se descubrieron en la misma pasada.

### Problema 1 · Cinco afirmaciones sobre un conjunto de valores que nadie lista

| Afirmación | Qué supone |
| --- | --- |
| `RF-24` | Un trabajo es consultable «con **su estado**» |
| `O-4` | Los intentos consumidos y el motivo del último fallo son visibles por trabajo |
| `P-3` | Si no hay techo disponible, el trabajo **«espera en cola»** |
| `P-4` | **«Esperando presupuesto»** es un estado visible y **distinguible de «en curso»** |
| `docs/architecture.md` § "Cuando algo falla" | El trabajo pasa a **«un estado de fallo»** |

Cinco afirmaciones, cuatro nombres de estado sueltos en prosa y **ninguna enumeración**. Es
exactamente lo que pasó con `estado_de_capitulo`: la puerta se daba por existente porque
varios documentos la mencionaban, y no existía en ninguna parte.

### Problema 2 · `T-1` y `T-2` hablan de trazas que la arquitectura no menciona

`docs/architecture.md` no contiene ni una aparición de *traza*, *observabilidad* ni
*telemetría*. Mientras tanto:

- **`T-1`** exige que cada llamada a un agente deje traza consultable.
- **`T-2`** exige que una llamada que falla también la deje.
- **`VER-41`** reconcilia los tokens que registra la traza contra los que declara la
  respuesta del modelo.
- **`VER-34`** depende de `VER-41`: sin reconciliar, mediría sobre un dato sin validar.

**Y aquí está lo que de verdad importa.** `VER-41` es la **segunda fuente independiente**
que exige la Regla 3 de `docs/verification.md`. Si la traza se rellena desde el mismo sitio
que el contador de presupuesto, `VER-41` compara un número consigo mismo: pasa siempre, no
puede fallar, y **es un eco**. Entonces `PC-8` deja de ser *"el contador y el proveedor
podrían equivocarse igual"* y pasa a ser *"no hay segunda fuente en absoluto"*, que es un
punto ciego mucho mayor y que además nadie vería, porque el validador estaría en verde.

Es `MF-24` otra vez, en su forma más cara: un validador verde por construcción del que
además depende otro.

## Qué tiene que ser verdad al terminar

### C-1 · Los estados de un trabajo están enumerados en `docs/architecture.md`

Junto a la máquina de estados de la escena y a la del capítulo, en su **propia tabla** y
con su columna de quién dispara cada transición, igual que las otras dos.

**No van en `docs/definitions.md`**, y el motivo es el criterio de pertenencia: la tabla de
trabajos no existiría si la novela se escribiera a mano. No es dominio, es infraestructura,
y por eso ya vive en `commons/trabajos/`.

Los estados que las cinco afirmaciones exigen, como mínimo:

| Estado | Lo exige |
| --- | --- |
| `en_cola` | `P-3` |
| `esperando_presupuesto` | `P-4`, que además pide que sea **distinguible** del siguiente |
| `en_curso` | `P-4` |
| `terminado` | Implícito: un trabajo que acaba bien |
| `fallido` | `O-3`, `O-4`, `docs/architecture.md` § "Cuando algo falla" |

### C-2 · El trabajo abandonado, que es donde la lista se rompe

`docs/architecture.md` dice dos cosas sobre él que **no caben en un solo estado**:

> *"Un trabajo abandonado **se marca fallido** y no se reintenta solo."*
>
> *"Tampoco **cuenta contra el tope de reintentos**: no es un intento que falló, es un
> intento cuyo resultado no se conoce."*

Si se marca `fallido` como cualquier otro, la lógica del tope no puede distinguirlo. Hay
dos formas de resolverlo y la spec no elige: un **estado propio** —`abandonado`—, o un
**campo aparte** que diga por qué se marcó fallido. La diferencia no es cosmética: con
estado propio, `RF-24` devuelve algo que el frontend puede pintar distinto; con campo, no.

Esto es también por lo que `O-2` de `SPEC-01` quedó redactado sin nombrar el estado.

### C-3 · La traza, descrita en `docs/architecture.md`

Qué registra una llamada al modelo, para que `T-1`, `T-2` y `VER-41` tengan base:

- El agente, la escena y el trabajo.
- Los tokens, en los dos campos separados de `C-4`.
- El resultado, **incluido el fallo**: `T-2` exige que una llamada que falla también deje
  traza, y una traza que solo se escribe al terminar bien pierde justo los casos que
  interesan.

### C-4 · `VER-41` no puede ser un eco, y eso se diseña, no se confía

**La traza lleva los tokens en dos campos con procedencia distinta y caminos de escritura
distintos:**

| Campo | De dónde sale | Quién lo escribe |
| --- | --- | --- |
| `tokens_estimados` | El contador propio, **antes** de la llamada, que es el que reserva presupuesto según `P-2` | `commons/modelo/`, control de presupuesto |
| `tokens_declarados` | El `usage` de la respuesta del proveedor, **copiado literal** | El límite de transporte, al deserializar la respuesta |

Tres reglas que hacen que la independencia sea estructural y no una buena intención:

1. **`tokens_declarados` no se calcula nunca.** Se copia de la respuesta. Si no viene, se
   deja **ausente**, no en cero: un cero se lee como un dato y un hueco no.
2. **El código que calcula `tokens_estimados` no escribe `tokens_declarados`.** Es la
   condición que impide el eco, y es comprobable de forma estática.
3. **`VER-41` compara los dos campos.** Su criterio de salida cita los dos por nombre, para
   que se vea en la propia fila que son dos y no uno.

**Qué le pasa a `PC-8` con esto.** Sigue en pie tal como está: si el proveedor declara mal,
el contador propio y el suyo pueden coincidir en el mismo error, y `VER-41` no ve la
verdad. Lo que este diseño impide es que `PC-8` **crezca** hasta *"no hay segunda fuente"*,
que es una cosa distinta y mucho peor.

## Qué queda explícitamente fuera

- **El formato y el destino de la traza** —fichero, tabla, exportador—. Es del plan.
- **Los números**: retención de trazas, tamaño, muestreo.
- **Métricas de producto.** Esto es observabilidad del pipeline, no calidad de la novela;
  eso es `docs/verification.md`.
- **Los `RF` y endpoints que esto genere en `SPEC-01`.** Vienen después.
- **Reconciliar el coste en dinero.** `VER-36` lo necesitará; no entra aquí.

## Qué gobierna esto

`RF-24`, `O-2`, `O-3`, `O-4`, `P-2`, `P-3`, `P-4`, `T-1` y `T-2` de `SPEC-01`; `VER-41` y
`VER-34`, `PC-8`, `MF-24` y las Reglas 2 y 3 de `docs/verification.md`; `A-05` y la sección
"Cuando algo falla" de `docs/architecture.md`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | `C-2`: ¿el trabajo abandonado es un **estado propio** o un **campo** sobre `fallido`? | Estado propio, `abandonado`. `RF-24` lo devuelve y el frontend lo pinta distinto; con un campo, una interfaz que solo mire el estado los confunde y vuelve a relanzarlo a mano creyendo que falló |
| 2 | `C-1`: ¿la enumeración de estados de trabajo sigue las reglas de nombres de `docs/definitions.md` —ASCII, `snake_case`— aunque no viva ahí? | Sí. Es el mismo código leyendo el mismo tipo de valor; dos convenciones de nombres para lo mismo es lo que hizo divergir `juez LLM` de `juez_llm` |
| 3 | `C-1`: ¿deja esto un precedente incómodo, con vocabularios controlados en dos documentos? | Sí, y se asume: el criterio de pertenencia manda sobre la comodidad de tenerlos juntos. `docs/architecture.md` dice de dónde sale cada uno |
| 4 | `C-4`: ¿la regla 2 necesita su propio validador, o basta con que `VER-41` cite los dos campos? | Necesita validador. Una regla que nadie comprueba es una intención, y esta es precisamente la que impide que otro validador se vuelva un eco |
| 5 | `C-3`: ¿la traza de una llamada fallida registra también la entrada que la produjo? | **Sí, pero acotada.** `prompt_hash`, los identificadores que entraron con su `version_en_t`, los niveles y la salida que falló — no el contexto entero, que se reconstruye. La salida de un fallo de contrato sí va entera: es pequeña y no se reconstruye.

*(Nota de la aplicación: la propuesta original decía «Sí» a secas.)* Sí. Sin ella, `T-2` deja constancia de que algo falló y no de qué falló, y un fallo de contrato no se puede diagnosticar sin ver qué se mandó |


# 5. Qué se tocó al aplicarla

`docs/architecture.md` gana "Los estados de un trabajo" —con su tabla de transiciones, junto
a las de escena y capítulo— y "La traza de una llamada al modelo". `docs/definitions.md`
avisa en su sección de vocabularios de que hay uno fuera y dónde. `VER-41` cita los dos
campos por nombre.

## Lo que la spec no previó

**El contexto no era reconstruible desde el estado en `t`, como la respuesta 5 suponía.**
Al comprobarlo salió que `EstadoDelMundo` tiene `t` y `Ficha` tiene `version_en_t`, pero
que **la selección** no es reproducible —el índice vectorial crece al consolidar y los
empates KNN no tienen orden definido— y que **`Resumen` no tiene versión**. La respuesta 5
se aplicó con la selección guardada como identificadores, que cierra lo primero; lo segundo
necesita `SPEC-09` y queda anotado como decisión abierta.

**El `prompt_hash` detecta, no reconstruye**, y solo vivía en `Borrador`, que una llamada
fallida nunca produce. Pasa a vivir también en la traza.

**Quién detecta un trabajo abandonado no lo decidió ninguna respuesta.** `SPEC-07` fijó qué
se hace con él y no quién lo encuentra. La celda de esa transición queda vacía a propósito
y la pregunta, en las decisiones abiertas de `docs/architecture.md`.