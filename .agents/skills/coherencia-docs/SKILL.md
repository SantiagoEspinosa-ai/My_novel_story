---
name: coherencia-docs
description: >
  Detecta y resuelve inconsistencias entre los documentos de contexto del proyecto
  (docs/definitions.md, docs/domain-knowledge.md, docs/architecture.md,
  docs/verification.md, CLAUDE.md y AGENTS.md): referencias de sección rotas, citas
  rotas a identificador, contradicciones factuales, deriva terminológica, afirmaciones
  de estado obsoletas, invariantes condicionales que han dejado de cumplirse,
  requisitos sin clasificar y contenido colocado en el documento equivocado. Usar
  cuando el usuario pida revisar la coherencia de la documentación, sospeche que dos
  documentos no concuerdan, antes de un merge que toque docs/, tras renumerar
  secciones, o cuando aterrice código que convierta en obsoletas las afirmaciones de
  estado de verification.md. Produce primero un informe, después un plan, y solo
  aplica cambios con aprobación explícita.
---

# Coherencia documental

Comparas los documentos de contexto del proyecto entre sí, localizas inconsistencias, las
clasificas y las resuelves. **Nunca editas sin aprobación explícita.**

## Alcance

| Documento | Papel |
| --- | --- |
| `docs/definitions.md` | Vocabulario del dominio |
| `docs/domain-knowledge.md` | Cómo funciona una novela |
| `docs/architecture.md` | Decisiones técnicas, agentes, proceso |
| `docs/verification.md` | Cómo se gana confianza: modos de fallo, validadores, puntos ciegos |
| `CLAUDE.md` | Stack, convenciones y reglas de dominio que el código debe respetar |
| `AGENTS.md` | Mapa de contexto. Documento **derivado**: nunca gana un conflicto |

`specs/` y `docs/revisiones/` entran como **destino de citas**, no como sujetos de revisión.

## Reglas innegociables

1. **Informe antes que plan, plan antes que edición.** Tres pasos separados, con parada en cada uno.
2. **Nada de escribir con el árbol sucio.** `git status` al empezar.
3. **Una incidencia = una edición atómica con ID.** El usuario aprueba por lotes.
4. **Ante la duda, informar en vez de resolver.**
5. **No inventes contenido.** Si la resolución exige información que no está en ningún documento, es decisión del usuario.
6. **Cita siempre los dos lados:** fichero, línea y texto literal.

---

## Jerarquía de autoridad

La fija `AGENTS.md` § "Precedencia" y manda sobre esta tabla:

| Tipo de afirmación | Manda | Los demás |
| --- | --- | --- |
| Qué significa un término, cómo se llama un concepto | `docs/definitions.md` | Lo usan, no lo redefinen |
| Cómo funciona el dominio | `docs/domain-knowledge.md` | Lo aplican. Es **vista**, no fuente: si un diagrama contradice una definición, gana la definición |
| Decisiones técnicas: stack, estructura, agentes, proceso, límites | `docs/architecture.md` | Lo referencian |
| Reglas de dominio que el código debe respetar, convenciones, comandos | `CLAUDE.md` | Las invocan |
| Qué modo de fallo existe, qué validador lo cubre y con qué punto ciego | `docs/verification.md` | — |

`docs/verification.md` **no introduce requisitos nuevos**: cada fila cita el documento del
que sale, y una fila sin origen sobra. Eso lo deja como autoridad sobre el *método* y
subordinado sobre los *hechos*. Sus citas de origen son el material más valioso de la
revisión.

### Criterio de pertenencia

- Cambiaría al cambiar de framework, de modelo o de base de datos → `docs/architecture.md`.
- Cambiaría aunque la novela se escribiera a mano → `docs/domain-knowledge.md`.
- Es «X significa Y» → `docs/definitions.md`.
- Describe cómo se comprueba algo y con qué punto ciego → `docs/verification.md`.
- Es una instrucción operativa para quien escribe código → `CLAUDE.md`.

---

## Taxonomía de inconsistencias

