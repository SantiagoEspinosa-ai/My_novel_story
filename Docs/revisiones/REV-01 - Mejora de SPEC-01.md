---
id: REV-01
titulo: Revisión de SPEC-01 para llevarla a aprobada
tipo: revision_de_spec
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
spec_evaluada: "specs/SPEC - Backend.md (SPEC-01, en_revision, version 2)"
---

# REV-01 — Revisión de SPEC-01

## Esto no es un plan de implementación

**Es una revisión del documento, no un plan sobre el código.** `AGENTS.md` define
`specs/plans/PLAN-NN.md` como el plan de implementación que se escribe **después** de
aprobar una spec y que dice qué ficheros se tocan y en qué orden. Este documento es otra
cosa: evalúa `SPEC-01` mientras sigue en `en_revision` y propone cómo llevarla hasta
`aprobada`. No toca código, no toca ficheros de `backend/`, y no sustituye al plan de
implementación, que seguirá haciendo falta cuando `SPEC-01` se apruebe.

**Por eso vive en `Docs/revisiones/` y se llama `REV-01`.** La primera versión estaba en
`specs/plans/` como `PLAN-01`, y ese número le corresponde al plan de implementación de
`SPEC-01`. Con dos documentos distintos llamados `PLAN-01` la referencia cruzada deja de
significar nada. Las revisiones tienen su propia serie, `REV-NN`, y su propia carpeta; una
revisión se numera por la spec que revisa, así que `REV-01` revisa `SPEC-01`.

**Lo que se evaluó.** `SPEC-01` entera, contra el estado **actual** de
`Docs/definitions.md` (después de aplicar `SPEC-02`), `Docs/architecture.md`,
`Docs/verification.md`, `CLAUDE.md` y `AGENTS.md`. No contra ninguna spec ni contra
ninguna versión anterior de esos documentos.

---

# PARTE 1 — Qué hay que mejorar

Severidad: **bloqueante** impide aprobar la spec; **mayor** permite aprobarla pero deja
deuda que hay que registrar; **menor** es cosmético.

## Eje 1 — Desfase con el dominio actual

`SPEC-01 v2` se escribió el 2026-09-21, antes de aplicar `SPEC-02`. Estos son los puntos
donde cita el dominio con su forma vieja.

| # | Sev | Qué dice SPEC-01 | Qué dice `Docs/definitions.md` hoy | Propuesta |
| --- | --- | --- | --- | --- |
| **D1-1** | 🟠 mayor | §1.3: *"**Hallazgo** \| Defecto detectado, con su verificador, su escena y su severidad"* | `Hallazgo`: **invariante** (`INV-xx`), **verificador**, **escena**, severidad, estado → `estado_de_hallazgo`, descripcion | El glosario de la propia spec describe la clase sin el campo que `RF-15` exige. La spec se contradice a sí misma: corregir §1.3 con los seis atributos actuales |
| **D1-2** | 🟠 mayor | §2.2.1, diagrama Mermaid: `Planificada`, `Generada`, `EnVerificacion`, `EnRevision`, `Rechazada`, `Aceptada`, `Consolidada` | `estado_de_escena`: `planificada, generada, en_verificacion, rechazada, en_revision, aceptada, consolidada`. Y: *"los literales se copian de esta tabla, nunca del diagrama"* | Es el mismo defecto que se corrigió en `Docs/domain-knowledge.md` y que sigue vivo aquí. La tabla de transiciones que hay justo debajo del diagrama **sí** usa los literales correctos, así que el documento se contradice a dos párrafos de distancia |
| **D1-3** | 🟠 mayor | §1.2, "No entra": *"`auditoria/` \| `INV-06`, `INV-09`, `INV-11`, `INV-12`, `INV-13` e `INV-16` necesitan la obra entera"* | El Auditor de obra ejecuta hoy, según `Docs/architecture.md`: obra `INV-06, INV-09, INV-11, INV-12, INV-13, INV-14, INV-16`; capítulo `INV-08, INV-15` | La lista de exclusión está incompleta: faltan `INV-14`, `INV-08` e `INV-15`. Como define el **alcance**, dejarla mal significa no saber qué queda fuera |
| **D1-4** | 🟡 menor | §3.2.2: *"`escena` \| Atributos obligatorios de `Escena` **más su** `estado`"* | `estado` ya **es** un atributo obligatorio de `Escena` | El "más su" sobra y sugiere que `estado` es un añadido del backend, no del dominio |
| **D1-5** | 🟡 menor | §1.3: *"`INV-xx` \| Invariante verificable de `Docs/definitions.md`"*, descrito como identificador | `Invariante` es ahora una **clase** del plano Calidad con **id**, **enunciado**, **nivel**, **severidad**, **tipo** | Distinguir la clase del identificador. Ver también `D3-4`: falta su tabla en el modelo de datos |
| **D1-6** | 🟡 menor | `RF-23`, §2.2.2, criterio 3 de §4: *"hallazgos abiertos"* en prosa | Existe `estado_de_hallazgo` con el valor `abierto` | Citar el literal (`estado_de_hallazgo = abierto`) en vez de decirlo en prosa, como ya hace `INV-02` con `estado_vital = vivo` |

**Identificadores desacentuados: sin hallazgos.** Comprobé uno a uno los que aparecen en
`SPEC-01` —`objetivo_dramatico` (`RF-02`), `en_verificacion` y `en_revision` (tabla de
§2.2.1), `Rubrica` y `GuiaDeEstilo` (§3.2.3), `hecho_canonico`, `registro_de_conocimiento`,
`ancla_de_estilo` (§3.2.2)— y todos están en su forma ASCII. La pasada de `SPEC-02` alcanzó
el cuerpo del documento. **No alcanzó el diagrama Mermaid**, que es `D1-2` y es un problema
distinto: allí no hay tildes, hay `PascalCase`.

