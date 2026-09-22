---
id: SPEC-01
titulo: Backend del harness — primera versión
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-21
version: 3
---

# SRS — Backend del harness de novelas

Especificación de requisitos del **backend**: el servicio que ejecuta el proceso de
generación y verificación de escenas descrito en `Docs/`.

## Qué es y qué no es este documento

**Es** la spec del backend, y solo del backend. Un documento, una spec: `SPEC-01`. El
frontend, la interfaz de puertas y cualquier otra pieza tendrán su propia spec, en su
propio fichero dentro de `specs/`.

**No es** una redefinición del dominio ni del proceso. El dominio está en
`Docs/definitions.md` y el proceso en `Docs/domain-knowledge.md` y `Docs/architecture.md`. Este
documento los toma como dados y especifica **qué tiene que hacer el backend para
ejecutarlos**.

**Precedencia.** Aquí se repiten cosas que ya están en `CLAUDE.md` y en `Docs/definitions.md`
para que el documento se pueda leer solo. Si alguna vez discrepan, **gana el original** y
este se corrige: `CLAUDE.md` en lo técnico, `Docs/definitions.md` en lo de dominio,
`Docs/architecture.md` en cómo se organiza el código.

| ID | Estado | Aprobada por | Fecha |
| --- | --- | --- | --- |
| `SPEC-01` | `en_revision` | — | — |

Sin `aprobada` no se escribe `specs/plans/PLAN-01.md` ni código.

---

# 1. Introducción

## 1.1 Propósito

Especificar la **primera versión del backend** del harness: el servicio FastAPI que
planifica, genera, verifica y consolida escenas de una novela, y que mide lo que produce.

Esta versión no busca una novela completa. Busca **llevar una escena de principio a fin
con todas las puertas cerrándose de verdad**, que es lo más pequeño que ejercita la
arquitectura entera: presupuesto de contexto, agentes, invariantes, delta y reconstrucción
de estado. Un sistema que hace eso una vez, lo hace cien veces; uno que no, no escala por
mucho que genere texto.

## 1.2 Alcance

**Entra** el recorrido vertical de una escena:

| Paso | Qué hace |
| --- | --- |
| `brief` | Dar de alta la obra: premisa, tono, guía de estilo, prohibiciones |
| `escaleta` | Planificar las escenas antes de escribirlas |
| `contexto` | Ensamblar el contexto de una escena dentro del presupuesto |
| `generacion` | Producir el borrador y el delta propuesto |
| `verificacion` | Pasar las puertas: reglas deterministas y juez |
| `consolidacion` | Aplicar el delta y resumir |
| `orquestacion` | Componer lo anterior y mover la máquina de estados |
| `commons` | Configuración, base de datos, enumeraciones, cliente del modelo, invariantes, trabajos |

**No entra**, y no por olvido:

| Fuera | Por qué |
| --- | --- |
| `revision/` (pases dirigidos) | Una escena puede recorrerse entera sin reescrituras dirigidas. Tiene consecuencias en §2.2.3 |
| `auditoria/` (invariantes de obra) | `INV-06`, `INV-09`, `INV-11`, `INV-12`, `INV-13` e `INV-16` necesitan la obra entera; con una escena no se pueden ejercitar |
| `lectura/` más allá de lo mínimo | Solo se exponen las consultas que el recorrido necesita |
| El frontend React | Esta versión se maneja por API. Es otra spec, en su propio fichero |
| Generar la novela completa | El objetivo es la escena, no el volumen |

## 1.3 Definiciones

Literales de `Docs/definitions.md`. No admiten sinónimos ni traducción.

| Término | Qué es |
| --- | --- |
| **Escena** | Unidad atómica: bloque continuo de tiempo y espacio con un cambio de valor. Es lo que se genera, se verifica y se recupera |
| **Cambio de valor** | Par `{eje, signo}` que toda escena mueve. Si no cambia nada, la escena sobra |
| **DeltaDeEscena** | Diff estructurado que la escena devuelve junto al texto: muertes, movimientos, revelaciones, setups pagados, cambios de posesión, deterioros |
| **EstadoDelMundo** | Instantánea del canon en `t`. No se redacta: se reconstruye acumulando deltas en orden |
| **RegistroDeConocimiento** | Quién sabe qué y desde cuándo. El sujeto puede ser personaje, narrador o lector |
| **Ficha** | Resumen recuperable de una entidad, para inyectar en contexto |
| **Hallazgo** | Defecto detectado, con su verificador, su escena y su severidad |
| **Puerta** | Condición que un artefacto debe pasar para avanzar |
| **Trabajo** | Unidad de trabajo asíncrono registrada en la base de datos |
| `INV-xx` | Invariante verificable de `Docs/definitions.md` |
| `VER-xx` | Fila del plan de verificación de `Docs/verification.md` |
| `A-xx` | Decisión de arquitectura de `Docs/architecture.md` |

