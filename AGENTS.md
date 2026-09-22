# AGENTS.md

Mapa de contexto de `My_novel_story`. Léelo antes de tocar nada: dice dónde está cada cosa, en qué orden cargarla y qué manda sobre qué.

**Proyecto:** sistema de IA que escribe novelas largas (caso base: terror, una sola obra) y el harness que lo evalúa.
**Rama de trabajo:** `contexto_semilla`.

## Dónde está cada cosa

| Necesitas | Archivo | Qué contiene |
| --- | --- | --- |
| Requisitos técnicos y stack | `CLAUDE.md` | FastAPI, React, límite de contexto de 100.000 tokens, SQLite con soporte vectorial, y el presupuesto de contexto que se deriva de ellos |
| Definiciones del dominio | `Docs/definitions.md` | Referencia normativa: los cinco planos, clases con atributos, tabla de relaciones, vocabularios controlados e invariantes `INV-01`…`INV-16` |
| Árbol y diagramas | `Docs/domain-knowledge.md` | El mismo modelo en Mermaid: árbol por planos, grafo de relaciones núcleo, ciclo de vida de la escena, secuencia de generación |
| Decisiones de sistema, agentes y proceso | `Docs/architecture.md` | Reparto frontend/backend, estructura por feature con `commons`, FSD en el frontend, los diez agentes del pipeline con sus habilidades e invariantes, el proceso de una escena y las decisiones `A-01`…`A-09` |
| Plan de verificación del sistema | `Docs/verification.md` | Primero **qué puede salir mal**: 24 modos de fallo `MF-01`…`MF-24` sobre las rejillas de MAST, ConStory-Bench y los fallos silenciosos, **ninguno sin estado**. Después **cómo se detecta**: 54 validadores `VER-01`…`VER-55`, cada uno con su punto ciego, más los 11 asumidos y lo que se aprendió al escribir cinco. Ninguno implementado hoy |
| Skills del proyecto | `.agents/skills/` | Contenido real de las ocho skills instaladas. Ver la sección "Skills" más abajo |
| Specs en curso | `specs/` | Un fichero por spec. Hoy `SPEC-01` backend del harness y `SPEC-07` modelo de fallo del pipeline, las dos en `en_revision`. `SPEC-07` va antes: `SPEC-01` se apoya en un modelo de fallo que todavía no existe |
| Specs ya aplicadas | `specs/aplicadas/` | Las que terminaron en `estado: aplicada`, con su `commit_de_aplicacion` en el frontmatter. Hoy `SPEC-03` referencias del dominio, `SPEC-04` puerta de capítulo y reclasificaciones, `SPEC-05` caducidad de las afirmaciones condicionales y `SPEC-06` estructura de `harness/`. **`SPEC-02`, vocabularios, no está**: se aplicó y su fichero se retiró antes de existir esta carpeta, y no se puede recuperar porque nunca llegó a commitearse. Es la única excepción y no se repite |
| Revisiones de documentos | `Docs/revisiones/` | Un `REV-NN.md` por documento revisado. Evalúa un documento **existente**; una spec dice qué va a cambiar. Por eso cuelga de `Docs/` y no de `specs/` |

> Las rutas de esta tabla son literales del repositorio: se copian tal cual, con su extensión. Si se renombra un documento, hay que actualizar esta tabla, el enlace en `CLAUDE.md` y todas las referencias en el mismo commit. Pasó lo contrario al renombrar `defintions` → `definitions.md` y `SRS.md` → `SPEC - Backend.md`: quedaron setenta referencias rotas.

## Orden de carga

1. `CLAUDE.md` — restricciones técnicas. Condicionan todo lo demás, así que van primero.
2. `Docs/definitions.md` — el modelo de dominio. Es la fuente de verdad.
3. `Docs/architecture.md` — cómo se organiza el código y quién habla con quién. Antes de escribir nada en `backend/` o `frontend/`.
4. `Docs/domain-knowledge.md` — solo cuando necesites ver la estructura de un vistazo o explicarla.
5. `Docs/verification.md` — cuando vayas a escribir una prueba o a cerrar una fila `VER-xx`.

