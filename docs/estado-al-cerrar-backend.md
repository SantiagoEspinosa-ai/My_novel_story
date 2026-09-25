# Estado al cerrar

Foto del repositorio el **2026-09-25**, hacia las 02:30 UTC. Todo lo que hay aquí se leyó ese
día con `git` o se abrió en un navegador, y cada apartado dice cómo. **Las ramas seguían
moviéndose mientras se escribía**: la fusión de `frontend-regalo` en `examen-cierre` ocurrió a
mitad de la redacción. Antes de fiarse de una fila, se vuelve a comprobar con las órdenes del
final de cada apartado.

Este documento **no es normativo**: cuenta dónde se quedó cada cosa, no decide nada.

---

## 1. Dónde se quedó cada rama

### Lo primero: casi nada de esto está en GitHub

El remoto (`origin`, `github.com/SantiagoEspinosa-ai/My_novel_story`) solo tiene tres ramas, y
ninguna lleva el trabajo de los últimos días (leído con `git ls-remote --heads origin`):

| Rama en GitHub | Commit | Qué es |
| --- | --- | --- |
| `main` | `fa79437` | La línea antigua del proyecto (ver `main` abajo) |
| `contexto_semilla` | `3b62d8f` | El contexto inicial |
| `ejecucion-spec-01` | `3b62d8f` | El mismo commit que `contexto_semilla` |