## 1.4 Referencias

| Documento | Qué aporta |
| --- | --- |
| `CLAUDE.md` | Stack, límite de contexto y su reparto por niveles, reglas de Pydantic y enumeraciones, persistencia |
| `Docs/definitions.md` | Clases, atributos, vocabularios controlados e invariantes `INV-01`…`INV-16` |
| `Docs/domain-knowledge.md` | **El proceso**: ciclo de vida de la escena y secuencia de generación |
| `Docs/architecture.md` | Decisiones `A-01`…`A-09`, estructura por feature, agentes y quién dispara cada transición |
| `Docs/verification.md` | Modos de fallo `MF-01`…`MF-23` y validadores `VER-01`…`VER-55`, cada uno con su punto ciego |

---

# 2. Descripción general

## 2.1 Perspectiva del producto

```mermaid
flowchart LR
  C["Cliente HTTP<br/>(el frontend llega en otra spec)"]
  API["FastAPI<br/>features + commons"]
  W["Worker<br/>mismo proceso"]
  M["Modelo de lenguaje"]
  DB[("SQLite<br/>estado + embeddings + trabajos")]
  C -->|HTTP/JSON| API
  API --> DB
  W -->|toma trabajos| DB
  W --> M
  W --> DB
```

Dos papeles en un solo proceso: **la API responde rápido y no llama nunca al modelo**; el
worker consume trabajos de la base y sí lo llama. Una sola base de datos, sin servicio de
vectores aparte ni cola externa.

## 2.2 El proceso que ejecuta el backend

Esta sección no inventa nada: recoge el proceso tal como está en `Docs/` y dice qué parte
cubre esta versión. Es el corazón del documento, porque todos los requisitos del §3
existen para que este proceso se ejecute bien.

### 2.2.1 Ciclo de vida de una escena

Los estados son la enumeración `estado_de_escena` de `Docs/definitions.md`:

```mermaid
stateDiagram-v2
  [*] --> Planificada
  Planificada --> Generada: modelo escribe
  Generada --> EnVerificacion: puerta
  EnVerificacion --> Rechazada: falla regla bloqueante
  EnVerificacion --> EnRevision: juez marca
  Rechazada --> Generada: regenera
  EnRevision --> Generada: reescribe
  EnVerificacion --> Aceptada: pasa todo
  Aceptada --> Consolidada: aplica delta
  Consolidada --> [*]
```

Quién dispara cada transición, según `Docs/architecture.md`:

| Transición | Quién la dispara | Condición | ¿En la v1? |
| --- | --- | --- | --- |
| `planificada` → `generada` | Worker | El Escritor devuelve borrador y delta | Sí |
| `generada` → `en_verificacion` | Orquestador | Automática | Sí |
| `en_verificacion` → `rechazada` | Verificador de reglas | Falla una invariante `bloqueante` | Sí |
| `en_verificacion` → `en_revision` | Juez de rúbrica | Hallazgo `mayor` o `menor` | **No**, ver §2.2.3 |
| `en_verificacion` → `aceptada` | Orquestador | Pasa todas las puertas | Sí |
| `rechazada` → `generada` | Cliente de la API | Regeneración | Sí |
| `en_revision` → `generada` | Revisor | Reescritura dirigida | **No**, con `revision/` |
| `aceptada` → `consolidada` | Consolidador | Delta aplicado sin conflicto | Sí |

**La transición que importa es `aceptada` → `consolidada`.** Hasta que el delta no está
aplicado, el estado del mundo no ha cambiado y la escena siguiente no puede generarse. Es
donde se corta la propagación del error, y es también la frontera entre memoria a corto y
largo plazo (`M-2`).

### 2.2.2 Secuencia de una escena

```mermaid
sequenceDiagram
  participant C as Cliente
  participant API as FastAPI
  participant T as Tabla de trabajos
  participant W as Worker
  participant CTX as Ensamblador
  participant E as Escritor
  participant VR as Verificador de reglas
  participant J as Juez
  participant CO as Consolidador
  C->>API: POST /escenas/{id}/generar
  API->>T: inserta trabajo
  API-->>C: 202 + id_trabajo
  W->>T: toma el trabajo
  W->>CTX: pide contexto
  CTX-->>W: contexto dentro del presupuesto
  W->>E: prompt + contexto
  E-->>W: borrador + delta propuesto
  W->>VR: puerta determinista
  VR-->>W: hallazgos con su INV-xx
  W->>J: puerta de rúbrica (sesión limpia)
  J-->>W: puntuación + hallazgos
  W->>T: resultado del trabajo
  C->>API: GET /escenas/{id}
  API-->>C: texto, estado, hallazgos abiertos
  C->>API: POST /escenas/{id}/aceptar
  API->>CO: aplica delta y resume
```

