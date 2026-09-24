# AGENTS.md

Mapa de contexto de `My_novel_story`. Léelo antes de tocar nada: dice dónde está cada cosa, en qué orden cargarla y qué manda sobre qué.

**Proyecto:** sistema agéntico que escribe novelas personalizadas para regalar —diez capítulos, a partir de una entrevista con el comprador— y el harness que las valida (`EXAMEN.md`). Nació con una novela de terror como caso base; lo específico de terror se retiró en `SPEC-26` v3.
**Rama de trabajo:** `contexto_semilla`.

## Dónde está cada cosa

| Necesitas | Archivo | Qué contiene |
| --- | --- | --- |
| Qué hay que construir y entregar | `EXAMEN.md` | El enunciado del examen: configuración, lectura (web o PDF), harness, memoria, los cuatro tipos de validadores (programáticos, semánticos, Lean 4, TLA+), evaluación con cinco briefs, observabilidad en Langfuse y guardrails; y lo que el repositorio debe incluir (novela de ejemplo en PDF, `/docs` de proceso, vídeo de demo, `.claude/`). **Manda sobre las decisiones del proyecto**: si una lo contradice, gana el enunciado y la decisión se revisa. **Un mínimo suyo no es un techo**: pedir tres roles y tener diez no es un incumplimiento. Dice qué, no cómo |
| Requisitos técnicos y stack | `CLAUDE.md` | FastAPI, React, límite de contexto de 100.000 tokens, SQLite con soporte vectorial, y el presupuesto de contexto que se deriva de ellos |
| Definiciones del dominio | `docs/definitions.md` | Referencia normativa: los seis planos (el sexto, Destinatario, desde `SPEC-25`), clases con atributos, tabla de relaciones, vocabularios controlados e invariantes `INV-01`…`INV-16` |
| Árbol y diagramas | `docs/domain-knowledge.md` | El mismo modelo en Mermaid: árbol por planos, grafo de relaciones núcleo, ciclo de vida de la escena, secuencia de generación |
| Decisiones de sistema, agentes y proceso | `docs/architecture.md` | Reparto frontend/backend, estructura por feature con `commons`, FSD en el frontend, los diez agentes del pipeline con sus habilidades e invariantes, el proceso de una escena y las decisiones `A-01`…`A-09` |
| Plan de verificación del sistema | `docs/verification.md` | Primero **qué puede salir mal**: 24 modos de fallo `MF-01`…`MF-24` sobre las rejillas de MAST, ConStory-Bench y los fallos silenciosos, **ninguno sin estado**. Después **cómo se detecta**: 54 validadores `VER-01`…`VER-55`, cada uno con su punto ciego, más los 11 asumidos y lo que se aprendió al escribir cinco. Ninguno implementado hoy |
| Briefs de evaluación | `harness/evals/` | Los briefs de prueba del enunciado y sus resultados esperados. Hoy uno de cinco, el de incoherencia temporal, sin ejecutar (`EX-06`) |
| Sesiones concurrentes | `docs/sesiones-concurrentes.md` | Cómo reservar un identificador con varias sesiones escribiendo, y qué hacer si dos colisionan |
| Documentación de proceso | `docs/proceso/` | Lo que el enunciado pide en `/docs`: spec inicial, trade-offs, explainers, diagramas (arquitectura, máquina de TLA+, esquema SQLite, validadores con su punto de ejecución), registro de iteraciones, red-team log y uso de Claude Code. **Cuenta cómo se llegó, no manda**: enlaza a lo normativo en vez de copiarlo |
| Huecos contra el enunciado | `docs/cobertura-examen.md` | Registro `EX-xx` de lo que `EXAMEN.md` exige y los documentos no recogen o contradicen (de documentación) y de lo documentado que el código no hace (de sistema), cada fila con cita de los dos lados, bloqueante o no, y el recuento por vuelta. No introduce requisitos: lo que decide cómo cerrar un hueco va en una spec |
| Skills del proyecto | `.agents/skills/` | Contenido real de las ocho skills instaladas, y en su `README.md` cuándo usar cada una y de dónde viene |
| Specs en curso | `specs/` | Un fichero por spec. **`aprobada`**: `SPEC-01` backend del harness, `SPEC-21` usos de un hecho y cronología de la fábula, `SPEC-22` frontend y contrato congelado, `SPEC-24` dónde se declara una analepsis, y las cinco que salen de `EXAMEN.md` (`docs/cobertura-examen.md`): `SPEC-27` exportar a PDF, `SPEC-28` tools de lectura de la story bible, `SPEC-29` Langfuse y qué sube y qué no, `SPEC-30` la puerta de publicación con Lean y `SPEC-31` la evaluación. **`en_revision`**: `SPEC-09` versión de `Resumen` y `SPEC-23` qué es regenerar en una obra acumulativa |
| Planes de implementación | `specs/plans/` | Un `PLAN-NN.md` por spec aprobada, con el mismo identificador y su propio estado. Hoy `PLAN-01`, el backend, en `en_revision`, `PLAN-21`, los usos y la cronología, **`aprobada`**, `PLAN-25`, el destinatario y la entrevista, **`aplicada`**, `PLAN-26`, el pipeline de la novela regalo, **`aplicada`**, y los seis que salen de `EXAMEN.md`: **`aprobada`** `PLAN-27`, `PLAN-28`, `PLAN-29` y `PLAN-31`, en `en_revision` `PLAN-30` (v2), y **`aplicada`** `PLAN-32`. Es la tercera puerta: sin plan aprobado no se escribe código |
| Specs ya aplicadas | `specs/aplicadas/` | Las que terminaron en `estado: aplicada`, con su `commit_de_aplicacion` en el frontmatter. Hoy `SPEC-03` referencias del dominio, `SPEC-04` puerta de capítulo y reclasificaciones, `SPEC-05` caducidad de las afirmaciones condicionales, `SPEC-06` estructura de `harness/` y `SPEC-07` modelo de fallo del pipeline y `SPEC-08` estados del trabajo y observabilidad `SPEC-10` huecos que la rama `main` ya sufrió `SPEC-11` observabilidad del pipeline, `SPEC-12` formas reducidas del recorte, `SPEC-13` durabilidad de los hechos, `SPEC-14` delegación en vez de API, `SPEC-15` lo que declara el plan, `SPEC-16` revelar es aprender, `SPEC-17` el conocimiento y su instante, `SPEC-18` el POV que nadie declara, `SPEC-19` lo prometido y lo entregado, `SPEC-20` qué se puede editar a mano `SPEC-25` el destinatario, la entrevista y las palabras vetadas, que abre el examen de la novela para regalar y lleva en su anexo la plantilla de la ficha, y `SPEC-26` el pipeline de la novela regalo (planificador con revisor, editor, validadores de personalización y los dos hooks) y `SPEC-32` la dedicatoria en `Obra` y la extensión preguntada. **`SPEC-02`, vocabularios, no está**: se aplicó y su fichero se retiró antes de existir esta carpeta, y no se puede recuperar porque nunca llegó a commitearse. Es la única excepción y no se repite |
| Código del backend | `backend/` | Servicio FastAPI con `app/commons/` y `app/features/`. Features: `escaleta`, `generacion`, `verificacion`, `consolidacion`, `contexto`, `orquestacion`, `auditoria`, `recuperacion`, `edicion`, `brief`, `cronologia` (dónde se usa cada hecho y la cronología de la fábula: `SPEC-21`), `entrevista` (la ficha del destinatario por turnos y el texto libre: `SPEC-25`) y `politica` (las palabras vetadas en tres niveles: `SPEC-25`); y en `auditoria/` la puerta de publicación con Lean (`SPEC-30`), que necesita `lake`. Lo que comparten las dos últimas —el detector de vetadas y el audit log— está en `app/commons/politica/`, y los modelos de la ficha en `app/commons/dominio/destinatario.py`. La CLI de la entrevista es `backend/entrevista_cli.py`. `planificacion` lleva de la ficha a un plan aprobado (`SPEC-26`); los dos hooks de Claude Code están en `backend/hooks/`, y la novela regalo con agentes reales se lanza con `backend/novela_regalo.py`, que gasta dinero. Las dependencias en `backend/requirements.txt`; las pruebas con `python -m pytest app -q` desde `backend/` |
| Revisiones de documentos | `docs/revisiones/` | Un `REV-NN.md` por documento revisado. Evalúa un documento **existente**; una spec dice qué va a cambiar. Por eso cuelga de `docs/` y no de `specs/` |
| Referencias externas | `docs/referencias.md` | **Consulta, no normativo.** Material de clase sobre métodos de Spec-Driven Development (Spec Kit, OpenSpec, MUSUBI, EasySpecs…) y lenguajes de especificación formal (TLA+, P, Dafny, Alloy…), más una lectura propia de qué se parece a lo que ya hacemos y qué hueco señala. No está en la cadena de precedencia y ninguna `INV-xx`, `VER-xx` ni spec puede citarlo como origen |