## Eje 2 — Requisitos no verificables

Ocho de los veinticinco requisitos funcionales llevan `—` en su columna *Verifica*:
`RF-01`, `RF-03`, `RF-04`, `RF-08`, `RF-10`, `RF-11`, `RF-12`, `RF-21`. No todos son igual
de graves: a unos solo les falta la fila `VER`, a otros les falta el criterio.

| # | Sev | Requisito y cita | Qué le falta |
| --- | --- | --- | --- |
| **D2-1** | 🔴 bloqueante | `RF-06`: *"Si no cabe, se recorta **por el nivel de menor prioridad**"* | **La spec nunca dice cuál es el orden de prioridad de los seis niveles.** `CLAUDE.md` tampoco. El único orden parcial escrito está en el criterio de salida de `VER-06` (*"el nivel inmutable nunca se toca antes que los resúmenes"*), que son dos de seis. Sin el orden completo, `RF-06` no se puede implementar sin inventarlo ni verificar sin suponerlo |
| **D2-2** | 🟠 mayor | `RF-08`: *"Cada agente recibe únicamente los niveles que le corresponden según `Docs/architecture.md`"* | La tabla a la que apunta no es especificable: sus celdas dicen *"según profundidad"*, *"guía de estilo y anclas"*, *"solo lo que cita el hallazgo"*. No son predicados comprobables, son descripciones. `RF-08` hereda esa vaguedad |
| **D2-3** | 🟠 mayor | `T-1`: *"Cada llamada a un agente deja traza **consultable**"* | Consultable dónde. *"Dónde viven las trazas de `VER-24` y quién las mira"* sigue abierta en `Docs/verification.md`. Hasta que se cierre, `T-1` no tiene criterio |
| **D2-4** | 🟠 mayor | `O-3`: *"se reintentan con espera creciente y un **tope acotado** de intentos"* | El número está explícitamente fuera de alcance (§5.2). La spec lo reconoce, pero eso convierte `O-3` en no verificable hasta que exista. Hay que decidir si se aprueba como deuda declarada o se le pone criterio cualitativo (*"el tope existe, es configurable y se registra"*), que sí es comprobable sin fijar el número |
| **D2-5** | 🟠 mayor | `P-4`: *"'Esperando presupuesto' es un estado **visible** y distinguible de 'en curso'"* | Visible dónde. El frontend está fuera de alcance (§1.2). Dentro de esta spec lo comprobable es que el estado exista en el modelo y se devuelva por la API, no que se vea |
| **D2-6** | 🟠 mayor | `RF-12`: *"Las comprobaciones deterministas las ejecuta **código**, no un juez"* | Es una restricción de diseño con forma de requisito funcional. Es verificable —con análisis estático: ninguna invariante de `tipo = regla` pasa por el cliente del modelo— pero no tiene criterio escrito ni fila `VER`. Su sitio natural es §3.4 |
| **D2-7** | 🟠 mayor | `RF-21`: *"se actualizan las `Ficha` de **las entidades afectadas**"* | "Afectadas" no está definido. Ver también `D6-2`: es además ambiguo |
| **D2-8** | 🟡 menor | `RF-03`, `RF-04`, `RF-10`, `RF-11` | Son perfectamente comprobables; solo les falta su fila en `Docs/verification.md`. `RF-11` es el que más importa de los cuatro, porque es el que sostiene la reproducibilidad |
| **D2-9** | 🟡 menor | `RF-01`: *"un `Brief` con premisa, tono, guía de estilo y prohibiciones"* | Mezcla atributos de dos clases: `premisa`, `tono` y `prohibiciones` son de `Brief`; `guia_de_estilo` es de `Obra`. Falta decir cuáles son obligatorios en la petición |

## Eje 3 — Trazabilidad

| # | Sev | Hallazgo, con cita | Propuesta |
| --- | --- | --- | --- |
| **D3-1** | 🟠 mayor | **La matriz de §4.1 y las tablas de §3.1 se contradicen.** §4.1 omite `RF-01`, `RF-02`, `RF-03`, `RF-04`, `RF-08`, `RF-10`, `RF-11`, `RF-12`, `RF-17`, `RF-21`, `RF-24`, `O-1`, `M-1`, `M-4`, `P-2`…`P-5` y `D-1`…`D-5`. Pero `RF-02` sí declara `INV-01` en su propia fila, `RF-17` declara `VER-29` y `RF-24` declara `VER-04` | Hay dos fuentes de trazabilidad que no coinciden. Una sobra: la matriz debe generarse desde las tablas, o desaparecer |
| **D3-2** | 🟠 mayor | **La recuperación no tiene ningún requisito.** `Docs/architecture.md` da al Ensamblador *"recuperar por similitud; seleccionar fichas y setups pendientes"*, y `RF-05`…`RF-08` solo hablan de presupuesto y recorte | La mitad del componente más crítico del sistema no está especificada: ni cuántos vecinos, ni con qué criterio, ni qué pasa si la recuperación no devuelve nada |
| **D3-3** | 🟠 mayor | **Nada cubre `VER-27`** (*"La salida de cada agente valida contra su esquema tipado, o se rechaza"*). `RF-09` lo exige solo para el Escritor; el Escaletador, el Juez y el Resumidor no tienen requisito equivalente | Falta un requisito transversal de validación de salida. Hoy la garantía está en `verification.md` pero no en la spec, y `AGENTS.md` dice que `verification.md` no introduce requisitos nuevos |
| **D3-4** | 🟠 mayor | **El rechazo de transiciones ilegales no es un requisito.** §3.2.1 dice *"`409` cuando la transición pedida no es legal"*, pero ningún `RF` lo recoge, y `Docs/architecture.md` da al Orquestador *"decidir la siguiente transición legal"* | Es la garantía central de la máquina de estados y vive solo como nota de una tabla de endpoints |
| **D3-5** | 🟠 mayor | **`RF-23` y `RF-25` trazan a pruebas de frontend.** `VER-18` y `VER-19` viven en `frontend/.../tests/` y hablan de *"se muestra"*, mientras `RF-25` dice *"se devuelve"* | Un requisito de backend no puede cerrarse con una prueba de frontend. Hay que partir esas dos filas `VER` en dos: la de la API y la de la interfaz |
| **D3-6** | 🟡 menor | **`A-06` está cubierta a medias.** `RF-16` recoge *"el Juez no recibe el prompt"*, pero no la otra mitad: *"modelo distinto si se puede; sesión limpia como mínimo"* | O se añade a `RF-16`, o se dice que la elección de modelo queda fuera |