La rama local `ejecucion-spec-01` va **265 commits por delante** de su copia en GitHub, y
`examen-cierre`, que es donde está todo integrado, **no existe en GitHub**. Si hoy se clona el
repositorio en otra máquina, se obtiene `3b62d8f`: ni backend de la novela regalo, ni web, ni
evaluación. **Antes del apartado 2 hay que subir `examen-cierre`** (ver "Qué falta por
fusionar"). No se ha subido nada: publicar en GitHub es una decisión del autor.

### La rama que manda: `examen-cierre`

**`examen-cierre` es la rama integrada**, en la carpeta `My_novel_story-examen`, con último
commit `bb165cf` («Fusionar frontend-regalo: PLAN-35, el techo a 121, docs corregidos, F-201 y
F-202») cuando se escribió este apartado; lo que se sumó después está en el apartado 4, y la cabeza se lee con `git log -1 examen-cierre`. Lleva dentro todas las ramas de la tabla siguiente, comprobado una por una con
`git merge-base --is-ancestor <rama> examen-cierre`:

| Rama | Carpeta (worktree) | Último commit | Qué trajo |
| --- | --- | --- | --- |
| `frontend-regalo` | `My_novel_story-frontend` | `2d90112` | La web de la novela regalo (`PLAN-33`, `PLAN-35`), `F-201` y `F-202`, `SPEC-31` v6 (techo de 121 USD) y el cierre del tuning en los documentos |
| `ejecucion-spec-01` | `My_novel_story` (la carpeta principal) | `b503226` | El backend hasta `PLAN-29` E11 (Langfuse) |
| `plan22-lectura` | `My_novel_story-plan22` | `11dfc43` | La lectura web (`PLAN-22`) |
| `plan22-peticion` | `My_novel_story-plan22b` | `94f330a` | La petición de cambio en la web (`PLAN-22` E18) |
| `plan23-regeneracion` | `My_novel_story-plan23` | `df40a79` | Regenerar, parte A (`PLAN-23`) |
| `plan23-parte-b` | `My_novel_story-plan23b` | `354f35d` | Regenerar, parte B (`PLAN-23`) |
| `plan31-evaluacion` | `My_novel_story-plan31` | `1256917` | La evaluación con los cinco briefs (`PLAN-31`) |
| `tla-backend` | `My_novel_story-tla` | `fa4507f` | El modelo TLA+ del backend (`EX-07`) |
| `specs-frontend` | `My_novel_story-specs` | `c80d393` | Specs del frontend |
| `verificacion-formal` | `My_novel_story-verificacion` | `15863fd` | Verificación formal y medidas |
| `contexto_semilla` | `My_novel_story-semilla` | `3b62d8f` | El contexto inicial |
| — (sin rama) | `My_novel_story-r1` | `89425c4` | La carpeta desde la que se lanzaron las generaciones reales |

Después de la fusión, `examen-cierre` sumó `fa0d588` («F-203: las fichas leen los capítulos de
la versión vigente»), que **no está en `frontend-regalo`**. La web que yo he tenido levantada
salía de `frontend-regalo`, así que **el arreglo de `F-203` no lo he visto en el navegador**. *(Añadido por la sesión de `examen-cierre`: lo comprobé después en la web servida desde `examen-cierre`; ver apartado 4.)*

### Lo que no está fusionado

| Rama | Carpeta | Commits propios | Qué tiene | Por qué no está |
| --- | --- | --- | --- | --- |
| `nombre-en-el-prompt` | `My_novel_story-nombre` | 1: `5d7a73b` | `F-152`: el Escritor sabe cuántas veces puede nombrar al destinatario | **Separada a propósito**: su commit dice que no se fusiona hasta que termine la pasada «después» de `T1`, porque el autor la quería en otra pasada. **Esa pasada no se va a hacer**: el tuning se cerró sin completar. Fusionarla da **un conflicto en `docs/verification.md`** (comprobado con `git merge-tree`) |
| `myfactory` | `My_novel_story-myfactory` | 3: `117eb79`, `fb5805e`, `817ce49` | Las skills pasan a `myFactory/` con su procedencia, `.claude/skills/` se versiona, y un informe sobre repositorios gigantes | Sale de `ejecucion-spec-01` y va **167 commits por detrás** de `examen-cierre`. Fusionarla da **un conflicto en `.claude/skills/README.md`** y cambia cómo se guardan las skills, que `AGENTS.md` describe de otra manera |
| `main` | `My_novel_story-main` | 45 | La primera versión del proyecto: `panel.html`, `archivo/`, `EJECUCION.md` y los modelos de OpenRouter | **No comparte historia** con las demás ramas (`git merge-base main examen-cierre` no encuentra ningún antecesor común). Es otra línea de trabajo, no una rama pendiente de fusionar. En local lleva 5 commits sin subir a GitHub |

### Lo que hay sin commitear

- **En la carpeta principal** (`My_novel_story`, rama `ejecucion-spec-01`) hay cambios sin
  commitear en cinco ficheros: `.gitignore`, `backend/app/commons/observabilidad/observacion.py`,
  `backend/app/features/orquestacion/novela.py`, `observar.py` y su prueba. Son de otra sesión
  y no están en ningún commit ni en ninguna rama.
- **En `My_novel_story-examen`** hay 13 capturas `.png` sin trackear (`cap01.png`…`cap10.png`,
  `fichas.png`, `indice.png`, `portada.png`).

### Qué falta por fusionar

- **Para que la web y el backend estén en una sola rama no falta nada.** `examen-cierre` ya lo
  tiene todo.
- **Falta subirla a GitHub**, que es lo que permite el apartado 2. La orden sería esta (**no se
  ha ejecutado**):
  ```
  git push origin examen-cierre
  ```
- **Tres decisiones del autor**: si `nombre-en-el-prompt` entra ahora que la pasada que la
  esperaba no existe (con su conflicto), si `myfactory` entra (con el suyo), y qué hacer con los
  cambios sin commitear de la carpeta principal.

**Para comprobar esta sección:**
```
git worktree list
git ls-remote --heads origin
git merge-base --is-ancestor <rama> examen-cierre && echo dentro
git rev-list --count examen-cierre..<rama>
```

---

## 2. Cómo levantar todo en local desde cero

Suponiendo que `examen-cierre` ya está en GitHub (apartado 1). Sin eso, el clon no tiene nada de
lo que sigue.

### Qué instalar

| Herramienta | Versión probada | Para qué | ¿Obligatoria? |
| --- | --- | --- | --- |
| Git | — | Clonar | Sí |
| Python | 3.12.10 | El backend | Sí |
| Node.js y npm | 24.19.0 y 11.17.0 | El frontend | Sí |
| Edge o Chrome | — | Abrir la web | Sí |
| Lean 4 con `lake` (4.34.0) | — | La puerta de publicación (`SPEC-30`): sin `lake`, una versión nueva no se publica y el informe lo dice | Solo para generar |
| Claude Code (`claude`) con la sesión iniciada | — | Todo lo que llama al modelo: cada turno de la entrevista, escribir la novela y confirmar un cambio. **Gasta dinero** | Solo para generar |

**Para leer lo que ya está escrito no hace falta ni `lake` ni `claude`.** Todo lo que se ve en
el apartado 3 se abrió sin ninguno de los dos.

### Clonar e instalar dependencias

```powershell
git clone https://github.com/SantiagoEspinosa-ai/My_novel_story.git
cd My_novel_story
git checkout examen-cierre

cd backend
pip install -r requirements.txt
cd ..\frontend
npm ci
```

`npm ci` instala exactamente lo de `frontend/package-lock.json`, que sí está versionado.

### Lo que no viaja por git y hay que copiar a mano

Sale de `.gitignore`: las bases (`*.db`, `*.sqlite`), los secretos (`.env`, `.env.*`), `salida/`,
`node_modules/`, `.claude/settings.local.json` y `.claude/skills/`. Las skills de verdad sí
viajan, porque están en `.agents/skills/`. `backend/config/sistema.json`, `brief.json` y
`vetadas.json` también viajan.

| Fichero | Dónde está hoy | Dónde va en la otra máquina | Qué pasa si no se copia |
| --- | --- | --- | --- |
| **La base de la demo**, `ejemplo-web.db` (876.544 bytes) | `My_novel_story-examen\backend\ejemplo-web.db` | `backend\ejemplo-web.db` | No se ve «La ruta de Pimienta» ni su versión 2. Es **la única base con una versión nacida de una petición**. Se copia con los servidores parados. `My_novel_story-frontend\backend\ejemplo-web-frontend.db` es una copia de ella |
| `backend/.env` | `My_novel_story-examen\backend\.env` | `backend\.env` | Nada se rompe: sin claves, la generación funciona igual, no envía nada a Langfuse y lo dice. La plantilla es `backend/.env.example`. **Lleva claves: no se commitea ni se pega en ningún chat** |
| `ejemplo.db` (270.336 bytes) | `My_novel_story-examen\backend\ejemplo.db` | — | Es una base antigua de la misma novela, `obra-ejemplo`, sin la tabla de versiones. Para la web no hace falta |

**Si no se puede copiar la base de la demo**, hay otra con datos inventados que se crea sin
modelo y sin gastar (la creé el 2026-09-25 para comprobar la entrevista):
```powershell
cd backend
python -X utf8 semilla_regalo.py regalo-semilla.db
```
Trae una obra publicada, una a medio escribir, una entrevista a medias y otra cerrada. **No
tiene ninguna versión 2**.

### Arrancar

Son dos terminales de PowerShell, desde la raíz del clon. Son los puertos con los que lo
comprobé (8010 y 5183).

**Terminal 1, el backend:**
```powershell
cd backend
$env:HARNESS_BASE = "$PWD\ejemplo-web.db"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

**Terminal 2, el frontend:**
```powershell
cd frontend
$env:HARNESS_API = "http://127.0.0.1:8010"
npx vite --port 5183 --strictPort --host 127.0.0.1
```

Y se abre **http://127.0.0.1:5183/**.

- `HARNESS_BASE` dice qué base se sirve. Sin ella, el backend usa `ruta_de_la_base` de
  `backend/config/sistema.json`, que es `obra.db`. Eso no lo he probado.
- `HARNESS_API` dice a dónde manda Vite las llamadas. Sin ella, van a `http://127.0.0.1:8000`
  (`frontend/vite.config.ts`).

**Las pruebas**, para ver que el clon está sano:
```powershell
cd backend;  python -m pytest app -q
cd frontend; npm test
```

---

## 3. Qué falta de la web

**Lo que se puede abrir hoy, no lo que promete el plan.** Lo abrí el 2026-09-25 con Edge sin
cabeza movido por Playwright, en dos montajes: la base de la demo (5183 → 8010) y la base
inventada de la semilla (5184 → 8011), las dos servidas desde `frontend-regalo`. **No pulsé
nada que gaste**: ni «Responder», ni «Generar novela», ni «Sí, escribir la novela», ni
«Confirmar el cambio».

### Las cinco pantallas que preguntas

| Pantalla | ¿Existe? | Cómo se llega | Qué vi |
| --- | --- | --- | --- |
| **La entrevista con el cuaderno** | **No se construyó.** El cuaderno no está en ninguna rama: busqué «cuaderno» y «Xime» en `frontend/src` de las 15 ramas y solo aparece un comentario de un color | — | Lo que sí hay es **la entrevista de `SPEC-33`**, como conversación simple (abajo) |
| **El cuaderno completo** | **No se construyó**, por lo mismo | — | — |
| **Pedir un cambio** | **Sí** (`PLAN-35` E5) | Índice → un capítulo **de la versión vigente** → botón **«Pedir un cambio»** debajo de cada escena. Si antes se selecciona texto, sale como cita. En las versiones que no son la vigente no aparece | Funciona. Ofrece los tres hechos de la escena y a las dos personas presentes. **Por «Un nombre», la demo lo rechaza**: *«no consta quien es el destinatario -no hay ficha de la obra-»*, porque esa base no tiene entrevista. Por «Un hecho» sí funciona |
| **Qué se reescribe** | **Sí** (`PLAN-35` E6) | Dentro del mismo panel, al pulsar **«Ver qué capítulos se tocarían»**. No es una página aparte | Sale la balda con los diez lomos. Con un hecho del capítulo 1 se marcaron los diez como «se reescribe», junto con la promesa, su punto ciego y «Confirmar el cambio», que no pulsé |
| **La versión nueva** | **Sí** (`PLAN-35` E7) | Índice → selector **«Versión 3 (vigente)»**, que enlaza a la Versión 2 y a la 1 → un capítulo marcado como cambiado | La versión 2 marca sus capítulos cambiados. Al abrir uno sale el aviso «por tu cambio» con las palabras de la petición |

### Por qué solo veías cinco pantallas

- **Tres de las cinco no son páginas propias.** «Pedir un cambio» y «Qué se reescribe» viven
  dentro del capítulo, y «la versión nueva» se abre desde el selector del índice. Si no se
  entra en un capítulo de la versión vigente ni se abre el selector, no aparecen.
- **La entrevista y el cuaderno de `SPEC-35` no se llegaron a hacer.** `PLAN-35` los dejó para
  una segunda tanda que espera al plan de `SPEC-34`. `SPEC-34` está aprobada, pero **no hay
  `PLAN-34` en ninguna rama** (comprobado en las 15). Sin plan aprobado no se escribe código.
- **La entrevista que sí existe no se ve con la base de la demo**, porque esa base no tiene
  ninguna entrevista. Con la base de la semilla aparece: en la estantería, «Seguir la
  entrevista» lleva a `/entrevistas/<id>`. Ahí se ven las preguntas y las respuestas, y en su
  turno los avisos, las contradicciones y lo que está pendiente, más «Responder» y «Cerrar la
  ficha». Con la entrevista cerrada, se ve la confirmación con el coste de la última generación,
  la referencia de 16,89 USD y lo gastado contra el techo de 50 USD, marcado como mínimo.
  **Contestar llama al modelo y gasta.**

### Lo demás que se abre hoy

- **La estantería.** Con la demo, «La ruta de Pimienta» con «Leer» y «Generar novela». Con la
  semilla, además «Ver cómo se escribe», «Seguir la entrevista» y «Escribir la novela».
- **La portada**, con título, dedicatoria y «Descargar en PDF», que descarga.
- **El índice** de la versión vigente, la 3, con sus diez capítulos.
- **El capítulo**, con el texto de sus escenas.
- **Las fichas**, con enlaces que llevan a su capítulo.
- **La página de la generación** (`/obras/<id>/generacion`) existe y la estantería de la
  semilla enlaza a ella, pero **hoy no la abrí**.

### Defectos que se ven

- **`F-203`**: con varias versiones, las fichas repetían cada capítulo una vez por versión. **Arreglado en `examen-cierre` (`fa0d588`) y comprobado el 2026-09-25 en la web servida desde `examen-cierre`** (8000/5173): ninguna ficha repite un capítulo y todas enlazan los de la versión 3 (apartado 4).
- **En la estantería de la demo, el destinatario sale «sin dato»**, porque la base no tiene
  entrevista. No es un fallo de la web: el dato no está.
- **La cabecera sigue diciendo «Novela regalo · lectura»**
  (`frontend/src/shared/ui/cabecera/Cabecera.tsx`).
- **Sin versión para móvil**: se descartó en `SPEC-35`.

---

# La parte del backend y la evaluación (sesión de `examen-cierre`)

Escrito el **2026-09-25** por la sesión que integró `examen-cierre`, lanzó las generaciones
reales y la demo de regeneración. Mismo criterio que arriba: **lo que existe hoy**, leído con
`git`, con la base o en el navegador ese día. Cada afirmación dice de dónde sale.

## 4. Dónde se quedó mi parte

### Ramas

- **`examen-cierre`** (carpeta `My_novel_story-examen`) es donde está todo lo mío. Encima de lo
  que cuenta el apartado 1 lleva, en este orden: `F-203` (`fa0d588`), su fila cerrada
  (`44b5594`), `resultados.md` regenerado (`4f2fae6`), la fusión del documento de cierre de
  `frontend-regalo` (`bd0570b`) y el commit que añade este texto. **El hash de la cabeza se lee
  con `git log -1 examen-cierre`**: no lo escribo aquí porque este mismo commit lo cambia.
- **`nombre-en-el-prompt`** (carpeta `My_novel_story-nombre`, 1 commit: `5d7a73b`, `F-152`):
  **sin fusionar**. El 2026-09-25 empecé a fusionarla, dio conflicto en `docs/verification.md`
  y paré porque el autor lo pidió; la fusión **se deshizo** (`git merge --abort`) y
  `examen-cierre` quedó como estaba. Que entre es decisión del autor (apartado 1).
- **`My_novel_story-r1`** no es una rama: es un worktree sin rama en `89425c4`. **No se borra**:
  guarda el libro de gasto (`backend/evaluacion.db`) y la base de cada ejecución real
  (`backend/evaluacion-<ejecucion>.db`: `R1` a `R5` y la antes-2). Git no los lleva.
- **Nada está en GitHub** (apartado 1).

### Servidores en marcha al cerrar

| Puertos | Desde | Base | Quién |
| --- | --- | --- | --- |
| 8000 (API) y 5173 (web) | `My_novel_story-examen`, código de `examen-cierre` | `backend/ejemplo-web.db` | Esta sesión |
| 8010 y 5183 | `My_novel_story-frontend` | una copia de la base de la demo | La sesión del frontend |

Los de 8000/5173 los arranqué con las órdenes del apartado 6 y los recorrí en Edge sin cabeza:
estantería, portada, índice, capítulo, fichas, y el índice y el capítulo 4 de las versiones 1, 2
y 3. **Sin errores de consola, sin respuestas 4xx ni 5xx y sin desbordar a 390 px.** El capítulo
4 dice «Tino» 10 veces en la versión 1 y «Anselmo» 6 en la 3. La portada descarga el PDF
(`/pdf/disponible` → `true`; `/pdf` → 200, 124.926 bytes). Los servidores mueren al cerrar la
sesión; se vuelven a levantar con el apartado 6.

### El gasto, corregido

Lo medido en esta fase suma **77,2132 USD**: 47,1354 del libro con `R1`–`R5`, 8,7712 de la
antes-2, 19,5379 de la demo B4, 0,6959 de la inspección de `INV-30` y 1,0728 de la de `PLAN-22`
E18. **Es un suelo**: solo lo medido. **Corrige dos cifras mías anteriores, las dos erróneas**:
«unos 76» (contaba dos veces 7,66 USD de la demo) y «unos 85». El techo del libro se bajó a 121
con aquel 76; con la cifra buena serían 128,69, así que 121 se equivoca hacia lo prudente.

## 5. El enunciado, punto por punto (a 2026-09-25)

Estados: **Hecho** (existe y se ejerció con el modelo real), **A medias** (una parte existe y
otra no, y se dice cuál), **Abierto declarado** (no existe, con su motivo escrito), **No existe**.

### §1 Configuración

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Entrevistador que recoge los datos y las palabras vetadas | **A medias** | Existe y se ejerció en real (`R2`, `R4`). Pero en `R4` las sesiones delegadas guardaron al destinatario como `[NOMBRE_ANONIMIZADO]` y no hubo novela (`F-146`). La salida, pseudonimizar, es `SPEC-34`, **aprobada, sin `PLAN-34`** |
| Datos que faltan y al menos una contradicción | **Hecho** | `R4`: el Entrevistador real detectó las tres contradicciones del brief |
| Texto libre como contenido no confiable | **Hecho** | `R2`: el detector cazó la inyección reconocible con el modelo real y descartó el texto. Punto ciego declarado: una instrucción que no se parece a ningún patrón no dispara (red-team log) |
| Brief estructurado y validado con schema | **Hecho** | `FichaDeEntrevista` (Pydantic) |

### §2 Lectura (web, con PDF exportado)

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Índice navegable | **Hecho** | Visto hoy en el navegador |
| Fichas con enlace al capítulo donde aparece cada uno | **Hecho**, con un punto ciego | `F-203` cerrado y visto hoy. **`F-142` abierto**: enlaza donde el plan declaró presente al personaje, no donde el texto lo pone |
| Portada con dedicatoria | **Hecho** | Visto hoy |
| Pedir un cambio desde la página | **A medias** | La página existe: fragmento, hecho o nombre, capítulos que se tocarían, confirmar. **Confirmar desde la web no regenera**: el worker de la API no tiene agentes (`F-126`, a propósito: nadie confirma el gasto desde la web), y una obra entregada no tiene ficha, así que un renombrado se rechaza (`F-91`, `F-147`). **La regeneración real se hizo por terminal** (`pedir_cambio.py`, demo B4) y la web enseña su resultado |
| «Regenera solo esos capítulos» | **Diferencia declarada** | La salida que eligió la medida es la cascada (`SPEC-23`, arrastre medio 2,33 ≤ 3): reescribe **desde el primer capítulo que usa lo cambiado hasta el final**, no solo esos. En B4 fueron del 4 al 10 |
| Sin romper la continuidad | **Hecho** | B4, versión 3: reverificación de 10 escenas, las 10 verificadas, y Lean con código 0 |
| Marca de capítulos cambiados | **Hecho** | Visto hoy: «cambió en esta versión» en 4–10 e «igual que en la versión anterior» en 1–3 |
| Se conserva la versión anterior | **Hecho** | La versión 1 se lee entera; la 2, parada, también |
| PDF exportado de la novela de ejemplo | **Hecho** | `ejemplos/novela-ejemplo.pdf`, 68 páginas, de `R1` publicada. Es la versión 1, anterior a la demo |

### §3 Harness

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Tres roles como mínimo | **Hecho** | Ocho definiciones en `.claude/agents/`: entrevistador, planificador, revisor del plan, escritor, editor, juez, resumidor e inspector visual |
| `CLAUDE.md`, una skill y dos hooks | **Hecho** | `CLAUDE.md`; `.agents/skills/novela-regalo/SKILL.md`, citada desde `docs/proceso/claude-code.md`; `.claude/settings.json` engancha `backend/hooks/validar_capitulo.py` en `Stop` y `policy.py` en `PreToolUse`. **Hoy no he vuelto a comprobar que disparen en una ejecución real** |
| Tools con schema validado | **Hecho** | Las tres tools de solo lectura de la story bible por MCP (`SPEC-28`) |
| Retries con límite | **Hecho, con un defecto abierto** | Los topes existen y se ejercieron. **`F-110`**: valen por ejecución, y relanzar los reinicia |
| Tokens y coste por novela en Langfuse | **Hecho** | El coste de `R1` en Langfuse y en el libro es el mismo: 16,8905 USD en 36 delegaciones (`harness/evals/medidas.md`) |

### §4 Memoria

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Story bible en SQLite, con los capítulos donde se usa cada hecho | **Hecho** | `uso_de_hecho` |
| Tabla de cronología que alimenta Lean | **Hecho** | `evento_cronologico` y `participacion_en_evento`; Lean las lee (§5) |
| Resúmenes por capítulo | **Hecho, con un defecto abierto** | **`F-116`**: una caída entre consolidar y resumir deja el capítulo sin resumen para siempre |
| Checkpoint por capítulo | **Hecho, con un defecto abierto** | Ejercido en real: `--reanudar` en `R1`, `R5` y la antes-2; `--relanzar` en B4. **`F-112`**: una caída entre las dos transacciones de consolidar deja un estado que la reanudación no sabe leer |

### §5 Validación y evaluación

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Programáticos (schema, nombres exactos, longitud, imprescindibles, vetadas) | **Hecho** | El schema del plan, `INV-22`, `INV-17`, `INV-23` e `INV-21`, ejercidos en `R1` y `R5` (`harness/evals/resultados.md`) |
| Validación visual por browser MCP | **A medias** | `INV-30` existe y **falló en real** (`F-141`, arreglado; `F-142`, abierto). **Que devuelva el error al writer no existe**: el autor lo dejó fuera y está declarado |
| Nombre, punto de ejecución y score en Langfuse de cada validador | **Hecho** | Tabla de validadores en `docs/proceso/diagramas.md` |
| LLM-as-judge con rúbrica, nota y justificación | **Hecho** | El Editor, seis criterios; en `R1`, medias de 4,00 (ritmo) a 5,00 (tono) |
| Revisión humana de una novela completa | **No existe** | Es del autor. **La plantilla y el script de comparación que prevé `PLAN-31` tampoco existen**: no hay `harness/evals/revision-humana-brief-base.json` ni `comparar.py` |
| Lean: fichero generado desde SQLite, al menos dos invariantes | **Hecho** | `specs/lean/generar_lean.py`; cuatro invariantes, `L-1`…`L-4` (`specs/lean/README.md`) |
| Lean automático, y si falla no se publica | **Hecho** | La puerta ejecuta `lake`; en B4 **no publicó** la versión 3 mientras Lean no tenía veredicto (`F-151`, arreglado) y la publicó con código 0 |
| Lean: un caso real que los demás no vieran, o por qué no | **Justificado, sin caso** | Ningún caso real. En el brief temporal (`R3`) el Revisor paró el plan por sus incoherencias antes de escribir, y Lean no tuvo eventos que mirar (`EX-15`) |
| TLA+ del flujo, invariantes, liveness, TLC, correspondencia con el código, contraejemplos | **Hecho, con una deuda** | `specs/tla/`: `HarnessNovela.tla`, `HarnessBackend.tla` y sus `.cfg`; el README relaciona acciones y código y documenta los contraejemplos con su cambio en el código. **El modelo no se ha vuelto a pasar por TLC tras los arreglos de `CE-14` y `CE-15`** (lo dice su README); los cubren pruebas |
| Cinco briefs, uno adversarial y uno temporal | **Hecho** | `harness/evals/`; los cinco se ejecutaron en la pasada «antes» |
| Tabla por brief de qué pasó y qué falló | **Hecho, con una limitación** | `harness/evals/resultados.md`, con la columna del Revisor desde hoy. **Enseña la última ejecución de cada brief y pasada**, así que la fila del brief base es la antes-2, incompleta, y `R1` no sale (sigue en `3717f25` y en `medidas.md`). Cambiarlo es cambiar `SPEC-31` `RF-02` |
| Una iteración de tuning, antes y después | **Abierto declarado** | T1 se commiteó (`6deefe5`) y **no se midió**: la antes-2 paró tres veces en el capítulo 3 por `F-155`, y el autor cerró el tuning sin «después». 8,7712 USD en 14 delegaciones (`medidas.md`) |

### §6 Observabilidad y §7 Guardrails

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Traza por novela en una sesión; spans por rol y por tool; tokens, coste y latencia; scores; prompts versionados | **Hecho** | `SPEC-29`/`PLAN-29`; cada guion informa del envío. **`F-154`**: la versión del prompt del Escritor es la huella de `escritor.md` y no cambia cuando cambia lo que recibe |
| Guardrail en tres niveles, normalizado, devuelve al writer con límite, se para e informa, audit log y Langfuse, tests por nivel y variante | **Hecho, sin disparar en real** | En `R5`, el brief diseñado para ello, **ninguna vetada disparó**: el Escritor esquivó las variantes porque su prompt le da la lista. Las pruebas cubren cada nivel y las variantes |

### Restricción global y entregables

| Requisito | Estado | Evidencia |
| --- | --- | --- |
| Máximo de 100.000 tokens concurrentes | **Hecho** | Límite sobre lo que se envía. Primera medida: 419 tokens estimados en el capítulo 1; el contexto no se ha recortado nunca (`CLAUDE.md`) |
| Novela de ejemplo en PDF | **Hecho** | `ejemplos/novela-ejemplo.pdf` |
| `/docs` de proceso | **Hecho** | `docs/proceso/`: spec inicial, trade-offs, explainers, diagramas, registro de iteraciones, red-team log y uso de Claude Code. El enunciado dice «storyMaker»; el repositorio se llama `My_novel_story` |
| Vídeo de demo | **No existe** | No hay `presentacion/`. Es del autor |
| Sin claves; `.env.example` | **Hecho** | `backend/.env.example`. En la raíz no hay |
| `CLAUDE.md`, `.claude/` con memoria y comandos, MCP de browser, su uso documentado, skills y subagentes documentados | **Hecho** | `.claude/memory/`, `.claude/commands/inspeccionar-novela.md` y `.claude/agents/` commiteados; `.mcp.json` con Playwright MCP; `docs/proceso/claude-code.md` |

## 6. Levantar mi parte en local

Lo general (instalar, clonar, dependencias, la base de la demo) está en el apartado 2. Lo que
añade mi parte:

### Lo que no viaja por git

| Fichero | Dónde está | Para qué | Si se pierde |
| --- | --- | --- | --- |
| `backend/ejemplo-web.db` | `My_novel_story-examen` | La demo: la novela de ejemplo con sus versiones 1, 2 y 3 | Se pierde la demo. **Es la única copia con la versión 3**: la que hice antes de B4 estaba en un directorio temporal de la sesión, que no sobrevive |
| `backend/evaluacion.db` | `My_novel_story-r1` | El libro de gasto de la evaluación: 55,9066 USD en 126 delegaciones | El techo de gasto empezaría de cero. Las cifras están también en `medidas.md` y `resultados.md` |
| `backend/evaluacion-<ejecucion>.db` | `My_novel_story-r1` | La base de cada ejecución real | La tabla no se puede regenerar |
| `backend/.env` | `My_novel_story-examen` y `My_novel_story-r1` | Las claves de Langfuse | Todo funciona y no se envía nada a Langfuse; se dice. **No se commitea ni se pega en un chat** |

### Qué hace falta instalar para lo que gasta

`claude` con la sesión iniciada (cada generación delega en Claude Code) y Lean 4 con `lake`
4.34.0 para la puerta de publicación. Los modelos de cada rol están en
`backend/config/sistema.json`, que sí viaja.

### Las órdenes, en PowerShell

**La web sobre la demo**, como está en marcha ahora (8000/5173):
```powershell
# Ventana 1
cd C:\Users\student\Desktop\My_novel_story-examen\backend
$env:HARNESS_BASE = "ejemplo-web.db"
python -m uvicorn app.main:app --port 8000

# Ventana 2
cd C:\Users\student\Desktop\My_novel_story-examen\frontend
npm run dev
```
Y se abre **http://localhost:5173**. Por ejemplo,
http://localhost:5173/obras/brief-base-antes-1/indice (con el selector de versiones) y
http://localhost:5173/obras/brief-base-antes-1/versiones/3/capitulos/brief-base-antes-1-cap-04-v3.

**Las pruebas:**
```powershell
cd backend;  python -m pytest app -q                 # 1281 al cerrar
cd frontend; npx vitest run                          # 108 al cerrar
python -X utf8 harness/documentos/contrato.py        # desde la raíz: el congelado coincide
```

**Lo que gasta.** Todo pide `--confirmo-el-gasto`; sin la bandera, solo enseña lo que haría:
```powershell
# Cuánto hay gastado y cuánto queda, sin gastar (desde My_novel_story-r1\backend, donde está el libro)
python -X utf8 evaluar.py ..\harness\evals\brief-base.json --pasada antes
# Pedir un cambio (desde My_novel_story-examen\backend): sin --confirmo-el-gasto solo enseña la propuesta
python -X utf8 pedir_cambio.py --base ejemplo-web.db --obra brief-base-antes-1 --personaje <id> --nombre "<nombre>" --texto "<palabras del lector>" --ficha ..\ejemplos\brief-ejemplo.json
# Volver a atender un trabajo parado sin pedir otra vez
python -X utf8 pedir_cambio.py --base ejemplo-web.db --obra brief-base-antes-1 --relanzar <trabajo> --ficha ..\ejemplos\brief-ejemplo.json --confirmo-el-gasto
```

## 7. Qué queda y por dónde seguir

**Primero, las decisiones del autor**, porque desbloquean lo demás:

1. **Subir `examen-cierre` a GitHub** (apartado 1). Sin eso, nada de esto existe fuera de esta
   máquina.
2. **La revisión humana y el vídeo.** No existen. La revisión necesita además una plantilla y un
   script de comparación que `PLAN-31` prevé y **no existen**.
3. **`nombre-en-el-prompt`**: fusionar (`F-152`, sin medir) o dejarla.

**Los hallazgos abiertos que importan:**

| Hallazgo | Qué pasa | Por dónde seguir |
| --- | --- | --- |
| **`F-155`** | El Planificador **no siembra nunca** el conocimiento inicial: los tres planes de las generaciones por ficha (`R1`, `R5`, antes-2) tienen `conocimiento_inicial` vacío, y **dos de esas tres generaciones se pararon por lo mismo** (`INV-03`: un secundario actúa sobre un imprescindible de la destinataria que nadie le sembró). Es la Regla 4: ni `planificador.md` ni el código lo piden (`esquemas.py:266`) | Una spec que decida quién siembra qué. **Es lo primero antes de volver a intentar el tuning**, que se paró por esto (unos 40 USD: una pasada antes y otra después) |
| **`F-110`** | Relanzar reinicia los contadores de reintento: los topes valen por ejecución, no por capítulo ni por plan | Decisión del autor pendiente. El dato para no reiniciar existe (`repo.intentos_de`) |
| **`F-112`** | Consolidar son dos transacciones; una caída entre ellas deja la escena en un estado que la reanudación no sabe leer, y la convierte en parada | Una sola transacción, o que la reanudación reconozca ese estado |
| **`F-116`** | Una caída entre consolidar y resumir deja el capítulo sin resumen para siempre, y el informe no lo dice | Que la reanudación detecte los capítulos consolidados sin resumen |
| **`F-142`** | Las fichas enlazan donde el plan declaró presente al personaje, no donde el texto lo pone (`INV-30` lo vio en real) | Decisión del autor: que el delta declare los presentes o que el Editor los contraste |

**Además, abiertos y con su causa escrita en `docs/verification.md`:** `F-146` (espera `PLAN-34`,
que no se aprueba sin revisar antes con la sesión del frontend cómo pide los nombres la
entrevista), `F-126` y `F-147` (pedir un cambio de principio a fin desde la web), `F-154`, la
tabla que solo enseña la última ejecución (`SPEC-31` `RF-02`) y volver a pasar TLC tras `CE-14`
y `CE-15`.

**Para comprobar este apartado:**
```
git -C C:\Users\student\Desktop\My_novel_story-examen log --oneline -6
git -C C:\Users\student\Desktop\My_novel_story-examen branch --no-merged examen-cierre
grep "^| F-155 |" docs/verification.md
```

---

## 8. La sesión de la máquina nueva (2026-09-25)

Foto, como el resto. Rama **`web-de-principio-a-fin`**, que sale de `examen-cierre` y **no está
en GitHub**: publicarla es decisión del autor.

- **Se perdió `ejemplo-web.db`** con la máquina anterior: la demo de «La ruta de Pimienta» y su
  versión 3 ya no existen aquí. En su lugar, `backend/web.db`: las semillas de la novela regalo y
  de la lectura, **datos inventados**, y una entrevista completa sin cerrar para ver el cuaderno
  completo.
- **Hecho:** `F-204`; `PLAN-34` aplicado (`SPEC-34` a `specs/aplicadas/`, `F-146` cerrado en el
  harness, `F-205`, `F-207`); `PLAN-35` v3 y v4 aplicados (`SPEC-35` v5, `F-206`): la entrevista
  con Xime y su cuaderno, el cuaderno completo y la generación de noche.
- **Sin Node en la máquina**, que el autor no puede instalar: la web se sirve con el Node de VS
  Code. `arrancar-web.ps1` lo hace solo.
- **Lo que no se ha ejercido aquí**: ninguna llamada al modelo (gasta). Ni un turno de la
  entrevista con el Entrevistador real ni una generación. Sin Lean (`lake`) una novela generada
  no se publica: se lee como «lo escrito», sin PDF.

**Levantar:** `powershell -ExecutionPolicy Bypass -File .\arrancar-web.ps1` y abrir
http://127.0.0.1:5173/.
