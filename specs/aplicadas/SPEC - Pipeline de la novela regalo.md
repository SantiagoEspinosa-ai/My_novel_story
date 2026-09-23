---
id: SPEC-26
titulo: El pipeline de la novela regalo
estado: aplicada
aprobada_por: "autor del proyecto, en sesión (sustituir por su identificador)"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: b68c505
fecha: 2026-09-23
version: 4
enmienda_aprobada: 2026-09-23
---

> **Historial.** v1: redactada con las doce respuestas, con `O-1` y `O-2`
> abiertas. v2: el autor aprueba con las dos propuestas, que pasan a los
> requisitos. v3 (enmienda del autor, 2026-09-23): **`INV-14` es general** —*«si
> Deterioro se queda, su invariante también»*— y se retira lo específico de
> terror con la lista que el autor aprobó (`RF-20` enmendado, `RF-21` nuevo).
> Terror se conserva como género, y el brief y los guiones de las mediciones
> antiguas se quedan: *«son la evidencia de lo medido y /docs los va a necesitar
> para el registro de iteraciones»*.
> v4 (decisión del autor, 2026-09-23): *«el escritor recibe el capítulo anterior
> completo para que tenga continuidad»* (`RF-22`).

# SPEC-26 — El pipeline de la novela regalo

> **De dónde salen las decisiones.** De las respuestas del autor a las doce
> preguntas de aclaración del 2026-09-23. La que cambia la forma del pipeline,
> en sus palabras: *«un agente tiene que revisar y aprobar el plan comparando
> con lo que escribió el usuario»*.

## Qué problema resuelve

`SPEC-25` deja una ficha del destinatario validada, pero **nada la lee todavía**.
El pipeline de hoy escribe una novela de terror a partir de una escaleta hecha a
mano, con seis escenas de 250 a 800 palabras por capítulo, y un juez que solo dice
PASA o FALLO con una rúbrica de terror. La última ejecución real dio capítulos de
3.109 a 3.512 palabras, más del doble de lo que pide el enunciado.

Faltan cinco cosas:

1. **Alguien que convierta la ficha en un plan** de 10 capítulos, y alguien que
   compruebe que ese plan es fiel a lo que dijo el comprador.
2. **Un editor que juzgue lo que pide el enunciado**: continuidad, tono, calidad
   narrativa y personalización natural, con nota por criterio y justificación.
3. **Validadores de personalización deterministas**: nombres exactos, elementos
   imprescindibles presentes y prosa que no se repita.
4. **Los dos hooks de Claude Code** que pide el enunciado.
5. **Que las reglas del terror no se apliquen a una novela que no lo es.**

## Qué tiene que ser verdad al terminar

### La forma

- **RF-01.** Un capítulo es **una escena** de entre 1.000 y 1.500 palabras. Se
  reutilizan la reanudación, la story bible, las invariantes de escena y `INV-21`,
  y cada llamada al Escritor produce un capítulo. `INV-17` comprueba la longitud.

### El plan

- **RF-02.** Un agente **Planificador** convierte la ficha terminada en el plan de
  los 10 capítulos: qué pasa en cada uno y qué valor cambia, qué personajes y
  lugares intervienen y en qué capítulo aparece cada elemento imprescindible.
- **RF-03.** Por cada elemento imprescindible, el plan declara **unas palabras
  clave** (por ejemplo, «Lisboa» y «tren» para un viaje) que el código buscará en
  el capítulo previsto (`INV-23`).
- **RF-04.** **El plan declara la cronología** que usará el validador formal: el
  momento de la fábula de cada capítulo, la fecha de nacimiento de cada personaje
  y los sucesos que excluyen a alguien (una muerte, una partida definitiva). Si
  hay una analepsis, la declara el plan (`SPEC-24`). La verificación con Lean
  queda fuera de esta spec; lo que se decide aquí es que **el dato lo pone el
  plan**.