Dos cosas que el proceso fija y que el §3 convierte en requisitos: **el Escritor devuelve
texto y delta en la misma llamada** —pedir el delta después, releyendo la escena, es más
caro y menos fiel—, y **la aceptación la dispara un cliente, no el worker**: la puerta la
cierra alguien.

### 2.2.3 Qué parte del ciclo cubre la v1, y una inconsistencia que hay que resolver

Como `revision/` queda fuera del alcance, el camino
`en_verificacion` → `en_revision` → `generada` **no existe en esta versión**. Eso obliga a
decidir qué pasa cuando el Juez levanta un hallazgo `mayor` o `menor`, y ahí los
documentos no dicen lo mismo:

| Documento | Qué dice |
| --- | --- |
| `CLAUDE.md` § Reglas de trabajo | *"`mayor` y `menor` generan hallazgo y dejan seguir"* |
| `Docs/architecture.md` § transiciones | `en_verificacion` → `en_revision` disparada por un hallazgo `mayor` o `menor` |

No pueden ser las dos: si va a `en_revision`, no sigue.

**Suposición de la v1, a confirmar al aprobar esta spec:** se sigue `CLAUDE.md`, que manda
en lo técnico. Un hallazgo `mayor` o `menor` **no** bloquea: la escena puede alcanzar
`aceptada` con el hallazgo abierto y visible. `en_revision` entra cuando entre `revision/`,
y entonces será una decisión del cliente mandar allí una escena, no un automatismo del
Juez. Queda anotado en §5.3 para cerrarlo en `Docs/architecture.md`.

## 2.3 Funciones principales

1. Dar de alta una obra a partir de un brief.
2. Planificar una escaleta de escenas.
3. Ensamblar el contexto de una escena sin pasarse del presupuesto.
4. Generar el texto de la escena y su delta en la misma llamada.
5. Verificar la escena contra las invariantes aplicables y producir hallazgos.
6. Aceptar o rechazar la escena, y al aceptarla aplicar el delta y resumir.
7. Informar del estado de todo lo anterior, incluidos los trabajos en curso.

## 2.4 Restricciones

De `CLAUDE.md`, no negociables desde aquí:

| Restricción | Detalle |
| --- | --- |
| Backend | FastAPI. Único servicio HTTP. Nada de lógica de dominio fuera de él |
| Persistencia | SQLite con extensión vectorial. Una sola base. Sin servicio de vectores externo |
| Contexto | 100.000 tokens, salida incluida. Ver `RNF-P` |
| Asincronía | Las llamadas al modelo son asíncronas: el endpoint arranca un trabajo y devuelve su identificador |
| Validación | Los modelos Pydantic son la frontera y replican las clases de `Docs/definitions.md`. Un campo que no está allí no entra en un esquema |
| Vocabularios | Los valores cerrados son `Enum`. Un valor fuera de la enumeración es un error de validación, no un aviso |

Reparto del presupuesto por nivel, tal como está hoy en `CLAUDE.md`:

| Nivel | Presupuesto | Contenido |
| --- | --- | --- |
| Inmutable | 15.000 | Premisa, guía de estilo, reglas del mundo, anclas de estilo |
| Estado actual | 10.000 | Instantánea del mundo en el momento de la escena |
| Local | 25.000 | Escena anterior completa y resumen de las tres previas |
| Recuperado | 20.000 | Fichas de entidades presentes, setups pendientes, registro de conocimiento aplicable |
| Resúmenes | 10.000 | Condensaciones de capítulo y de parte |
| Salida | 20.000 | Reserva para el texto generado y su delta |

**Suma exactamente 100.000.** Esa igualdad tiene consecuencias en `P-5`.

### Orden de recorte

`CLAUDE.md` dice que se recorta *"por el nivel de menor prioridad"* y no dice cuál es.
Este es el orden, y **también modifica `CLAUDE.md`**, igual que `P-1`.

El criterio no es cuánto ocupa cada nivel, sino **qué se pierde si falta**:

El orden opera sobre **bloques**, no sobre niveles, porque `Recuperado` se parte en dos:
sus fichas y setups se recortan pronto y su registro de conocimiento no.