> Las rutas de esta tabla son literales del repositorio: se copian tal cual, con su extensión. Si se renombra un documento, hay que actualizar esta tabla, el enlace en `CLAUDE.md` y todas las referencias en el mismo commit. Pasó lo contrario al renombrar `defintions` → `definitions.md` y `SRS.md` → `SPEC - Backend.md`: quedaron setenta referencias rotas.

## Orden de carga

1. `EXAMEN.md` — qué hay que construir y entregar. Va primero porque es lo único que puede obligar a revisar una decisión del proyecto; basta con la sección que toque la tarea.
2. `CLAUDE.md` — restricciones técnicas. Condicionan todo lo demás del proyecto.
3. `docs/definitions.md` — el modelo de dominio. Es la fuente de verdad del dominio.
4. `docs/architecture.md` — cómo se organiza el código y quién habla con quién. Antes de escribir nada en `backend/` o `frontend/`.
5. `docs/domain-knowledge.md` — solo cuando necesites ver la estructura de un vistazo o explicarla.
6. `docs/verification.md` — cuando vayas a escribir una prueba o a cerrar una fila `VER-xx`.

No cargues los seis enteros por costumbre. Para una tarea de backend suele bastar `CLAUDE.md`, la sección de invariantes de `docs/definitions.md` y la de backend de `docs/architecture.md`; para una discusión de arquitectura del dominio, el árbol de `docs/domain-knowledge.md`.