- **RF-05.** Un agente **Revisor del plan** compara el plan con la ficha antes de
  escribir nada. Comprueba que el género, el tono, la ocasión y el papel del
  destinatario se respetan, que el plan no contradice ni inventa datos de la
  ficha y que la historia tiene arco. Aprueba o devuelve objeciones concretas.
- **RF-06.** Antes del Revisor, el código comprueba lo que se puede comprobar
  sin juicio: que hay 10 capítulos, que cada imprescindible tiene capítulo y
  palabras clave, que los nombres coinciden con la ficha y que ninguna palabra
  vetada aparece en el plan. **El Revisor juzga la fidelidad; la cobertura la
  cuenta el código.**
- **RF-07.** Con objeciones, el Planificador rehace el plan con ellas delante,
  hasta **3 revisiones** (configuración, `O-1`). Si se agota, **la generación
  no empieza** y lo informa: sin plan aprobado no se escribe.

### La escritura y el editor

- **RF-08.** El Escritor escribe cada capítulo a partir del plan y de la ficha. Su
  prompt lleva lo que las reglas le van a exigir (Regla 4): los nombres exactos,
  las palabras clave de los imprescindibles de ese capítulo y las vetadas.
- **RF-09.** Un agente **Editor** juzga cada capítulo y **no reescribe**: da una
  nota de **1 a 5** por criterio, con una justificación obligatoria y unas
  instrucciones concretas. Los criterios son: continuidad, tono, arco, coherencia
  de personajes, ritmo y personalización natural (no forzada). El Editor se lanza
  aislado, como el Juez de hoy (`A-06`).
- **RF-10.** La nota que obliga a reescribir es **configuración y está pendiente
  de medida**. El valor inicial es «menos de 3 en cualquier criterio», y la
  medida que lo ajustará es comparar las notas del Editor con la revisión humana
  de una novela completa (sección 5 del enunciado).
- **RF-11.** Por debajo del umbral, el capítulo vuelve al Escritor con las
  instrucciones del Editor, **hasta 3 reescrituras**. Si se agotan, se acepta como
  `aceptada_por_rendicion`, con sus hallazgos visibles, igual que hoy.
- **RF-12.** Al terminar la novela, el Editor hace un **juicio de obra**: el arco
  completo, la coherencia entre capítulos y el final, para cazar un final
  abrupto. No recibe el texto entero, que `CLAUDE.md` prohíbe mandar al modelo:
  recibe los resúmenes de los capítulos y el texto completo del último. Su
  resultado queda como hallazgos de nivel obra; qué bloquea la publicación lo
  decide la spec de la puerta de publicación.

### Los validadores deterministas

- **RF-13 (`INV-22`, `bloqueante`).** Los nombres del destinatario y de los
  personajes aparecen **escritos exactamente** como en la story bible. Un nombre
  parecido que no es igual («Irena» por «Irene») hace que el capítulo **se
  reescriba**, con el mismo mecanismo que `INV-21`: vuelve al Escritor con el
  fragmento exacto, **el mismo contador y el mismo tope de 2 reescrituras** que
  `INV-21` (`O-2`), y al agotarse se para sin rendición.
- **RF-14 (`INV-23`, `mayor`).** Las palabras clave de cada imprescindible
  aparecen en su capítulo previsto. Si faltan, el capítulo se reescribe dentro de
  los intentos de calidad.
- **RF-15 (`INV-24`, `bloqueante`, nivel obra).** Cada imprescindible aparece en
  **al menos un capítulo** de la novela, comprobado contra la tabla de usos de
  SQLite. Si queda alguno, **la novela no se da por terminada**.
- **RF-16 (`INV-25`, `menor`).** Prosa repetitiva: avisa si el nombre del
  destinatario aparece demasiadas veces en un capítulo o si una frase se repite
  entre capítulos (`FraseRecurrente`). Los umbrales son configuración y están
  pendientes de medida.

### Los hooks

- **RF-17. Hook de validación del capítulo.** Cuando el Escritor termina su
  respuesta, un script comprueba la longitud, los nombres y las vetadas. Si algo
  falla, se lo devuelve **dentro de la misma sesión** para que lo corrija antes de
  entregar. Es una primera línea más barata que una delegación nueva; **las
  puertas del código siguen mandando**.