No cargues los cinco enteros por costumbre. Para una tarea de backend suele bastar `CLAUDE.md`, la sección de invariantes de `Docs/definitions.md` y la de backend de `Docs/architecture.md`; para una discusión de arquitectura del dominio, el árbol de `Docs/domain-knowledge.md`.

## Precedencia

- En lo técnico manda `CLAUDE.md`. En lo de dominio manda `Docs/definitions.md`. En cómo se organiza el código manda `Docs/architecture.md`.
- `Docs/architecture.md` no redefine ni el stack ni el dominio: los desarrolla. Si contradice a `CLAUDE.md`, gana `CLAUDE.md`; si usa un nombre de clase o de enumeración que no está en `Docs/definitions.md`, el error es suyo.
- `Docs/verification.md` no introduce requisitos nuevos. Cada fila `VER-xx` cita el documento del que sale; una fila sin origen sobra.
- `Docs/domain-knowledge.md` es una vista, no una fuente. Si un diagrama contradice una definición, gana la definición y el diagrama se corrige.
- Nada de lo anterior sustituye al código: si el código contradice a los documentos, es un defecto de uno de los dos y hay que decidir cuál antes de seguir.

## Reglas de uso del modelo de dominio

- Los nombres de clase, atributo y valor de enumeración de `Docs/definitions.md` son literales. No los traduzcas, no los abrevies, no uses sinónimos.
- Toda comprobación del harness referencia su invariante por identificador (`INV-07`, no "la regla de los beats").
- Una entidad nueva se define primero en `Docs/definitions.md` y solo después se dibuja en `Docs/domain-knowledge.md`. Nunca al revés.
- Los identificadores publicados no se reutilizan ni se renumeran. Lo que deja de aplicar se marca como obsoleto, no se borra.

## Proceso de trabajo

Tres puertas en cadena. Cada una se abre solo con la anterior cerrada, y ninguna se salta porque el cambio parezca pequeño.

```
Docs/  →  spec aprobada  →  plan aprobado  →  código (TDD)  →  spec y Docs/ al día
```

**Qué cuenta como aprobación.** El frontmatter del propio fichero: `id`, `estado` (`borrador | en_revision | aprobada | aplicada | obsoleta`), `aprobada_por` y `fecha_aprobacion`. Los planes llevan el mismo.

**Una spec aplicada se mueve, no se borra.** Cuando su contenido ya está en `Docs/`, pasa a `estado: aplicada`, se anota `fecha_aplicacion` y `commit_de_aplicacion` —que necesita un commit propio, porque el hash no existe hasta después— y el fichero se mueve con `git mv` a `specs/aplicadas/`. Así `specs/` contiene lo que está en curso y nada más, y sigue siendo posible leer por qué se decidió cada cosa. Las referencias son siempre por identificador (`SPEC-03`), nunca por ruta, así que mover el fichero no rompe nada.

Sin `estado: aprobada` no se pasa, aunque el documento esté escrito entero y aunque se haya hablado. "Lo comentamos ayer" no es una aprobación; el campo sí. `SPEC-NN` es un identificador estable: no se reutiliza ni se renumera, y lo que deja de aplicar pasa a `obsoleta` en vez de borrarse. Los identificadores internos de una spec (`RF-xx`, `O-x`, `M-x`, `P-x`) tampoco se renumeran al reescribirla.

### 1. Actualizar `Docs/`

`Docs/` es lo normativo permanente. Hay dos clases de cambio y no se tratan igual:

- **Cambio documental** —corregir un error, aclarar una frase, añadir un diagrama de algo ya decidido—: se hace directamente, sin spec.
- **Cambio que decide algo nuevo** —una clase, una invariante, una decisión de arquitectura, un umbral—: **necesita spec aprobada primero**. El documento se actualiza después, no antes.