## Precedencia

- **Por encima de todo, `EXAMEN.md` en qué se construye y se entrega.** Su cabecera lo declara: si algo del enunciado contradice a una decisión del proyecto —de `CLAUDE.md`, de `docs/`, de una spec o de un plan—, gana el enunciado y la decisión se revisa. Revisarla sigue el proceso de siempre: una spec que la cambie, aprobada antes del código. Lo que el enunciado no menciona lo gobiernan las reglas de abajo.
- En lo técnico manda `CLAUDE.md`. En lo de dominio manda `docs/definitions.md`. En cómo se organiza el código manda `docs/architecture.md`.
- `docs/architecture.md` no redefine ni el stack ni el dominio: los desarrolla. Si contradice a `CLAUDE.md`, gana `CLAUDE.md`; si usa un nombre de clase o de enumeración que no está en `docs/definitions.md`, el error es suyo.
- `docs/verification.md` no introduce requisitos nuevos. Cada fila `VER-xx` cita el documento del que sale; una fila sin origen sobra.
- `docs/domain-knowledge.md` es una vista, no una fuente. Si un diagrama contradice una definición, gana la definición y el diagrama se corrige.
- Nada de lo anterior sustituye al código: si el código contradice a los documentos, es un defecto de uno de los dos y hay que decidir cuál antes de seguir.

## Reglas de uso del modelo de dominio

- Los nombres de clase, atributo y valor de enumeración de `docs/definitions.md` son literales. No los traduzcas, no los abrevies, no uses sinónimos.
- Toda comprobación del harness referencia su invariante por identificador (`INV-07`, no "la regla de los beats").
- Una entidad nueva se define primero en `docs/definitions.md` y solo después se dibuja en `docs/domain-knowledge.md`. Nunca al revés.
- Los identificadores publicados no se reutilizan ni se renumeran. Lo que deja de aplicar se marca como obsoleto, no se borra.

## Proceso de trabajo

Tres puertas en cadena. Cada una se abre solo con la anterior cerrada, y ninguna se salta porque el cambio parezca pequeño.

```
docs/  →  spec aprobada  →  plan aprobado  →  código (TDD)  →  spec y docs/ al día
```