| Código | Tipo | Qué es | Resolución |
| --- | --- | --- | --- |
| `REF` | Referencia rota o desplazada | Una cita `§N` o a un identificador (`INV-xx`, `VER-xx`…) apunta a algo inexistente, o a algo que ya no dice lo que la cita afirma | Automática si el destino correcto es identificable |
| `COB` | Cobertura | Una regla o requisito existe y no aparece cubierto en `docs/verification.md` | Propuesta de fila nueva; la decide el usuario |
| `EDO` | Estado obsoleto | Una afirmación de estado ya no coincide con el repositorio | Decisión del usuario |
| `CND` | Invariante condicional caducada | Una afirmación es cierta *porque* algo no existe, y esa condición ha cambiado | **Máxima prioridad.** Decisión del usuario |
| `FAC` | Factual | Dos documentos afirman cosas incompatibles | Decisión del usuario |
| `TER` | Terminológica | Mismo concepto con nombres distintos, o literal escrito fuera de su forma canónica | Automática si hay canónico en `docs/definitions.md` |
| `AUT` | Autoridad | El mismo asunto desarrollado a fondo en dos documentos | Propuesta: cuál manda, el otro enlaza |
| `ALC` | Alcance | Contenido en el documento equivocado | Propuesta de movimiento |
| `OBS` | Obsolescencia | Un documento refleja una decisión que otro ya cambió | Decisión del usuario |
| `HUE` | Hueco | Término definido que nadie usa, o concepto usado que nadie define | Solo informar |
| `EST` | Estructural | Enlaces rotos, numeración descuadrada, anclas inexistentes | Automática |

**Severidad:** alta → `CND`, `REF`, `FAC`, `OBS`, `COB`. Media → `EDO`, `TER`, `AUT`, `ALC`. Baja → `HUE`, `EST`.

### Por qué `REF` es la comprobación de mayor valor aquí

Este proyecto cita **por identificador**, no por ruta ni por título: `INV-07`, `VER-38`,
`MF-24`, `PC-13`, `RF-26`, `A-01`, `F-16`, `D4-9`, `SPEC-04`. Son más de mil citas. Se
rompen en silencio y nada en el repositorio lo detecta.

Comprobarlo tiene dos mitades, y las dos son necesarias:

1. **Existencia** — el identificador está declarado. Mecánico, con `grep`.
2. **Sustancia** — lo declarado sigue diciendo lo que la cita afirma. Semántico. Una cita
   que apunta a un identificador existente pero equivocado es peor que una rota, porque
   parece correcta.

**Cuidado con los falsos positivos.** No todo se declara en una fila de tabla: `O-x`,
`M-x`, `P-x` y `D-x` se declaran en prosa, `SPEC-NN` y `REV-NN` en el frontmatter, y un
identificador retirado se marca tachado en vez de borrarse. Verifica antes de reportar.

### Por qué `CND` es lo más urgente

Varias afirmaciones son fuertes **precisamente porque una capacidad no existe**: no hay
migración porque no hay base de datos; cero validadores implementados porque no hay
código; un punto ciego no se tapa porque no hay nada que auditar. Todas dejan de ser
ciertas el mismo día, y nada avisa.

Peor: una premisa cierta puede sostener una conclusión falsa. `VER-45` eximía la columna
"Dónde vive" *porque* esas carpetas no existen —cierto— y con eso tapó diecisiete rutas mal
escritas que existía para cazar. Está en `F-16` y es `MF-24`. **Un criterio que no puede
marcar nada está verde por construcción, y eso no se distingue de estar verde por mérito.**

---

## Procedimiento

### Fase 0 — Preparación

1. `git status`. Si hay cambios sin commitear en el alcance, avisa.
2. Por cada documento: árbol de encabezados con su numeración literal, tamaño y fecha del
   último commit (`git log -1 --format=%cs -- <fichero>`). **Un documento con fecha más
   vieja que los demás es el primer sospechoso de `OBS`.**
3. Comprueba qué carpetas de código existen: es lo que decide si las afirmaciones de
   estado siguen siendo válidas.

### Fase 1 — Pasada determinista

Barata, con `grep` y `git`, antes de gastar contexto en razonar.

- **Mapa de citas por identificador.** Extrae toda cita `INV-xx`, `VER-xx`, `MF-xx`,
  `PC-xx`, `RF-xx`, `A-xx`, `F-xx`, `D*-*`, `SPEC-NN`, `REV-NN`. Para cada una, comprueba
  que esté declarada. Ojo a los falsos positivos de arriba.
- **Mapa de citas por sección.** `§N`, `sección N`, enlaces con ancla.
- **Índice de términos.** Nombres de clase, atributo y valor de enumeración de
  `docs/definitions.md`. **Normaliza el guion bajo escapado** antes de contar, o los
  recuentos salen mal: en las tablas los atributos se escriben con la barra delante.
- **Literales fuera de su forma canónica.** Un valor de enumeración escrito en mayúscula,
  con espacios o traducido. `definitions.md` es el canónico.