Se mantienen las reglas que ya existen: una entidad se define primero en `Docs/definitions.md` y solo después se dibuja en `Docs/domain-knowledge.md`; un cambio de atributo obligatorio lleva su migración en el mismo commit; los identificadores publicados no se renumeran. Y este archivo se actualiza en el mismo commit que mueve un archivo de contexto.

### 2. Crear o actualizar una spec

Un fichero propio en `specs/`, con su `SPEC-NN` en el frontmatter. Responde a tres cosas y solo a tres: **qué problema resuelve**, **qué tiene que ser verdad al terminar** y **qué queda explícitamente fuera**.

- **Antes de escribirla se pregunta.** Una spec con huecos rellenados por suposición es peor que no tener spec, porque parece acordada. Las dudas se preguntan al escribirla, no se descubren implementando.
- **Una spec no dice cómo se hace.** Nada de ficheros, funciones ni orden de tareas: eso es el plan.
- **Cita lo que la gobierna** por identificador: `INV-xx`, `A-xx`, `VER-xx`.
- Termina en `estado: aprobada`, o no hay nada más que hacer con ella.

### 3. Plan de implementación

Vive en `specs/plans/PLAN-NN.md`, con el mismo identificador que su spec y su propio estado. **No se confunde con `Docs/revisiones/REV-NN.md`**, que revisa el documento antes de aprobarlo: el plan dice cómo se construye el código y nace después de la aprobación.

- **No se crea un plan si su spec no está aprobada.** Un plan sin spec aprobada está resolviendo un problema que nadie ha acordado.
- Dice qué ficheros se tocan, en qué orden, **qué prueba cubre cada paso** y qué filas `VER-xx` de `Docs/verification.md` cierra.
- Cada paso debe dejar el repositorio funcionando. Un paso que solo tiene sentido con el siguiente son un paso.
- También se aprueba, y es la tercera puerta.

### 4. Crear o modificar código

- **No se escribe código si el plan no está aprobado.** Ni un fichero de andamiaje.
- **TDD, en este orden:** primero la prueba que falla, después el código mínimo que la pasa, después el refactor. Ningún código de producción nace sin una prueba que haya fallado antes. Esto es la misma exigencia que el proyecto ya tiene para las invariantes: una regla que nunca ha fallado en las pruebas no está verificada, solo declarada.
- **Al terminar, en el mismo commit:** la spec al día, `Docs/` al día y la fila `VER-xx` actualizada si se ha cerrado alguna.

### Cuando el código descubre que la spec estaba mal

Pasa, y es sano que pase. Lo que no vale es seguir.

Se para, se corrige la spec, se vuelve a aprobar, y si el plan cambia de forma, se vuelve a aprobar también. El código nunca avanza por delante de la spec: en cuanto lo hace, la spec deja de gobernar lo que se va a hacer y pasa a describir mal lo que ya se hizo. A las tres semanas es ficción y nadie la lee.

## Skills

El contenido real vive en `.agents/skills/` y **se versiona con el repositorio**. Claude Code lee esa carpeta directamente, así que tras clonar no hay que hacer nada: las skills están disponibles. `.claude/skills/` sigue en `.gitignore` porque `npx skills add` crea allí enlaces que git en Windows no guarda como tales, y no hacen falta.

**Ninguna skill se actualiza sola, y no hay lockfile.** Las dos de upstream se actualizan a mano: se reinstalan con `npx skills add <repo> --skill <nombre>` y se revisa el diff antes de aceptarlo. Su origen y el hash con el que entraron están en la tabla de arriba, que es donde hay que mirar para saber qué se instaló y desde dónde.