**Qué cuenta como aprobación.** El frontmatter del propio fichero: `id`, `estado` (`borrador | en_revision | aprobada | aplicada | obsoleta`), `aprobada_por` y `fecha_aprobacion`. Los planes llevan el mismo.

**Una spec aplicada se mueve, no se borra.** Cuando su contenido ya está en `docs/`, pasa a `estado: aplicada`, se anota `fecha_aplicacion` y `commit_de_aplicacion` —que necesita un commit propio, porque el hash no existe hasta después— y el fichero se mueve con `git mv` a `specs/aplicadas/`. Así `specs/` contiene lo que está en curso y nada más, y sigue siendo posible leer por qué se decidió cada cosa. Las referencias son siempre por identificador (`SPEC-03`), nunca por ruta, así que mover el fichero no rompe nada.

Sin `estado: aprobada` no se pasa, aunque el documento esté escrito entero y aunque se haya hablado. "Lo comentamos ayer" no es una aprobación; el campo sí. `SPEC-NN` es un identificador estable: no se reutiliza ni se renumera, y lo que deja de aplicar pasa a `obsoleta` en vez de borrarse. Los identificadores internos de una spec (`RF-xx`, `O-x`, `M-x`, `P-x`) tampoco se renumeran al reescribirla.

### 1. Actualizar `docs/`

`docs/` es lo normativo permanente. Hay dos clases de cambio y no se tratan igual:

- **Cambio documental** —corregir un error, aclarar una frase, añadir un diagrama de algo ya decidido—: se hace directamente, sin spec.
- **Cambio que decide algo nuevo** —una clase, una invariante, una decisión de arquitectura, un umbral—: **necesita spec aprobada primero**. El documento se actualiza después, no antes.

Se mantienen las reglas que ya existen: una entidad se define primero en `docs/definitions.md` y solo después se dibuja en `docs/domain-knowledge.md`; un cambio de atributo obligatorio lleva su migración en el mismo commit; los identificadores publicados no se renumeran. Y este archivo se actualiza en el mismo commit que mueve un archivo de contexto.

### 2. Crear o actualizar una spec

Un fichero propio en `specs/`, con su `SPEC-NN` en el frontmatter. Responde a tres cosas y solo a tres: **qué problema resuelve**, **qué tiene que ser verdad al terminar** y **qué queda explícitamente fuera**.

- **Antes de escribirla se pregunta.** Una spec con huecos rellenados por suposición es peor que no tener spec, porque parece acordada. Las dudas se preguntan al escribirla, no se descubren implementando.
- **Una spec no dice cómo se hace.** Nada de ficheros, funciones ni orden de tareas: eso es el plan.
- **Cita lo que la gobierna** por identificador: `INV-xx`, `A-xx`, `VER-xx`.
- Termina en `estado: aprobada`, o no hay nada más que hacer con ella.

### 3. Plan de implementación

Vive en `specs/plans/PLAN-NN.md`, con el mismo identificador que su spec y su propio estado. **No se confunde con `docs/revisiones/REV-NN.md`**, que revisa el documento antes de aprobarlo: el plan dice cómo se construye el código y nace después de la aprobación.

- **No se crea un plan si su spec no está aprobada.** Un plan sin spec aprobada está resolviendo un problema que nadie ha acordado.
- Dice qué ficheros se tocan, en qué orden, **qué prueba cubre cada paso** y qué filas `VER-xx` de `docs/verification.md` cierra.
- Cada paso debe dejar el repositorio funcionando. Un paso que solo tiene sentido con el siguiente son un paso.
- También se aprueba, y es la tercera puerta.

### 4. Crear o modificar código

- **No se escribe código si el plan no está aprobado.** Ni un fichero de andamiaje.
- **TDD, en este orden:** primero la prueba que falla, después el código mínimo que la pasa, después el refactor. Ningún código de producción nace sin una prueba que haya fallado antes. Esto es la misma exigencia que el proyecto ya tiene para las invariantes: una regla que nunca ha fallado en las pruebas no está verificada, solo declarada.
- **Al terminar, en el mismo commit:** la spec al día, `docs/` al día y la fila `VER-xx` actualizada si se ha cerrado alguna.