| Orden | Bloque | Nivel del que sale | Qué se pierde |
| --- | --- | --- | --- |
| 1.º | Condensaciones de capítulo y de parte | Resúmenes | Son condensaciones de condensaciones. Perderlas degrada el contexto lejano, que es el que menos afecta a la escena en curso |
| 2.º | Fichas de entidad y setups pendientes | Recuperado | Duele, pero es recuperable después y no rompe nada de inmediato |
| 3.º | Escena anterior completa y resumen de las tres previas | Local | Aquí ya se nota: el texto pierde continuidad de tono y de ritmo |
| 4.º | Estado del mundo en `t` **y registro de conocimiento aplicable** | Estado actual + Recuperado | Sin el primero el modelo inventa dónde está la gente. Sin el segundo, `INV-03` no es peor: es **imposible** |
| 5.º | Reserva de salida | Salida | Recortar aquí no es recortar contexto: es **truncar la escena** |
| 6.º | Premisa, guía de estilo, reglas del mundo, anclas | Inmutable | **Nunca.** Sin esto no estás generando esta novela, estás generando otra |

**Por qué el registro de conocimiento sube a la cuarta posición y no se queda con el resto
de `Recuperado`.** `INV-03` es `bloqueante` y **depende de ese dato**. Si se recorta en
segunda posición, el recorte se lo lleva antes de que la regla de fallar por debajo del
nivel 3 llegue a activarse, y la puerta queda en pie pero sin la información con la que
juzgar: sigue ahí, y ya no puede decidir. El criterio es el mismo que para el estado del
mundo —sin él la comprobación no es peor, es imposible—, así que va en el mismo bloque.

**Por debajo del nivel 3 no se recorta: se falla.** Una escena escrita sin la anterior y
sin el estado del mundo va a salir mal y va a consumir una regeneración igualmente, así
que fallar antes es más barato que generar y tirar. En la práctica eso hace que los
niveles 4, 5 y 6 no se toquen nunca: el ensamblador se detiene antes de llegar a ellos.

## 2.5 Suposiciones y dependencias

- Una sola obra y un solo usuario. Sin multi-tenencia ni autenticación.
- Un único worker, en el mismo proceso que la API.
- El modelo de lenguaje es un servicio externo que puede fallar y tardar.
- La extensión vectorial de SQLite está disponible en el entorno de despliegue.
- **No hay ninguna medición previa** de tokens, coste ni latencia de este sistema. Todo
  requisito que necesitaría un número lo declara pendiente en vez de inventarlo.

---

# 3. Requisitos

## 3.1 Requisitos funcionales

### Alta de obra y escaleta

| ID | Requisito | Verifica |
| --- | --- | --- |
| **RF-01** | Se puede crear una `Obra` a partir de un `Brief` con premisa, tono, guía de estilo y prohibiciones. Los campos obligatorios de `Docs/definitions.md` son obligatorios aquí | — |
| **RF-02** | Se genera una `Escaleta`: lista ordenada de escenas planificadas, cada una con su `cambio_de_valor` previsto, su `pov`, su `lugar`, su `objetivo_dramatico` **y los `Beat` que realiza, cada uno ligado al `ArcoNarrativo` al que sirve** | `INV-01`, `INV-07` |
| **RF-03** | Toda escena de la escaleta nace en estado `planificada` | — |
| **RF-04** | La generación de la escaleta es asíncrona: devuelve un identificador de trabajo | — |

### Ensamblado de contexto

| ID | Requisito | Verifica |
| --- | --- | --- |
| **RF-05** | Antes de cada llamada al modelo se ensambla el contexto por niveles y **se comprueba que cabe en el presupuesto** | `VER-05` |
| **RF-06** | Si no cabe, se recorta siguiendo el **orden de recorte de §2.4**: condensaciones, después fichas y setups, después la escena anterior. Nunca truncando por el final ni partiendo un bloque | `VER-06` |
| **RF-07** | El contexto nunca incluye el texto completo de la obra. Solo la escena anterior entra en texto completo | `VER-07` |
| **RF-08** | Cada agente recibe únicamente los niveles que le corresponden según `Docs/architecture.md` | — |
| **RF-26** | **Si tras recortar los tres primeros bloques el contexto sigue sin caber, el trabajo falla en vez de generar.** No se tocan el estado del mundo, el registro de conocimiento, la reserva de salida ni el nivel inmutable | `VER-06` |

### Generación

