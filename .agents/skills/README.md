# Skills del proyecto

Contenido real de las skills instaladas. Se movió aquí desde `AGENTS.md`, que lo apunta, para mantener aquel archivo por debajo de su tope de líneas.

El contenido real vive en `.agents/skills/` y **se versiona con el repositorio**. Claude Code lee esa carpeta directamente, así que tras clonar no hay que hacer nada: las skills están disponibles. `.claude/skills/` sigue en `.gitignore` porque `npx skills add` crea allí enlaces que git en Windows no guarda como tales, y no hacen falta.

**Ninguna skill se actualiza sola, y no hay lockfile.** Las dos de upstream se actualizan a mano: se reinstalan con `npx skills add <repo> --skill <nombre>` y se revisa el diff antes de aceptarlo. Su origen y el hash con el que entraron están en la tabla de abajo, que es donde hay que mirar para saber qué se instaló y desde dónde.

| Skill | Cuándo usarla | Procedencia |
| --- | --- | --- |
| `spec-and-plan` | Empezar cualquier cambio que decida algo nuevo. Ejecuta las puertas de "Proceso de trabajo" y comprueba si están abiertas | Propia |
| `fastapi` | Endpoints, dependencias, modelos Pydantic, streaming: los idiomas del framework | Oficial, de `github.com/fastapi/fastapi`, ruta `.agents/skills/fastapi/`. Instalada 2026-09-21, hash `187b2e06` |
| `coherencia-docs` | Revisar la coherencia entre los documentos de contexto: citas rotas por identificador, contradicciones, deriva de literales y afirmaciones que caducan en silencio. Antes de un merge que toque `docs/` | Propia. Escrita sobre un borrador del usuario y adaptada al repositorio; ver su § "Procedencia" |
| `backend-feature` | Decidir dónde va un fichero de `backend/` y de qué puede depender. La contraparte de FSD en el servidor (`A-01`, `A-02`) | Propia |
| `feature-sliced-design` | Decidir dónde va un fichero del frontend, resolver un cross-import o revisar la estructura de capas (`A-09`) | Oficial de FSD v2.1, de `github.com/feature-sliced/skills`. Instalada 2026-09-21, hash `e2b86275` |
| `harness-invariantes` | Implementar o revisar una comprobación `INV-xx`: regla o juez, severidad, hallazgo y caso negativo | Propia |
| `verification-plan` | Escribir o revisar un `verification.md` (también llamado `validation.md` o `evaluation.md`), decidir cómo se prueba una afirmación o clasificarla en T/A/I/D/U | Propia. Construida sobre una hoja de referencia de 19 metodologías; el flujo, la plantilla y los criterios de selección son nuestros |
| `novela-regalo` | **La del pipeline.** Lanzar una generación de la novela regalo e inspeccionar lo que hizo de verdad —base, hooks, tools y Langfuse—, sin fiarse del código de salida. La usa el comando `/inspeccionar-novela` | Propia, escrita el 2026-09-24 con lo que enseñó la primera ejecución real aceptada (`F-76`, `F-77`) |
| `sqlite-vec` | Crear tablas `vec0`, hacer consultas KNN o serializar embeddings al implementar la persistencia | **Vendorizada y sin mantenimiento.** Su autor la borró del repositorio original; se recuperó del historial de git. Ver `.agents/skills/sqlite-vec/PROCEDENCIA.md` |

**Por qué se versiona el contenido y no basta con `skills-lock.json`.** Un lockfile fija una versión, pero no garantiza que siga existiendo: si el upstream borra el contenido, no hay nada que reinstalar. Es exactamente lo que pasó con `sqlite-vec`. La única garantía es tener el contenido en el repositorio.

**Cuidado con `sqlite-vec`.** Está abandonada y describe una librería viva, así que envejece en silencio: con el tiempo dirá cosas de `vec0` que ya no son ciertas y nada avisará. Contrástala con la documentación oficial de `asg017/sqlite-vec` antes de confiar en ella, y actualiza la fecha de revisión de su `PROCEDENCIA.md` cada vez que lo hagas.