**Partes de `Docs/architecture.md` sin requisito, comprobadas y descartadas:** `A-09` (FSD),
las vistas del frontend, el Revisor y el Auditor de obra están **legítimamente** sin
requisito porque §1.2 los excluye de forma explícita. `A-07` y `A-08` son decisiones sobre
documentación y no producen código. Recorrí las nueve decisiones `A-01`…`A-09` y los diez
agentes: los únicos huecos reales son `D3-2`, `D3-3`, `D3-4` y `D3-6`.

## Eje 4 — Huecos

### Lo que preguntaste explícitamente

**¿Los agentes tienen requisitos formales o se quedan fuera por ser adaptadores?**
Se quedan fuera, pero **sin decirlo**. Los cuatro agentes aparecen en §3.2.3 como una tabla
de *interfaces externas*, no como requisitos. Solo el Escritor (`RF-09`) y el Juez
(`RF-16`) tienen requisito propio; el Escaletador y el Resumidor no. Tratarlos como
adaptadores es defendible —son la frontera con un servicio externo—, pero entonces la spec
debe decir esa decisión y sus consecuencias, y hoy no lo dice. Es `D4-1`.

**¿El presupuesto de 100.000 está como requisito verificable o solo como nota?**
Como las dos cosas, y ahí está el problema. Aparece como **nota** en §2.4 (tabla de
restricciones copiada de `CLAUDE.md`) y como **requisito** en `RF-05` y `P-1`. Pero las dos
formas dicen cosas distintas: §2.4 dice *"100.000 tokens, salida incluida"* (por llamada) y
`P-1` dice *"un techo para todo lo que está en vuelo a la vez"* (concurrente). La propia
spec lo reconoce en §4.1: *"`VER-05` hay que revisarla porque hoy habla del límite por
llamada"*. Es `D4-2`. Y el reparto por niveles (15.000 / 10.000 / 25.000 / 20.000 / 10.000
/ 20.000) está **solo** como nota: ningún requisito obliga a respetarlo, solo a no pasarse
del total. Es `D4-3`.

### Tabla de huecos

| # | Sev | Qué falta | Por qué importa |
| --- | --- | --- | --- |
| **D4-4** | 🔴 bloqueante | **El modelo de datos de §3.2.2 no tiene tablas para `Beat`, `ArcoNarrativo`, `POV` ni `MomentoNarrativo`** | `RF-13` incluye `INV-07` (*"toda escena realiza al menos un beat que sirve a un arco"*) entre las invariantes que se ejecutan, e `INV-04` es sobre el POV. Además `pov` y `momento_narrativo` son atributos **obligatorios** de `Escena`. No se puede comprobar `INV-07` sin tabla de beats ni de arcos |
| **D4-5** | 🔴 bloqueante | **El orden de prioridad de los niveles de memoria** (ver `D2-1`) | Sin él `RF-06` no es implementable |
| **D4-6** | 🔴 bloqueante | **`DeltaDeEscena` no puede expresar `desaparecido`.** Sus campos son `muertes, movimientos, revelaciones, setups_pagados, cambios_de_posesion, deterioros` | `estado_vital` tiene tres valores y el delta solo sabe expresar el paso a `muerto`. Una escena que deja a un personaje desaparecido no puede reflejarlo en el estado, e **`INV-02` lo leerá como vivo**. `SPEC-02` añadió `desaparecido` precisamente porque en terror la ambigüedad sobre si alguien vive es material narrativo: si el delta no sabe expresarlo, hemos creado un valor que el sistema **no puede alcanzar**, y una invariante `bloqueante` que da por buenas presencias que el texto no sostiene. Reclasificado de `mayor` a `bloqueante` el 2026-09-22 |
| **D4-7** | 🟠 mayor | **No hay requisito de idempotencia de los trabajos.** `O-2` dice que un reinicio *retoma* el trabajo pendiente | Si el worker muere después de llamar al modelo y antes de registrar el resultado, al reanudar vuelve a llamar: se paga dos veces y, como el modelo no es determinista, sale otra escena. La cola da *at-least-once* y la spec razona como si fuera *exactly-once* |
| **D4-8** | 🟠 mayor | **El ciclo `rechazada` → `generada` → `en_verificacion` → `rechazada` no tiene tope** | `O-3` acota los reintentos **dentro** de un trabajo; nada acota las vueltas **entre** trabajos. Un Escritor que insiste en devolver escenas sin `cambio_de_valor` gira indefinidamente |
| **D4-9** | 🔴 bloqueante | **La puerta de cierre de capítulo no existe en ningún documento.** `estado_de_escena` no tiene estados de capítulo, `Capitulo` no tiene atributo de estado, y `SPEC-01` no tiene ningún requisito de cierre de capítulo | **Hallazgo nuevo, descubierto al cerrar `C-1` el 2026-09-22.** La salvaguarda de esa decisión —*"un hallazgo `mayor` abierto impide cerrar el capítulo"*— necesita una puerta que hoy no está definida. Sin ella la decisión queda a medias: se quita el bloqueo por escena y no se pone el de capítulo, así que un `mayor` deja de tener consecuencia alguna |
| **D4-1** | 🟠 mayor | **No se declara que los agentes son adaptadores** | Ver arriba |
| **D4-2** | 🟠 mayor | **Dos definiciones vivas del límite de 100.000** | Ver arriba. Se resuelve al cerrar la decisión de `P-1`, no antes |
| **D4-3** | 🟡 menor | **El reparto por niveles no es requisito** | Se puede cumplir el total y repartirlo de cualquier forma |