| ID | Requisito | Verifica |
| --- | --- | --- |
| **RF-09** | El Escritor devuelve **texto y `DeltaDeEscena` en la misma respuesta**. Una respuesta sin delta, o con delta fuera de esquema, se rechaza antes de llegar a las puertas | `VER-20` |
| **RF-10** | La escena pasa a `generada` cuando el Escritor devuelve borrador y delta válidos | — |
| **RF-11** | Cada `Borrador` conserva su versión, el modelo usado y el `prompt_hash`, para poder reproducir de dónde salió | — |

### Verificación

| ID | Requisito | Verifica |
| --- | --- | --- |
| **RF-12** | Las comprobaciones deterministas las ejecuta **código**, no un juez. El reparto entre regla y juez es el de la columna `Tipo` de `Docs/definitions.md` y no se reinterpreta caso por caso | — |
| **RF-13** | Se ejecutan las invariantes de nivel escena: `INV-01`, `INV-02`, `INV-03`, `INV-04`, `INV-05`, `INV-07`, `INV-10` | `VER-10`, `VER-11` |
| **RF-14** | Un fallo `bloqueante` detiene la escena en la puerta: no puede pasar a `aceptada`. `mayor` y `menor` generan `Hallazgo`, dejan seguir y el hallazgo queda abierto (ver §2.2.3) | `VER-11` |
| **RF-15** | Todo `Hallazgo` cita su invariante **por identificador** (`INV-07`), nunca por descripción | `VER-12` |
| **RF-16** | El Juez recibe el texto y la rúbrica, **no** el prompt ni el razonamiento del Escritor | `VER-25` |

### Aceptación y consolidación

| ID | Requisito | Verifica |
| --- | --- | --- |
| **RF-17** | La aceptación la dispara un cliente, **nunca el worker por su cuenta** | `VER-29` |
| **RF-18** | Al aceptar, el delta se aplica al estado del mundo y la escena pasa a `consolidada` | `INV-05`, `VER-10` |
| **RF-19** | **Ninguna escena posterior puede generarse mientras la anterior no esté `consolidada`** | `INV-05` |
| **RF-20** | Un delta incompatible con el estado en `t` no se aplica: produce hallazgo y la escena no se consolida | `INV-06` |
| **RF-21** | Al consolidar se produce el `Resumen` de la escena y se actualizan las `Ficha` de las entidades afectadas | — |
| **RF-22** | Al consolidar se indexan por similitud las fichas, el resumen y los presagios pendientes. **El texto completo se guarda pero no se indexa** | `VER-08` |

### Estado y trabajos

| ID | Requisito | Verifica |
| --- | --- | --- |
| **RF-23** | Consultar una escena devuelve siempre texto, **estado** y **hallazgos abiertos** juntos. Nunca el texto solo | `VER-18` |
| **RF-24** | Todo trabajo es consultable por su identificador, con su estado, sus intentos consumidos y el motivo del último fallo | `VER-04` |
| **RF-25** | Un dato que no se ha medido se devuelve como ausente y distinguible de cero | `VER-19` |

## 3.2 Interfaces externas

### 3.2.1 API HTTP

Contratos, no implementación. Los nombres de campo replican `Docs/definitions.md`.

| Método | Ruta | Entrada | Salida | Códigos |
| --- | --- | --- | --- | --- |
| `POST` | `/obras` | `Brief` | `Obra` con su `id` | 201, 422 |
| `GET` | `/obras/{id}` | — | `Obra` con partes, capítulos y escenas con su estado | 200, 404 |
| `POST` | `/obras/{id}/escaleta` | parámetros de planificación | `{id_trabajo}` | 202, 404, 409 |
| `GET` | `/escenas/{id}` | — | texto, `estado`, `cambio_de_valor`, delta propuesto, hallazgos abiertos | 200, 404 |
| `POST` | `/escenas/{id}/generar` | — | `{id_trabajo}` | 202, 404, 409 |
| `POST` | `/escenas/{id}/aceptar` | — | `Escena` consolidada | 200, 404, 409 |
| `POST` | `/escenas/{id}/rechazar` | motivo | `Escena` en `rechazada` | 200, 404, 409 |
| `GET` | `/trabajos/{id}` | — | estado, intentos, motivo del último fallo | 200, 404 |
| `GET` | `/trabajos` | filtro por estado | lista de trabajos | 200 |

Reglas transversales:

- **Ningún endpoint que llame al modelo responde de forma síncrona.** Devuelve `202` con
  un identificador de trabajo.
- **`409`** cuando la transición pedida no es legal en el estado actual de la escena; el
  cuerpo dice qué estado tiene y cuál se esperaba.
- **`422`** es la validación de Pydantic, incluidos los valores fuera de una enumeración.

### 3.2.2 Modelo de datos

Qué tablas existen y para qué. La DDL, los índices y las migraciones son del plan.

