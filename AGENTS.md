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

> El archivo se llama `defintions`, sin la segunda `i` y sin extensión. La ruta de la tabla es la literal del repositorio. Si se corrige el nombre, hay que actualizar esta tabla y el enlace en `CLAUDE.md` en el mismo commit.

## Orden de carga

1. `CLAUDE.md` — restricciones técnicas. Condicionan todo lo demás, así que van primero.
2. `Docs/defintions` — el modelo de dominio. Es la fuente de verdad.
3. `Docs/domain-knowledge` — solo cuando necesites ver la estructura de un vistazo o explicarla.

No cargues los tres enteros por costumbre. Para una tarea de backend suele bastar `CLAUDE.md` más la sección de invariantes de `Docs/defintions`; para una discusión de arquitectura del dominio, el árbol de `Docs/domain-knowledge`.

## Precedencia

- En lo técnico manda `CLAUDE.md`. En lo de dominio manda `Docs/defintions`.
- `Docs/domain-knowledge` es una vista, no una fuente. Si un diagrama contradice una definición, gana la definición y el diagrama se corrige.
- Nada de lo anterior sustituye al código: si el código contradice a los documentos, es un defecto de uno de los dos y hay que decidir cuál antes de seguir.

## Reglas de uso del modelo de dominio

- Los nombres de clase, atributo y valor de enumeración de `Docs/defintions` son literales. No los traduzcas, no los abrevies, no uses sinónimos.
- Toda comprobación del harness referencia su invariante por identificador (`INV-07`, no "la regla de los beats").
- Una entidad nueva se define primero en `Docs/defintions` y solo después se dibuja en `Docs/domain-knowledge`. Nunca al revés.
- Los identificadores publicados no se reutilizan ni se renumeran. Lo que deja de aplicar se marca como obsoleto, no se borra.

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