## Eje 5 — Decisiones pendientes que la bloquean

§5.3 lista cuatro. Están bien, pero la lista **está incompleta**: hay tres decisiones
abiertas en otros documentos que afectan a requisitos concretos de `SPEC-01` y no aparecen.

| # | Sev | Decisión | Dónde está abierta | Qué requisito de SPEC-01 bloquea |
| --- | --- | --- | --- | --- |
| **D5-1** | ✅ **cerrada** | *"`mayor` y `menor`: ¿dejan seguir o van a `en_revision`?"* | Era §2.2.3 de la propia spec, más `CLAUDE.md` y `Docs/architecture.md` | **Decidida el 2026-09-22. Ver "Decisiones cerradas" más abajo.** Queda pendiente de aplicar a `SPEC-01` en el paso 2 |
| **D5-2** | 🟠 mayor | *"Qué valida un humano y cuándo"* | `Docs/definitions.md` y `Docs/architecture.md` | `RF-17` asume que **toda** aceptación la dispara un cliente. Si se decide que una escena sin hallazgos puede auto-aceptarse, `RF-17` cambia. No está en §5.3 |
| **D5-3** | 🟠 mayor | *"Corpus de fixtures"* | `Docs/definitions.md` | El criterio 7 de §4 exige un caso negativo por invariante ejecutada; sin corpus no se puede construir. No está en §5.3 |
| **D5-4** | 🟠 mayor | *"Dónde viven las trazas"* | `Docs/verification.md` | `T-1` (ver `D2-3`). No está en §5.3 |
| **D5-5** | 🟡 menor | *"Persistencia del estado"* y *"Granularidad de generación"* | `Docs/definitions.md`, `Docs/architecture.md` y §5.3 | Sí están listadas y la spec dice qué asume. Correcto: se anota como suposición, no se decide |

## Eje 6 — Ambigüedad

| # | Sev | Frase citada | Lectura A | Lectura B |
| --- | --- | --- | --- | --- |
| **D6-1** | ✅ **cerrada** | `RF-07`: *"Solo **la escena anterior** entra en texto completo"* | La anterior en **discurso** (`t_discurso`) ← **elegida** | La anterior en **fábula** (`t_fabula`) |
| **D6-2** | 🟠 mayor | `RF-21`: *"se actualizan las `Ficha` de las **entidades afectadas**"* | Las que aparecen en el `DeltaDeEscena` | Las de `personajes_presentes[]` de la escena |
| **D6-3** | 🟠 mayor | `RF-19`: *"Ninguna **escena posterior** puede generarse mientras la anterior no esté `consolidada`"* | Solo la inmediatamente siguiente en la escaleta | Cualquier escena con orden mayor, en cualquier capítulo o línea argumental |
| **D6-4** | 🟠 mayor | `M-1`: *"Corto plazo: la escena en curso y la anterior, en texto completo"* frente al nivel Local de §2.4: *"Escena anterior completa **y resumen de las tres previas**"* | El resumen de las tres previas es corto plazo, porque está en el nivel Local | Es largo plazo, porque `M-1` define largo plazo como *"lo ya consolidado"* y esas tres lo están |
| **D6-5** | 🟡 menor | `RF-25`: *"se devuelve como **ausente** y distinguible de cero"* | El campo se omite del JSON | El campo está presente con valor `null` |

`D6-1` era bloqueante y no mayor porque el dominio separa `t_fabula` y `t_discurso` **a
propósito** —`Docs/definitions.md` dice que esa separación *"es lo que habilita analepsis,
relatos enmarcados y narradores no fiables"*— así que las dos lecturas no coinciden en
cuanto haya una analepsis, que es material típico del género. Ya está cerrada: ver
"Decisiones cerradas".

## Mejoras opinables — no son defectos

Separadas a propósito: ninguna de estas es una contradicción ni un hueco, son cosas que yo
haría distinto.

- **§2.4 repite el reparto por niveles de `CLAUDE.md`.** La spec declara precedencia, así
  que es correcto. Pero es la misma duplicación que en otros sitios ha divergido. Yo dejaría
  solo el total y un puntero.
- **Los criterios de aceptación de §4 son ocho para cuarenta requisitos.** No es un
  defecto —son criterios de versión, no de requisito—, pero la relación entre unos y otros
  no está escrita.