| Tabla | Contiene | Notas |
| --- | --- | --- |
| `obra`, `parte`, `capitulo` | Jerarquía estructural | `contiene` como clave foránea |
| `escena` | Los atributos obligatorios de `Escena`, con `POV` y `MomentoNarrativo` **embebidos como columnas** | Las dos son objetos de valor 1:1 (`narrada_desde` y `situada_en` son `1:1`), así que no necesitan tabla propia: 8 columnas |
| `beat`, `arco_narrativo` | Las dos entidades que `INV-07` necesita | Son `N:M` con `Escena` y entre sí, así que sí necesitan tabla |
| `escena_realiza_beat`, `beat_sirve_a_arco` | Las dos uniones | Materializan las relaciones `realiza` y `sirve_a` |
| `borrador` | Texto por versión, modelo y `prompt_hash` | Varios por escena |
| `delta_de_escena` | El diff estructurado por escena | Fuente de verdad del estado |
| `estado_del_mundo` | Instantánea materializada en `t` | Derivada: reconstruible desde los deltas |
| `personaje`, `lugar`, `objeto` | Entidades del canon | — |
| `hecho_canonico`, `registro_de_conocimiento` | Verdad y quién la sabe | `registro_de_conocimiento` sostiene `INV-03` |
| `presagio` | Setups plantados y su estado | Se indexa por similitud |
| `resumen`, `ficha`, `ancla_de_estilo` | Memoria a largo plazo | Se indexan por similitud |
| `hallazgo` | Defectos con su `INV-xx`, severidad y estado | — |
| `trabajo` | Cola y estado de los trabajos asíncronos | Soporte de `O-1` y `O-2` |
| Tablas `vec0` | Embeddings de fichas, resúmenes y presagios | **No** del texto de escena |

**El coste de `beat` y `arco_narrativo` no son dos tablas.** Alguien tiene que
**rellenarlas**, y ese alguien es el Escaletador: su salida pasa de una lista de escenas
con sus campos a una lista de escenas **con sus beats, y cada beat ligado al arco al que
sirve**. Eso hace su prompt más largo, su salida más grande y su validación más estricta,
y es trabajo que hoy no hace nadie. Reconocerlo aquí es parte de la decisión, no una nota
al pie.

Entran en la v1 no por completitud, sino por **el tipo de defecto que detectan**. `INV-07`
es lo único que distingue una escena necesaria de una de relleno, y ese fallo **no se ve
escena a escena**: se ve al leer la novela entera y notar que no avanza. Es el más caro de
descubrir tarde, porque cuando se nota ya hay treinta mil palabras escritas. Y sacarlo del
alcance tampoco habría cerrado el hueco: `pov` y `momento_narrativo` son atributos
obligatorios de `Escena` y seguirían sin tener dónde vivir.

### 3.2.3 Interfaz con el modelo de lenguaje

Cada agente es una llamada con contexto propio y salida tipada (`A-03`).

| Agente | Recibe | Devuelve | Validación |
| --- | --- | --- | --- |
| Escaletador | Brief, guía de estilo, estado, recuperado, resúmenes | `Escaleta`, **con sus `Beat` y los `ArcoNarrativo` a los que sirven** | Esquema Pydantic; rechazo si falla |
| Escritor | Los niveles que le tocan | Texto **y** `DeltaDeEscena` | Rechazo si falta el delta |
| Juez | Texto y `Rubrica`, sin el prompt del Escritor | Puntuación y `Hallazgo[]` | Rechazo si falla |
| Resumidor | La escena consolidada | `Resumen` y `Ficha` actualizadas | Rechazo si falla |

## 3.3 Requisitos no funcionales

Los identificadores `O-`, `M-`, `P-` y `T-` se conservan de la versión 1. No se renumeran.

### Orquestación (`RNF-O`)

- **O-1.** Cada transición de la máquina de estados es un trabajo registrado en la tabla
  de trabajos. El Orquestador **no guarda estado en memoria del proceso**.
- **O-2.** Un reinicio del servidor a mitad de una escena no pierde el progreso: al
  arrancar, el trabajo pendiente se retoma desde la última transición registrada.
- **O-3.** Los fallos **transitorios** (red, timeout) se reintentan con espera creciente y
  un tope acotado de intentos. Los fallos **de contrato** (salida fuera de esquema) **no**
  se reintentan: el trabajo queda marcado como fallido y visible. Reintentar a ciegas un
  fallo de contrato suele limitarse a repetirlo y a gastar llamadas.
- **O-4.** Los intentos consumidos y el motivo del último fallo son visibles por trabajo.

### Memoria a corto y largo plazo (`RNF-M`)