- **Números con unidad.** Tokens, recuentos de filas, número de agentes, de estados, de
  invariantes. Dos cifras para el mismo concepto son `FAC` alta. **Y cuenta las listas
  enumeradas contra el número que las anuncia.**
- **Marcadores de estado.** `hoy`, `todavía`, `por ahora`, `aún no`, `cero`, `ninguno`.
- **Marcadores condicionales.** `porque no hay`, `mientras no`, `en cuanto`, `cuando haya`,
  `se eximen`, `por construcción`, `sale gratis`. Cada uno es una `CND` a verificar.

### Fase 2 — Pasada semántica

Solo sobre lo que la Fase 1 no ve, y siempre por **pares**:

1. `verification.md` ↔ `architecture.md` — el par con más citas explícitas.
2. `verification.md` ↔ `CLAUDE.md` — reglas de dominio frente a su cobertura.
3. `definitions.md` ↔ `domain-knowledge.md` — el par que más deriva. Recuerda que el
   segundo es una **vista**: una clase que no dibuja puede estar ausente a propósito, pero
   un literal mal escrito nunca lo está.
4. `architecture.md` ↔ `CLAUDE.md` — decisiones frente a convenciones. **Busca frases
   duplicadas**: son el mecanismo por el que una corrección futura entra a medias.
5. `domain-knowledge.md` ↔ `architecture.md`
6. `definitions.md` ↔ `architecture.md` / `verification.md`

No releas documentos enteros: trabaja sobre los conceptos compartidos y los destinos de
las citas.

### Fase 3 — Informe (PARADA)

Orden fijo: `CND` primero, después el resto por severidad. Cada incidencia cita fichero,
línea y texto literal de los dos lados, y declara su confianza.

Incluye siempre:
- **Huecos detectados**, y las familias de identificador que **no existen** aunque se
  esperaran. Un resultado negativo es un resultado.
- **No revisado**: qué ha quedado fuera y por qué.

Termina preguntando: **«¿Sigo con el plan de resolución, o quieres ajustar el diagnóstico primero?»**

### Fase 4 — Plan (PARADA)

Agrupado por cubo, no por documento: automáticas, requieren decisión, reestructuración,
solo informar. Una pregunta por incidencia que necesite decisión, con las dos opciones, la
recomendación según la jerarquía y qué ficheros cambiarían.

**Si un lote decide algo nuevo —una convención, un validador, una carpeta—, no se aprueba
en el chat: necesita spec.** Es la primera puerta de `AGENTS.md` y esta skill no la salta.

### Fase 5 — Aplicación

Solo tras aprobación explícita, y solo de los lotes aprobados.

1. Lote por lote, un commit por lote citando los IDs.
2. Conserva el estilo del documento: tono, formato de tabla, nivel de encabezado.
3. **Un literal equivocado se cita en cursiva, nunca entre acentos graves** (`F-15`): si no,
   los propios validadores de documentos marcan el texto que explica el defecto.
4. **Si aparece una inconsistencia nueva al aplicar, para y repórtala.** No la resuelvas
   sobre la marcha.
5. Muestra `git diff --stat` tras cada lote.

### Fase 6 — Cierre

Qué se resolvió, qué quedó pendiente de decisión, qué debe revisar el usuario a mano.

---

## Qué no es esto

- No es un corrector de estilo.
- No es un generador de documentación: una fila `COB` se propone vacía.
- No es un linter de markdown.
- **No reclasifiques un validador ni cambies la severidad de una invariante.** Eso afirma
  algo sobre lo que el proyecto puede demostrar, y lo decide una persona.

---

## Procedencia

Propia. Escrita a partir de un borrador del usuario y adaptada al repositorio en la sesión
del 2026-09-22. Los cambios respecto al borrador son todos por la misma razón: el borrador
nombraba rutas y estructuras que aquí no existen, y `VER-45` las habría marcado.

- `docs/` pasa a `docs/`; `src/backend/` y `src/frontend/` pasan a las carpetas reservadas
  reales de `AGENTS.md`.
- El borrador remitía a un fichero de autoridad que no existe. La jerarquía la fija
  `AGENTS.md` § "Precedencia", y se cita esa.
- La tabla de trazabilidad y las clases T/A/I/D/U que el borrador daba por supuestas en
  `verification.md` no son su estructura actual: se sustituyen por modos de fallo,
  validadores y puntos ciegos, que es lo que el documento tiene hoy.
- Se añade el mapa de citas **por identificador**, sus falsos positivos conocidos y el caso
  `F-16`, porque es el defecto más frecuente de este repositorio.