- **§2.2.2 dibuja una secuencia que §1.2 excluye en parte.** El diagrama incluye al Juez,
  que sí entra, pero el lector puede leerlo como el flujo definitivo. Añadiría una nota.

---

# Decisiones cerradas

Tomadas el 2026-09-22. **Aún no están aplicadas a `SPEC-01`**: eso es el paso 2.

## C-1 · `D5-1` — Un hallazgo `mayor` o `menor` no manda la escena a `en_revision`

**Decisión.** La escena **avanza** y el hallazgo **queda abierto**. La transición
`en_verificacion → en_revision` disparada por el Juez desaparece.

**Motivo.** Si `mayor` bloquea, la escala de tres niveles tiene dos reales —`bloqueante` y
`mayor` se comportan igual— y la distinción deja de servir para nada. Una escala cuyos
valores no producen comportamientos distintos es una etiqueta, no un control.

**Salvaguarda.** Un hallazgo `mayor` abierto **impide cerrar el capítulo**, que es la
puerta con firma humana. El control no se pierde: se mueve de la escena al capítulo, que
es donde una persona puede juzgar si el conjunto se sostiene. Así no se para el flujo
escena a escena y sigue habiendo un punto donde alguien responde.

**Qué toca, y va todo junto o queda incoherente:**

| Documento | Qué cambia |
| --- | --- |
| `SPEC-01` `RF-14` | Redacción: `mayor` y `menor` no bloquean, y el hallazgo abierto bloquea el cierre de capítulo |
| `SPEC-01` §2.2.1, tabla | Se elimina la fila `en_verificacion → en_revision` |
| `SPEC-01` §2.2.1, diagrama | Se elimina la arista `EnVerificacion --> EnRevision` (y se corrigen los literales, `D1-2`) |
| `SPEC-01` §2.2.3 | Deja de ser una contradicción abierta y pasa a ser la decisión y su salvaguarda |
| `CLAUDE.md` § Reglas de trabajo | Queda confirmado, no cambia |
| `Docs/architecture.md` | Se elimina la misma fila de su tabla de transiciones |
| `Docs/domain-knowledge.md` | Se elimina la arista `en_verificacion --> en_revision: juez marca` |
| `Docs/verification.md` `VER-28` | Su enunciado razona sobre la máquina de estados y hay que revisarlo |

**Consecuencia que hay que escribir en alguna parte:** la puerta de cierre de capítulo
**no existe hoy en ningún documento**. `estado_de_escena` no tiene estados de capítulo y
`SPEC-01` no tiene requisito de cierre de capítulo. La salvaguarda de esta decisión
necesita un sitio donde vivir, y ese sitio no está creado. Se anota como hallazgo nuevo
`D4-9` más abajo.

## C-2 · `D6-1` — "La escena anterior" es la anterior en discurso

**Decisión.** `RF-07` se refiere a la escena anterior en **`t_discurso`**, no en
`t_fabula`. Se escribe con el literal, no en prosa.

**Motivo.** Es lo que ve el lector y es el contexto que el modelo necesita para continuar
el texto: voz, ritmo y dónde quedó la última frase. La anterior en fábula puede estar a
veinte escenas de distancia en la lectura y no aporta continuidad de superficie.

**Qué toca:** `RF-07` y el nivel Local de §2.4. También la definición de "las tres
previas" del mismo nivel, que hereda la misma ambigüedad y que hay que fijar igual.

---

# Propuestas pendientes de tu respuesta

## P-A · `D2-1` / `D4-5` — Orden de recorte de los niveles de memoria

**Aviso antes de la propuesta: son cinco niveles recortables, no seis.**

Propongo que **`Salida` no entre en el orden de recorte**. Recortarla no reduce el
contexto que ve el modelo: reduce el sitio que tiene para escribir. El fallo que produce
es distinto —un borrador truncado, que además incumple `RF-09` porque llega sin delta— y
consume la llamada entera igual. Los otros cinco degradan la calidad; este rompe la
salida. Si prefieres que entre, dilo y la coloco.

Orden propuesto, del primero que se recorta al último:

| # | Nivel | Presupuesto | Argumento para esa posición |
| --- | --- | --- | --- |
| 1.º | **Resúmenes** | 10.000 | Es el nivel **más redundante**: las condensaciones de capítulo y parte ya están representadas, más comprimidas, en `Estado actual` (los hechos vigentes) y en `Recuperado` (las fichas). Además su valor decrece con la distancia, así que se puede recortar **dentro** del nivel soltando lo más lejano primero, en vez de todo o nada |
| 2.º | **Recuperado** | 20.000 | Es el único nivel que **se puede volver a pedir**: es el resultado de una consulta, así que recortarlo es bajar la `k`, no perder información. Y el buscador ya lo devuelve ordenado por relevancia, así que se recorta por la cola, que es exactamente lo menos relevante |
| 3.º | **Local** | 25.000 | Se parte en dos: **primero el resumen de las tres previas** (redundante con `Resúmenes`) y **después la escena anterior completa**, que es lo último de este nivel. La escena anterior es lo que da continuidad de superficie y es justo lo que `C-2` acaba de fijar como `t_discurso` |
| 4.º | **Estado actual** | 10.000 | Recortarlo no hace que el modelo escriba peor: hace que escriba cosas que **contradicen el canon**. Y esas contradicciones las caza una puerta *después*, habiendo pagado ya la llamada. Sostiene `INV-02` e `INV-06` |
| 5.º | **Inmutable** | 15.000 | Último, como fijaste. Es lo único **irrecuperable**: premisa, guía de estilo, reglas del mundo y anclas son el contrato de la obra. Perderlo no degrada una escena, cambia el libro. Y las anclas son la defensa contra la deriva de voz (`INV-15`), el fallo que solo se detecta tarde |
| — | **Salida** | 20.000 | **No se recorta** (ver arriba) |