- **M-1.** La frontera entre corto y largo plazo es **la consolidación**. Corto plazo: la
  escena en curso y la anterior, en texto completo. Largo plazo: lo ya consolidado —deltas
  aplicados, resúmenes, fichas y embeddings—.
- **M-2.** El `DeltaDeEscena` es lo único que cruza de corto a largo plazo, y cruza en la
  transición `aceptada` → `consolidada`. Es la misma transición que `INV-05` protege, así
  que la frontera de memoria y la puerta que corta la propagación del error son el mismo
  punto.
- **M-3.** Ningún texto de escena pasa a largo plazo. Al consolidarse, una escena deja en
  largo plazo su delta, su resumen y sus embeddings; su texto se conserva en la base pero
  no vuelve a entrar en el contexto.
- **M-4.** El largo plazo se consulta siempre por recuperación —similitud o clave—, nunca
  entero.

### Presupuesto concurrente (`RNF-P`)

- **P-1.** Los 100.000 tokens son un techo para **todo lo que está en vuelo a la vez**, no
  solo por llamada. **Esto modifica `CLAUDE.md`**, y esa modificación forma parte de esta
  spec.
- **P-2.** Una llamada reserva su presupuesto antes de salir y lo libera al volver, también
  cuando falla. Un fallo no puede dejar presupuesto retenido.
- **P-3.** Si no hay techo disponible, el trabajo **espera en cola**. No se recorta el
  contexto para que quepa: degradar la calidad en silencio para ganar velocidad es
  exactamente el fallo que el sistema intenta evitar.
- **P-4.** "Esperando presupuesto" es un estado visible y distinguible de "en curso".
- **P-5.** Se asume y se deja escrito el efecto secundario: como el reparto por niveles
  suma exactamente 100.000, una llamada del Escritor a tamaño completo agota el techo
  global y es, de hecho, **exclusiva**. Los agentes que reciben menos niveles —Juez,
  Resumidor— sí pueden coincidir entre ellos.

**Qué aporta `P-1` si la ruta principal queda en concurrencia 1.** Que el límite exista y
se registre: impide que los agentes pequeños se acumulen sin control, impide que un
segundo worker futuro duplique el consumo sin darse cuenta, y convierte el consumo en
vuelo en un dato medible en vez de una suposición.

### Observabilidad (`RNF-T`)

- **T-1.** Cada llamada a un agente deja traza consultable con el agente, la escena, los
  niveles de contexto enviados y los tokens realmente consumidos.
- **T-2.** Una llamada que falla también deja traza.

## 3.4 Restricciones de diseño

De `Docs/architecture.md`. Condicionan el código, no solo su organización:

- **D-1.** Una carpeta por feature —caso de uso del pipeline— más `commons/` para lo
  compartido (`A-01`, `A-02`).
- **D-2.** Una feature **nunca** importa de otra feature. `commons/` **nunca** importa de
  una feature. `features/orquestacion/` es la única excepción, porque existe para componer.
- **D-3.** Los `Enum` de los vocabularios controlados viven **solo** en `commons/dominio/`.
- **D-4.** La severidad de las invariantes se implementa una vez, en
  `commons/invariantes/`, y no se resuelve caso por caso en cada verificador.
- **D-5.** Las migraciones se versionan. Un cambio en `Docs/definitions.md` que altere un
  atributo obligatorio necesita su migración en el mismo commit.

---

# 4. Criterios de aceptación

El backend v1 está terminado cuando **todo** esto es cierto:

1. Se puede crear una obra desde un brief, generar su escaleta y llevar **una escena** de
   `planificada` a `consolidada` usando solo la API.
2. Una escena que viola `INV-01` (sin `cambio_de_valor`) **no** llega a `aceptada`.
3. Una escena que viola `INV-07` genera hallazgo, sigue adelante, y el hallazgo aparece al
   consultar la escena.
4. Matar el proceso con una generación a medias y volver a arrancarlo **retoma** el
   trabajo (`O-2`).
5. Una respuesta del Escritor sin delta se rechaza antes de las puertas (`RF-09`).
6. Intentar generar la escena siguiente con la anterior sin consolidar **falla** (`RF-19`).
7. Cada invariante ejecutada tiene su caso de prueba negativo, y ese caso falla si se
   desactiva la comprobación.
8. Las trazas muestran los tokens realmente consumidos por llamada.

## 4.1 Trazabilidad

