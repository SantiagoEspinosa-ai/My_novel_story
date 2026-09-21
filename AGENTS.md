# AGENTS.md

Mapa de contexto de `My_novel_story`. Léelo antes de tocar nada: dice dónde está cada cosa, en qué orden cargarla y qué manda sobre qué.

**Proyecto:** sistema de IA que escribe novelas largas (caso base: terror, una sola obra) y el harness que lo evalúa.
**Rama de trabajo:** `contexto_semilla`.

## Dónde está cada cosa

| Necesitas | Archivo | Qué contiene |
| --- | --- | --- |
| Requisitos técnicos y stack | `CLAUDE.md` | FastAPI, React, límite de contexto de 100.000 tokens, SQLite con soporte vectorial, y el presupuesto de contexto que se deriva de ellos |
| Definiciones del dominio | `Docs/defintions` | Referencia normativa: los cinco planos, clases con atributos, tabla de relaciones, vocabularios controlados e invariantes `INV-01`…`INV-16` |
| Árbol y diagramas | `Docs/domain-knowledge` | El mismo modelo en Mermaid: árbol por planos, grafo de relaciones núcleo, ciclo de vida de la escena, secuencia de generación |
| Decisiones de sistema, agentes y proceso | `Docs/architecture.md` | Reparto frontend/backend, estructura por feature con `commons`, FSD en el frontend, los diez agentes del pipeline con sus habilidades e invariantes, el proceso de una escena y las decisiones `A-01`…`A-09` |
| Plan de verificación del sistema | `Docs/verification.md` | Cómo se prueba que el código hace lo que dice: 37 afirmaciones `VER-01`…`VER-37` con clase T/A/I/D/U, metodología, criterio de salida y caso negativo |
| Skills del proyecto | `.agents/skills/` | Contenido real de las tres skills instaladas. Ver la sección "Skills" más abajo |
| Utilidades del repositorio | `scripts/` | `link-skills.mjs`, que recrea los enlaces de `.claude/skills/` tras clonar |

> El archivo se llama `defintions`, sin la segunda `i` y sin extensión. La ruta de la tabla es la literal del repositorio. Si se corrige el nombre, hay que actualizar esta tabla y el enlace en `CLAUDE.md` en el mismo commit.

## Orden de carga

1. `CLAUDE.md` — restricciones técnicas. Condicionan todo lo demás, así que van primero.
2. `Docs/defintions` — el modelo de dominio. Es la fuente de verdad.
3. `Docs/architecture.md` — cómo se organiza el código y quién habla con quién. Antes de escribir nada en `backend/` o `frontend/`.
4. `Docs/domain-knowledge` — solo cuando necesites ver la estructura de un vistazo o explicarla.
5. `Docs/verification.md` — cuando vayas a escribir una prueba o a cerrar una fila `VER-xx`.

No cargues los cinco enteros por costumbre. Para una tarea de backend suele bastar `CLAUDE.md`, la sección de invariantes de `Docs/defintions` y la de backend de `Docs/architecture.md`; para una discusión de arquitectura del dominio, el árbol de `Docs/domain-knowledge`.

## Precedencia

- En lo técnico manda `CLAUDE.md`. En lo de dominio manda `Docs/defintions`. En cómo se organiza el código manda `Docs/architecture.md`.
- `Docs/architecture.md` no redefine ni el stack ni el dominio: los desarrolla. Si contradice a `CLAUDE.md`, gana `CLAUDE.md`; si usa un nombre de clase o de enumeración que no está en `Docs/defintions`, el error es suyo.
- `Docs/verification.md` no introduce requisitos nuevos. Cada fila `VER-xx` cita el documento del que sale; una fila sin origen sobra.
- `Docs/domain-knowledge` es una vista, no una fuente. Si un diagrama contradice una definición, gana la definición y el diagrama se corrige.
- Nada de lo anterior sustituye al código: si el código contradice a los documentos, es un defecto de uno de los dos y hay que decidir cuál antes de seguir.

## Reglas de uso del modelo de dominio

- Los nombres de clase, atributo y valor de enumeración de `Docs/defintions` son literales. No los traduzcas, no los abrevies, no uses sinónimos.
- Toda comprobación del harness referencia su invariante por identificador (`INV-07`, no "la regla de los beats").
- Una entidad nueva se define primero en `Docs/defintions` y solo después se dibuja en `Docs/domain-knowledge`. Nunca al revés.
- Los identificadores publicados no se reutilizan ni se renumeran. Lo que deja de aplicar se marca como obsoleto, no se borra.

## Skills

El contenido real vive en `.agents/skills/` y **se versiona con el repositorio**. `.claude/skills/` solo contiene enlaces y está en `.gitignore`, porque git en Windows no guarda los enlaces como tales: los convierte en ficheros de texto con la ruta dentro. Tras clonar, se recrean con un comando:

```
node scripts/link-skills.mjs
```

| Skill | Cuándo usarla | Procedencia |
| --- | --- | --- |
| `feature-sliced-design` | Decidir dónde va un fichero del frontend, resolver un cross-import o revisar la estructura de capas. Manda sobre las dudas de colocación en `frontend/` (decisión `A-09`) | Oficial de FSD v2.1, instalada con `npx skills add`. Anotada en `skills-lock.json` |
| `verification-plan` | Escribir o revisar un `verification.md` (también llamado `validation.md` o `evaluation.md`), decidir cómo se prueba una afirmación o clasificarla en T/A/I/D/U | Propia. Construida sobre una hoja de referencia de 19 metodologías; el flujo, la plantilla y los criterios de selección son nuestros |
| `sqlite-vec` | Crear tablas `vec0`, hacer consultas KNN o serializar embeddings al implementar la persistencia | **Vendorizada y sin mantenimiento.** Su autor la borró del repositorio original; se recuperó del historial de git. Ver `.agents/skills/sqlite-vec/PROCEDENCIA.md` |

**Por qué se versiona el contenido y no basta con `skills-lock.json`.** Un lockfile fija una versión, pero no garantiza que siga existiendo: si el upstream borra el contenido, no hay nada que reinstalar. Es exactamente lo que pasó con `sqlite-vec`. La única garantía es tener el contenido en el repositorio.

**Cuidado con `sqlite-vec`.** Está abandonada y describe una librería viva, así que envejece en silencio: con el tiempo dirá cosas de `vec0` que ya no son ciertas y nada avisará. Contrástala con la documentación oficial de `asg017/sqlite-vec` antes de confiar en ella, y actualiza la fecha de revisión de su `PROCEDENCIA.md` cada vez que lo hagas.

## Todavía no existe

Estas rutas están reservadas y aparecerán aquí en cuanto se creen. Si encuentras una que no está en la tabla de arriba, añádela.

- `backend/` — servicio FastAPI.
- `frontend/` — aplicación React.
- `harness/` — ejecución de invariantes y fixtures.
- `Docs/decisions/` — decisiones de arquitectura fechadas.

## Mantenimiento de este archivo

Este archivo cambia cada vez que se añade, renombra o mueve un archivo de contexto. Al hacerlo:

1. Añade o corrige la fila en "Dónde está cada cosa" en el mismo commit que toca el archivo.
2. Describe qué contiene, no solo cómo se llama. Una fila que solo repite el nombre no ahorra ninguna lectura.
3. Si el archivo nuevo sustituye a otro, borra la fila vieja en vez de dejar las dos.
4. Mantén el total por debajo de unas 150 líneas. Si crece más, parte el contenido en un documento propio y deja aquí solo el puntero.