**El principio detrás del orden**, por si prefieres discutir el principio y no las
posiciones: *se recorta primero lo que se puede reconstruir o ya está representado en otro
nivel, y al final lo que es irrecuperable o sostiene una invariante bloqueante.*

**Dos matices que salen de proponerlo:**

1. **`Recuperado` contiene algo que no debería recortarse con el resto.** Sus tres
   contenidos son fichas, setups pendientes y *registro de conocimiento aplicable*. El
   tercero sostiene `INV-03`, que es **bloqueante**. Recortarlo en silencio hace que el
   Escritor no sepa quién sabe qué y que la puerta lo cace después. Propongo separarlo:
   el registro de conocimiento del `t` de la escena se recorta en la posición 4.ª, con
   `Estado actual`, no en la 2.ª.
2. **Qué pasa si después de recortar todo lo recortable sigue sin caber.** No se sigue
   cortando hacia `Inmutable`: el ensamblador **falla y lo dice**. `CLAUDE.md` ya da el
   diagnóstico —*"el fallo está en los resúmenes o en la recuperación, no en el
   presupuesto"*—, y convertirlo en un fallo ruidoso es lo que impide que el sistema
   degrade en silencio.

## P-B · `D4-4` — Qué cuesta cada salida

**Corrección al enunciado, antes de los costes.** Las cuatro clases no cuestan lo mismo
porque no son la misma cosa:

- `POV` y `MomentoNarrativo` son **objetos de valor 1:1 con `Escena`** (`narrada_desde` y
  `situada_en` son ambas `1:1` en la tabla de relaciones). No necesitan tabla propia: son
  columnas embebidas en `escena`.
- `Beat` y `ArcoNarrativo` son **entidades con relaciones N:M** (`realiza` es `N:M`,
  `sirve_a` es `N:M`). Esas sí necesitan tabla, y además su tabla de unión.

### Salida A — Añadir lo que falta

| Qué hay que crear | Cantidad |
| --- | --- |
| Columnas nuevas en `escena` para `POV` (`personaje`, `persona`, `tiempo_verbal`, `distancia`, `fiabilidad`) y `MomentoNarrativo` (`t_fabula`, `t_discurso`, `duracion_ficcional`) | 8 columnas, 0 tablas |
| Tablas `beat` y `arco_narrativo` | 2 tablas |
| Tablas de unión `escena_realiza_beat` y `beat_sirve_a_arco` | 2 tablas |
| Cambio de contrato del **Escaletador** | `Docs/architecture.md` ya le da *"asignar beats a arcos"*, así que su salida `Escaleta` tiene que incluirlos. Toca §3.2.3 y `RF-02` |
| Decisión nueva | Si el Escritor puede **añadir o modificar** beats, o solo consumir los que vienen de la escaleta |

### Salida B — Sacar `INV-07` de la v1

| Qué se ahorra | Qué cuesta |
| --- | --- |
| Las 2 tablas de entidad y las 2 de unión | `RF-13` pasa de siete invariantes a seis |
| — | **El criterio 3 de §4 se queda sin ejemplo.** Hoy dice: *"Una escena que viola `INV-07` genera hallazgo, sigue adelante, y el hallazgo aparece al consultar la escena"* |

**Lo que hace cara la salida B, y es el dato que más pesa:** `INV-07` es **la única
invariante de nivel escena que es `mayor` y de tipo `regla`**. Las de escena son `INV-01`,
`INV-02`, `INV-04` y `INV-05` (`bloqueante`, regla), `INV-03` (`bloqueante`, juez),
`INV-07` (`mayor`, regla) e `INV-10` (`mayor`, juez). Si se saca `INV-07`, el único
`mayor` que queda en la escena es `INV-10`, que lo decide un juez LLM.

Eso choca de frente con la decisión `C-1` que acabas de tomar: `C-1` dice que un `mayor`
no bloquea, y el criterio 3 es **cómo se demuestra**. Sin `INV-07`, la v1 no puede
demostrar con una regla determinista que un hallazgo `mayor` deja pasar la escena: solo
podría demostrarlo con un juez, que es no determinista y cuya fiabilidad `VER-26` reconoce
sin medir.

**Y no cierra el hueco entero**, como ya señalaste: `pov` y `momento_narrativo` son
atributos obligatorios de `Escena`, e `INV-04` (*"el POV no cambia dentro de una escena"*)
es **bloqueante**. Las 8 columnas hay que crearlas en las dos salidas.

### Recomendación

**Salida A.** Lo que de verdad se ahorra la salida B son dos tablas y sus dos uniones, y
lo que cuesta es dejar sin demostración determinista la decisión que acabas de tomar. La
diferencia de esfuerzo es pequeña; la diferencia de lo que el sistema puede probar de sí
mismo, no.

---

# PARTE 2 — El ciclo de mejora

Dos ciclos distintos, con disparadores, participantes y condición de salida propios. El
primero termina; el segundo no termina nunca, y por eso necesita métrica más que
condición de salida.

## Ciclo corto — sobre el documento, hasta aprobar

### Quién hace qué