| Requisito | Invariante | Fila de verificación |
| --- | --- | --- |
| RF-05, RF-06, RF-07, RF-26, P-1 | — | `VER-05`, `VER-06`, `VER-07` |
| RF-09 | — | `VER-20` |
| RF-13, RF-14, RF-15 | `INV-01`…`INV-04`, `INV-07`, `INV-10` | `VER-02`, `VER-11`, `VER-12` |
| RF-16 | — | `VER-25` |
| RF-18, RF-19, RF-20 | `INV-05`, `INV-06` | `VER-10` |
| RF-22 | — | `VER-08` |
| RF-23, RF-25 | — | `VER-18`, `VER-19` |
| O-2, O-3, O-4 | — | `VER-04`, y filas nuevas pendientes |
| M-2, M-3 | `INV-05` | filas nuevas pendientes |
| T-1, T-2 | — | `VER-24` |

`Docs/verification.md` necesita filas nuevas para `O-3`, `M-2`, `M-3`, `P-2` y `P-3`, y
`VER-05` hay que revisarla porque hoy habla del límite **por llamada**.

---

# 5. Fuera de alcance y pendientes

## 5.1 Explícitamente fuera

- El reparto numérico de tokens por agente. Sin medir (`VER-34`).
- El número de reintentos y la curva de espera de `O-3`.
- Subir el techo por encima de 100.000.
- Cambiar el reparto por niveles de `CLAUDE.md`.
- Paralelizar escenas entre sí: el estado se reconstruye acumulando deltas en orden.
- Autenticación, multiusuario y multi-obra.

## 5.2 Números que faltan

Ninguno lleva valor provisional. **Un umbral inventado que queda escrito deja de
distinguirse de uno medido.**

| Qué falta | Bloquea | Cómo se obtiene |
| --- | --- | --- |
| Umbrales de `INV-15` e `INV-16` | `VER-32`, `VER-33` | Medir sobre un corpus y fijar con esa medición. Es la decisión "Umbrales" abierta en `Docs/definitions.md`: se cierran a la vez o ninguna |
| Reparto de tokens por agente | `VER-34` | Instrumentar el consumo durante varias escenas |
| Coste por escena | `VER-36` | Medir una escena completa con `A-03` |
| Suficiencia del reparto por niveles | `VER-37` | Ensamblar el contexto de una escena real y ver si cabe |
| Tope de reintentos y espera de `O-3` | — | Observar la tasa real de fallos transitorios |

## 5.3 Decisiones abiertas que afectan a esta spec

**Cerradas el 2026-09-22**, y por eso ya no aparecen abajo:

- ~~El orden de recorte de los niveles de memoria~~ — fijado en §2.4, con la regla de
  fallar antes que generar por debajo del nivel 3 (`RF-26`).
- ~~Si `Beat` y `ArcoNarrativo` entran en la v1~~ — entran, con su coste reconocido en
  §3.2.2.

Siguen abiertas:

- **`mayor` y `menor`: ¿dejan seguir o van a `en_revision`?** `CLAUDE.md` y
  `Docs/architecture.md` se contradicen (§2.2.3). La v1 asume lo primero. Al cerrarlo hay
  que corregir el documento que quede en falso.
- **La puerta de cierre de capítulo.** La salvaguarda de esa misma decisión —un hallazgo
  `mayor` abierto impide cerrar el capítulo— necesita una puerta que hoy no existe en
  ningún documento.
- **Desempate juez contra regla.** Cuando `INV-03` la marca el Juez y la regla de
  continuidad no ve nada, qué gana.
- **Persistencia del estado.** Si los deltas son la única fuente de verdad o se materializa
  `EstadoDelMundo` en cada `t`. El modelo de datos de §3.2.2 admite las dos; la decisión
  cambia qué se lee en caliente.
- **Granularidad de generación.** Escena completa o beat. Esta versión asume escena
  completa.

---

# 6. Historial

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1 | 2026-09-21 | Primera versión. Absorbe la spec de orquestación, memoria y presupuesto conservando los identificadores `O-`, `M-`, `P-` |
| 2 | 2026-09-21 | Pasa a ser **solo** la spec del backend: fuera el registro multi-spec. Se añade §2.2 con el proceso tomado de `Docs/`, y se documenta en §2.2.3 la contradicción entre `CLAUDE.md` y `Docs/architecture.md` sobre `mayor` y `menor` |
| 3 | 2026-09-22 | Se cierran dos bloqueantes. **§2.4 fija el orden de recorte** por qué se pierde si falta, y `RF-26` añade que por debajo del nivel 3 se falla en vez de generar. **`Beat` y `ArcoNarrativo` entran en la v1** con su coste reconocido: el Escaletador pasa a tener que rellenarlos. `D4-6` ya lo había cerrado `SPEC-03` al poner `cambios_de_estado_vital` en el delta |