- **RF-18. Hook de policy.** Impide a cualquier agente del pipeline usar
  herramientas que no le tocan (leer ficheros, red, ejecutar órdenes), y cada
  bloqueo queda en el audit log.
- **RF-19.** Los dos hooks actúan **solo sobre las delegaciones del pipeline**,
  nunca sobre una sesión interactiva de Claude Code en el mismo proyecto. Un hook
  de policy que bloqueara las herramientas de quien desarrolla sería un defecto.

### El género

- **RF-20 (enmendado en v3).** Las invariantes propias de terror (`INV-10`,
  `INV-11`, `INV-12` e `INV-16`) **se retiran como obsoletas** (`RF-21`) y no se
  aplican a ninguna obra. `INV-13`, `INV-14` e `INV-15` son narrativa general y
  se aplican siempre. El informe dice cuáles están obsoletas en vez de callarse.
  Terror se conserva como género: una obra de terror se escribe con su género y
  su tono en el prompt, como cualquier otra.
- **RF-21 (nuevo en v3). Lo que se retira y lo que se queda.** Se retira lo
  específico de terror: la curva de dread y sus válvulas, los presagios, la
  amenaza con su tell y su grado de explicación, y la fuente del miedo; y con
  ellas `INV-10`, `INV-11`, `INV-12` e `INV-16`, que se marcan obsoletas sin
  renumerar. Los presagios indexables pasan a ser *setups* pendientes. **Se
  queda** lo que parece de terror y es narrativa general: `SetupYPago` (y su
  vocabulario `estado_de_presagio`), `PuntoDeNoRetorno`, `Deterioro` con sus
  ejes, los ejes de valor, el registro de conocimiento, los roles dramáticos y el
  bloque `fichas_y_setups`. **No se borran** el brief de terror ni los guiones de
  las mediciones antiguas.

- **RF-22 (nuevo en v4). El capítulo anterior completo.** El Escritor recibe el
  texto aceptado del capítulo anterior entero, además de los resúmenes. En la
  novela regalo cada capítulo es una escena, así que con el alcance de `SPEC-21`
  —la escena anterior no cruza el capítulo— no le llegaba nunca. La obra de
  terror, con varias escenas por capítulo, conserva el alcance de `SPEC-21`.

## Cuestiones resueltas

- **O-1. Tope de revisiones del plan (`RF-07`) → 3**, igual que las reescrituras
  del Editor.
- **O-2. Tope de reescrituras por nombre mal escrito (`RF-13`) → el mismo
  contador y tope que `INV-21` (2)**, porque es el mismo tipo de error: una regla
  del código que le dice al Escritor exactamente qué escribió mal.

## Qué queda explícitamente fuera

- **Langfuse**: sesiones, spans, scores y prompts versionados. Es la spec de
  observabilidad.
- **La web, las versiones y la regeneración por cambio del lector.**
- **La puerta de publicación**: conectar Lean, qué hallazgos de obra bloquean una
  versión y TLA+.
- **Los cinco briefs de evaluación, la revisión humana y la iteración de tuning**,
  aunque `RF-10` nombra la revisión humana como la medida del umbral.
- **La validación visual con el navegador.**

## Lo que la gobierna

- `CLAUDE.md`: límite de 100.000 tokens y nunca el texto completo de la obra al
  modelo (`RF-12`).
- `A-03`: un agente por llamada. `A-06`: el Editor, aislado del Escritor.
- `SPEC-14`: los agentes se ejecutan por delegación.
- `SPEC-24`: una analepsis la declara el plan (`RF-04`).
- `SPEC-25`: la ficha es la única entrada que viene del comprador; `INV-21`.
- `INV-17` (longitud), `INV-21` (vetadas) y las nuevas `INV-22` a `INV-25`, que se
  añaden a `Docs/definitions.md` al aplicar esta spec.