| Rol | Quién | Qué hace | Qué no hace |
| --- | --- | --- | --- |
| **Crítico** | Un agente, o una persona distinta de quien redactó | Recorre los seis ejes, produce hallazgos con cita y severidad, y **lleva el recuento de bloqueantes** | No corrige, no negocia la severidad |
| **Redactor** | Quien mantiene la spec | Corrige, o argumenta por qué un hallazgo no lo es | No cambia el `estado` del frontmatter, **no cuenta los bloqueantes ni reclasifica severidades** |
| **Decisor** | Tú | Resuelve las decisiones abiertas, arbitra si crítico y redactor no se ponen de acuerdo sobre una severidad, y aprueba | No redacta |

Que el crítico no corrija es deliberado: quien redacta defiende lo que escribió, y quien
critica lo suyo encuentra menos.

**El recuento de bloqueantes lo lleva el crítico, y esto no es un detalle de reparto.** La
condición de salida es "cero bloqueantes"; si quien corrige es también quien decide qué
cuenta como bloqueante, la condición se cumple sola bajando severidades. El redactor puede
**argumentar** que algo no es bloqueante, pero quien lo reclasifica es el crítico, y si no
hay acuerdo lo arbitra el decisor. Una condición de salida que el interesado puede mover
no es una condición.

### Qué se comprueba en cada vuelta

Primero lo mecánico, que es barato y no necesita criterio:

1. Todo literal de dominio citado existe hoy en `Docs/definitions.md`, con esa forma exacta.
2. Todo `RF`/`RNF` aparece en la matriz de trazabilidad, y al revés.
3. Todo requisito tiene criterio de aceptación comprobable, o está declarado como deuda.
4. Toda decisión abierta que afecta a un requisito está en §5.3.
5. Ningún número aparece sin estar medido.

Después los seis ejes de la Parte 1, en ese orden: **desfase, huecos, verificabilidad,
trazabilidad, decisiones, ambigüedad**. El orden importa: un desfase invalida requisitos
enteros, así que buscar ambigüedades antes de corregir el desfase es pulir frases que van a
desaparecer.

### Condición de salida

Sin esto el ciclo no termina o termina por cansancio, que es peor porque la última vuelta
es la que menos atención recibe. Propongo **dos condiciones y un tope**:

> **La spec se aprueba cuando (a) hay cero hallazgos bloqueantes y (b) una vuelta completa
> no produce ningún hallazgo nuevo de eje 1 (desfase) ni de eje 4 (huecos).**
>
> **Tope: tres vueltas.** Si en la tercera siguen apareciendo bloqueantes, el ciclo se
> detiene y no se sigue puliendo: se parte la spec en dos.

Por qué así:

- **Cero bloqueantes** es la única condición no negociable: un bloqueante es, por
  definición, algo que obliga a adivinar al implementar. Los `mayor` **no** bloquean, pero
  al aprobar se copian a una sección de deuda con dueño y fecha; si no se escriben, se
  olvidan.
- **"Ningún hallazgo nuevo de eje 1 o 4"** y no "ningún hallazgo nuevo" a secas, porque
  siempre se puede encontrar una ambigüedad más. Desfase y huecos son los dos ejes donde
  encontrar algo nuevo significa que la revisión anterior no miró bien; los otros cuatro
  tienen rendimiento decreciente.
- **El tope de tres** convierte el fracaso en información. Si a la tercera vuelta la spec
  sigue produciendo bloqueantes, el problema no es la redacción: es que el alcance es
  demasiado grande para una sola spec. Seguir dando vueltas lo esconde.

### Cómo se sabe si el ciclo corto funciona

| Métrica | Cómo se lee |
| --- | --- |
| **Bloqueantes por vuelta** | Debe ser estrictamente decreciente. Si la vuelta 2 encuentra más que la 1, el alcance es el problema, no el texto |
| **Abiertos frente a cerrados por vuelta** | Si cada vuelta abre más hallazgos de los que cierra, el documento está creciendo más rápido de lo que se estabiliza: para y parte |
| **Reincidencia** | Cuántos hallazgos reaparecen en una vuelta posterior. Alta reincidencia significa que la corrección fue cosmética y no tocó la causa |
| **Vueltas hasta aprobar** | Se registra para calibrar el tope. Hoy no hay dato: esta es la primera |

La tercera es la que más dice. Un hallazgo que reaparece es exactamente el patrón de
"corregir las copias en vez de eliminar la duplicación".

## Ciclo largo — sobre el sistema, después de aprobar

Empieza cuando hay código y no termina. No tiene condición de salida: tiene disparadores.

### Disparadores y qué se hace en cada caso

| Disparador | Qué se hace | Por qué |
| --- | --- | --- |
| **Un requisito resulta inimplementable** | Se **para el código**, se corrige la spec y se vuelve a aprobar. Si además cambia el alcance, spec nueva | Es la regla de `AGENTS.md`: el código nunca avanza por delante de la spec. Corregir la spec después convierte el documento en descripción, no en gobierno |
| **Un umbral se mide y no era el supuesto** | **No se toca `SPEC-01`.** Se cierra la decisión abierta correspondiente y se actualiza `Docs/verification.md` | La spec nunca llevó el número: §5.2 lo declara pendiente. Esta es la recompensa de no haber inventado ninguno, y conviene notarla |
| **Una invariante falla de una forma que la spec no previó** | Tres casos distintos: **(a)** la invariante está mal definida → spec de dominio, como `SPEC-02`; **(b)** la spec no cubría ese caso → se corrige `SPEC-01` y se reaprueba; **(c)** el código está mal → no se toca ninguna spec, se arregla el código y se añade el caso negativo | Confundir (a) con (c) es lo que lleva a relajar una invariante para desatascar un test, que es exactamente lo que la puerta existe para impedir |
| **Se cierra una decisión abierta que la spec asumía** | Se reescribe la sección que contenía la suposición y se reaprueba. `§2.2.3` es el caso vivo | Una suposición que sobrevive a la decisión que la reemplaza es peor que no haberla escrito |
| **Cambia `Docs/`** | Al aprobar una spec de dominio se revisa qué specs la citan y se marcan como desfasadas | Es lo que le pasó a `SPEC-01` con `SPEC-02` y por eso existe el eje 1 de este plan |