### Cuando el código descubre que la spec estaba mal

Pasa, y es sano que pase. Lo que no vale es seguir.

Se para, se corrige la spec, se vuelve a aprobar, y si el plan cambia de forma, se vuelve a aprobar también. El código nunca avanza por delante de la spec: en cuanto lo hace, la spec deja de gobernar lo que se va a hacer y pasa a describir mal lo que ya se hizo. A las tres semanas es ficción y nadie la lee.

## Varias sesiones a la vez

**Una carpeta por sesión, con `git worktree`.** Dos sesiones en el mismo directorio se pisan: cambian de rama bajo los pies de la otra y se barren los ficheros mutuamente. Cada worktree tiene su carpeta y su rama, y comparten el mismo `.git`.

```
git worktree add -b <rama-nueva> ../My_novel_story-<nombre> <rama-de-partida>
git worktree list
git worktree remove ../My_novel_story-<nombre>
```

Una rama solo puede estar checkouteada en **un** worktree a la vez. Lo ignorado —`.env`, `*.db`, `salida/`— no viaja a un worktree nuevo y hay que copiarlo a mano; las skills sí, porque `.agents/skills/` está versionado.

**Nunca `git add -A` ni `git commit -a`: se añade por ruta.** Un barrido se lleva lo que otra sesión dejó a medias y lo mete en un commit que no habla de ello; ya pasó, y el fichero acabó dentro de un commit sobre otra cosa. **Un worktree separa carpetas, no costumbres**: con carpetas separadas el barrido sigue arrastrando lo que uno mismo tenía sin terminar.

**Y antes de abrir una spec, mirar los identificadores que hay.** Dos sesiones trabajando a la vez eligen el mismo `SPEC-NN` sin enterarse: pasó dos veces seguidas. Si ya está cogido, se renumera el propio —nunca se reutiliza— y conserva el número la spec que ya esté `aprobada`.

**Con varias sesiones escribiendo, mirar el último identificador no basta**: hay que reservarlo antes de escribir o volver a comprobarlo justo antes del commit, y si dos colisionan conserva el número el primero publicado según git. El procedimiento completo, con su porqué, está en `docs/sesiones-concurrentes.md`.

## Skills

El contenido real vive en `.agents/skills/`, se versiona con el repositorio y Claude Code lo lee directamente. **Qué skill usar y cuándo, su procedencia y cómo se actualizan** —ninguna se actualiza sola, y `sqlite-vec` está abandonada y hay que contrastarla antes de fiarse— está en `.agents/skills/README.md`.

## Todavía no existe

Estas rutas están reservadas y aparecerán aquí en cuanto se creen. Si encuentras una que no está en la tabla de arriba, añádela.

- `frontend/` — aplicación React.
- `harness/documentos/` y `harness/adversarial/` — dos de las tres carpetas que declara `docs/architecture.md` § "El harness". La tercera, `harness/evals/`, ya existe y tiene su fila arriba. Se escribieron cinco validadores a modo de prueba y se retiraron; lo que enseñaron está en `docs/verification.md` § "Lo que se aprendió al implementar".
- `docs/decisions/` — decisiones de arquitectura fechadas.
- Lo que `EXAMEN.md` exige que el repositorio incluya, y no existe todavía (§ "Los repositorios deben incluir también"): `README.md` en la raíz con un brief de ejemplo reproducible, `.env.example`, `ejemplos/novela-ejemplo.pdf`, `presentacion/` con el vídeo de demo, `.claude/commands/` y la memoria dentro de `.claude/`, y el fichero de configuración MCP con un servidor de inspección de browser.

## Mantenimiento de este archivo

Este archivo cambia cada vez que se añade, renombra o mueve un archivo de contexto. Al hacerlo:

1. Añade o corrige la fila en "Dónde está cada cosa" en el mismo commit que toca el archivo.
2. Describe qué contiene, no solo cómo se llama. Una fila que solo repite el nombre no ahorra ninguna lectura.
3. Si el archivo nuevo sustituye a otro, borra la fila vieja en vez de dejar las dos.
4. Mantén el total por debajo de unas 150 líneas. Si crece más, parte el contenido en un documento propio y deja aquí solo el puntero.