| Skill | Cuándo usarla | Procedencia |
| --- | --- | --- |
| `spec-and-plan` | Empezar cualquier cambio que decida algo nuevo. Ejecuta las puertas de "Proceso de trabajo" y comprueba si están abiertas | Propia |
| `fastapi` | Endpoints, dependencias, modelos Pydantic, streaming: los idiomas del framework | Oficial, de `github.com/fastapi/fastapi`, ruta `.agents/skills/fastapi/`. Instalada 2026-09-21, hash `187b2e06` |
| `coherencia-docs` | Revisar la coherencia entre los documentos de contexto: citas rotas por identificador, contradicciones, deriva de literales y afirmaciones que caducan en silencio. Antes de un merge que toque `Docs/` | Propia. Escrita sobre un borrador del usuario y adaptada al repositorio; ver su § "Procedencia" |
| `backend-feature` | Decidir dónde va un fichero de `backend/` y de qué puede depender. La contraparte de FSD en el servidor (`A-01`, `A-02`) | Propia |
| `feature-sliced-design` | Decidir dónde va un fichero del frontend, resolver un cross-import o revisar la estructura de capas (`A-09`) | Oficial de FSD v2.1, de `github.com/feature-sliced/skills`. Instalada 2026-09-21, hash `e2b86275` |
| `harness-invariantes` | Implementar o revisar una comprobación `INV-xx`: regla o juez, severidad, hallazgo y caso negativo | Propia |
| `verification-plan` | Escribir o revisar un `verification.md` (también llamado `validation.md` o `evaluation.md`), decidir cómo se prueba una afirmación o clasificarla en T/A/I/D/U | Propia. Construida sobre una hoja de referencia de 19 metodologías; el flujo, la plantilla y los criterios de selección son nuestros |
| `sqlite-vec` | Crear tablas `vec0`, hacer consultas KNN o serializar embeddings al implementar la persistencia | **Vendorizada y sin mantenimiento.** Su autor la borró del repositorio original; se recuperó del historial de git. Ver `.agents/skills/sqlite-vec/PROCEDENCIA.md` |

**Por qué se versiona el contenido y no basta con `skills-lock.json`.** Un lockfile fija una versión, pero no garantiza que siga existiendo: si el upstream borra el contenido, no hay nada que reinstalar. Es exactamente lo que pasó con `sqlite-vec`. La única garantía es tener el contenido en el repositorio.

**Cuidado con `sqlite-vec`.** Está abandonada y describe una librería viva, así que envejece en silencio: con el tiempo dirá cosas de `vec0` que ya no son ciertas y nada avisará. Contrástala con la documentación oficial de `asg017/sqlite-vec` antes de confiar en ella, y actualiza la fecha de revisión de su `PROCEDENCIA.md` cada vez que lo hagas.

## Todavía no existe

Estas rutas están reservadas y aparecerán aquí en cuanto se creen. Si encuentras una que no está en la tabla de arriba, añádela.

- `backend/` — servicio FastAPI.
- `frontend/` — aplicación React.
- `harness/` — ejecución de los validadores de `Docs/verification.md` y sus fixtures, en las tres carpetas que declara `Docs/architecture.md` § "El harness": `documentos/`, `evals/` y `adversarial/`. Se escribieron cinco a modo de prueba y se retiraron; lo que enseñaron está en `Docs/verification.md` § "Lo que se aprendió al implementar".
- `specs/plans/` — un `PLAN-NN.md` por spec aprobada. Nace con el primer plan.
- `Docs/decisions/` — decisiones de arquitectura fechadas.

## Mantenimiento de este archivo

Este archivo cambia cada vez que se añade, renombra o mueve un archivo de contexto. Al hacerlo:

1. Añade o corrige la fila en "Dónde está cada cosa" en el mismo commit que toca el archivo.
2. Describe qué contiene, no solo cómo se llama. Una fila que solo repite el nombre no ahorra ninguna lectura.
3. Si el archivo nuevo sustituye a otro, borra la fila vieja en vez de dejar las dos.
4. Mantén el total por debajo de unas 150 líneas. Si crece más, parte el contenido en un documento propio y deja aquí solo el puntero.