### Corregir, spec nueva, o documentar la desviación

Regla para no discutirlo cada vez:

- **Cambia el *qué*** —alcance, criterios de aceptación, un requisito que deja de aplicar—:
  **spec nueva**, que marca la anterior como `obsoleta`. Los identificadores no se
  renumeran.
- **Cambia *cómo se dice*** —una ambigüedad, un literal desfasado, un criterio que faltaba—:
  **misma spec, versión nueva**, y se vuelve a aprobar.
- **Es consciente y temporal** —se sabe que se incumple y se acepta por ahora—:
  **desviación documentada** en la spec, con fecha y dueño, y con revisión obligatoria. Una
  desviación sin fecha es una mentira con buena letra.

### Cómo se sabe si el ciclo largo funciona

| Métrica | Cómo se lee |
| --- | --- |
| **Retraso entre que un requisito se revela falso y que la spec lo refleja** | Si crece, la spec se está convirtiendo en ficción. Es la métrica principal |
| **Requisitos cambiados después de escribir su código** | Rework. Alto significa que el ciclo corto no está haciendo su trabajo y hay que endurecer su condición de salida |
| **Desviaciones abiertas y su antigüedad** | Cuántas hay y cuánto llevan. El umbral a partir del cual una desviación es inaceptable **se fija cuando haya datos**, no ahora |
| **Specs marcadas desfasadas por un cambio de dominio** | Cuenta cuántas veces un cambio en `Docs/` rompió una spec. Si es frecuente, el dominio no está estable y las specs se están escribiendo demasiado pronto |

Ninguna de las cuatro tiene número objetivo hoy, y ponerlo sería inventarlo. Lo que sí se
puede hacer desde la primera vuelta es **registrarlas**, que es lo que permite fijarlas más
adelante con una medición en vez de con una intuición.

---

# Orden de corrección

1. **`C-1`, la decisión de `D5-1`** —la severidad de `mayor`—. Ya está tomada; aplicarla es
   lo primero porque arrastra `RF-14`, la tabla de §2.2.1, el diagrama, §2.2.3, `VER-28` y
   tres documentos de `Docs/`. Todo lo demás se escribe encima de ella. Arrastra también
   `D4-9`, la puerta de capítulo que su salvaguarda necesita y que no existe.
2. **Los bloqueantes restantes**: `D4-6` (el delta no sabe expresar `desaparecido`),
   `D4-4` (tablas que faltan), `D4-5` / `D2-1` (orden de recorte) y `C-2`, la decisión de
   `D6-1`. Son los puntos donde hoy habría que adivinar para escribir código. `D4-6` entra
   aquí tras reclasificarse a bloqueante el 2026-09-22: un valor de enumeración que el
   sistema no puede alcanzar deja `INV-02` leyendo desaparecidos como vivos.
3. **Eje 1 entero** (`D1-1`…`D1-6`). Es mecánico, barato y no depende de ninguna decisión.
   Hacerlo pronto evita seguir razonando sobre literales que ya no existen.
4. **`D5-2`, `D5-3`, `D5-4`**: completar §5.3 con las tres decisiones que faltan. No hay que
   cerrarlas, solo listarlas.
5. **Eje 3** (trazabilidad) y el resto de eje 2. Dependen de que los requisitos ya no se
   muevan.
6. **Ambigüedades restantes y menores.**

# Qué correcciones se pisan entre sí

- **`D5-1` toca cuatro sitios a la vez**: `RF-14`, la fila `en_verificacion → en_revision` de
  §2.2.1, el diagrama de §2.2.1 y §2.2.3 entera. Y fuera de la spec, `Docs/architecture.md`,
  `Docs/domain-knowledge.md` y `VER-28`. Va en un solo cambio o queda incoherente.
- **`D1-2` (diagrama) y `D5-1`** se pisan: no tiene sentido corregir los literales del
  diagrama y volver a tocarlo para quitar una transición. Primero la decisión, luego el
  dibujo.
- **`D2-1` / `D4-5` (orden de recorte) y `VER-06`**: si el orden se fija en la spec, el
  criterio de salida de `VER-06` —que hoy lleva su propio orden parcial— pasa a ser
  redundante o contradictorio. Se corrigen juntos.
- **`D4-4` (tablas que faltan) y `RF-13`**: hay dos salidas. Añadir las tablas, o sacar
  `INV-07` del alcance de la v1. La segunda cambia también el criterio 3 de §4, que es
  justamente el ejemplo de hallazgo `mayor`. Decidir antes de tocar.
- **`D3-5` (`RF-23`/`RF-25` trazan a frontend) y `D2-5` (`P-4` habla de visibilidad)** son el
  mismo problema: la spec del backend describe lo que se ve. Se resuelven con la misma
  regla —el backend devuelve, la interfaz muestra— y se aplican a la vez.
- **`D1-1` (glosario de `Hallazgo`) y `D1-5` / `D3-4` (clase `Invariante` y su tabla)** tocan
  §1.3 y §3.2.2 juntas.
- **`D4-2` (los dos límites de 100.000)** no se toca hasta que se apruebe la spec: el propio
  `P-1` declara que modifica `CLAUDE.md`, así que corregirlo antes sería aplicar una spec no
  aprobada.
