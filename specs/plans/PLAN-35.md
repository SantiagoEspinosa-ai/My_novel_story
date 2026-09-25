---
id: PLAN-35
spec: SPEC-35
titulo: Implementación de las seis pantallas rediseñadas — primera y segunda tanda
estado: aprobada
aprobada_por: "autor del proyecto, en sesión («si escribe el plan y ejecutalo»); la segunda tanda (v3), la sesión autónoma del 2026-09-24 por delegación escrita del autor («Decide tú todo […] No pares a consultarme»)"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 3
---

> **v3 (2026-09-24), la segunda tanda.** `PLAN-34` ya está aplicado, que era lo que esperaba:
> los nombres se escriben en su campo (`PUT /entrevistas/{id}/nombres`) y el historial trae
> `nombres`. Esta tanda son la entrevista con Xime, el cuaderno y el cuaderno completo
> (`RF-04`..`RF-07`) y la página de la generación (`RF-13`, `SPEC-35` v5). Pasos F0–F8, al
> final, después de los de la primera tanda. **Rama `web-de-principio-a-fin`**, en la carpeta
> principal: ya no hay otra sesión con la que repartir ficheros (cuestión 3 de la spec).

> **v2 (2026-09-25), lo hecho frente a lo planeado.** Primera tanda terminada (E0–E8).
> - **E5 es solo estilo.** El panel ya tenía el fragmento como cita, así que su prueba nueva
>   habría pasado sin cambiar nada y no se escribió; lo verificó la inspección.
> - **E7 espera a `vigente`** en la respuesta de versiones (`F-150`, decisión del autor, hecho
>   por la sesión de `PLAN-22` en `89425c4`), y lee de ahí la vigente en vez de deducirla.
> - **E8 encontró `F-201`** (el PDF ofrecido que daba un 500) y lo corrigió con dos pruebas rojas
>   antes.
> - Los estilos van en un CSS propio de cada página o feature, cargado después de `estilos.css`.
> - La segunda tanda (la entrevista con Xime y el cuaderno) sigue esperando al plan de `SPEC-34`.

# PLAN-35 — Las seis pantallas, primera tanda

Cómo se construye `SPEC-35` (v3, aprobada), en el orden de su cuestión 4. **Esta tanda
son las cuatro pantallas de rediseño** (la portada, pedir un cambio, qué se reescribe y la
versión nueva) y sus dos lecturas nuevas en el backend. **La entrevista con Xime y el
cuaderno esperan al plan de `SPEC-34`** (su cuestión 4) y tendrán su propia versión de este
plan.

Cada paso empieza por la prueba que falla y deja en verde las suites **enteras** (backend,
harness, contrato, frontend, `tsc`, steiger). Se commitea por ruta, con el `add` y el
`commit` en un solo comando. **Ningún paso llama al modelo.** Rama `frontend-regalo`, en su
worktree.

## Lo que se encontró al preparar el plan

1. **`RF-02` choca con `CLAUDE.md`.** `CLAUDE.md` dice que una escena se muestra siempre con
   su estado y con los hallazgos abiertos que tenga: *«un texto sin ese contexto induce a darlo
   por bueno»*. Y en lo técnico `CLAUDE.md` manda sobre una spec. **En el índice y el capítulo
   el estado y los hallazgos se quedan**: se rediseñan, pero no se quitan. Quitarlos para el
   cliente exige revisar `CLAUDE.md`, y eso es una decisión del autor. Queda anotado en
   `SPEC-35` v4.
2. **El PDF ya se niega a exportar lo no publicado.** `manuscrito.service.exportar_pdf` lanza
   `VersionNoPublicada` con su motivo. Solo falta la ruta HTTP y una consulta de si hay PDF,
   para que la portada no ofrezca un botón que falla (`RF-12`, cuestión 2).
3. **El texto de la petición existe** (`peticion_de_cambio.texto`), pero la versión solo
   expone su identificador. Se lee con una ruta propia en `features/regalo/`, **sin tocar**
   `orquestacion/schemas.py`, que es de `PLAN-22`/`PLAN-23`.

## Reparto con la sesión de `PLAN-22`

La portada, el índice, el capítulo, `features/pedir-cambio` y `shared/ui/tema` los hizo esa
sesión. Por `SPEC-35` cuestión 3, **el reparto se le propone antes de editarlos**:
- Este plan cambia solo **la presentación** de esas páginas (marcado y CSS) y añade tokens.
- No cambia ni su comportamiento ni sus rutas ni su contrato.
- Sus pruebas siguen pasando o se reescriben diciendo qué comprobaban, nunca se borran.

**Los pasos E1 y E2 no tocan nada suyo y van primero.** E3 a E7 empiezan cuando esa sesión
conteste. Si pide cambios, el plan se corrige.

## Pasos

### E0 · `SPEC-35` v4 y este plan

La nota del hallazgo 1 en la spec. Es documental: no lleva prueba.

### E1 · Descargar el PDF (`RF-12`, cuestión 2)

`features/manuscrito/router.py` (fichero nuevo):
- `GET /obras/{id}/pdf` devuelve el PDF de la versión vigente, con `application/pdf`.
- `GET /obras/{id}/pdf/disponible` devuelve `{disponible, motivo}`.

Los dos usan `exportar_pdf` y `VersionNoPublicada` tal como son. Contrato regenerado.

**Prueba que falla primero:** `test_una_obra_publicada_descarga_su_pdf` (empieza por `%PDF`).
Además:
- `test_una_obra_sin_publicar_no_tiene_pdf_y_dice_por_que` (`409` con el motivo de la puerta);
- `test_disponible_dice_si_hay_pdf_sin_generarlo`;
- `test_obra_que_no_existe_es_404`.

### E2 · El texto de la petición de una versión (`RF-10`)

`GET /obras/{id}/versiones/{n}/peticion` en `features/regalo/`: `{texto}` con las palabras del
lector, o `texto: null` si la versión no nació de una petición. Por SQL, sin importar
`orquestacion`. Contrato regenerado.

**Prueba que falla primero:** `test_la_version_trae_las_palabras_de_su_peticion`. Además
`test_una_version_sin_peticion_trae_texto_nulo` y `test_version_que_no_existe_es_404`.

### E3 · Los tokens del estilo (`RF-01`)

`shared/ui/tema/tokens.ts`: los colores de madera, noche y crema oscuro de la propuesta, dentro
de la paleta provisional marcada como tal. **Prueba que falla primero:** los de `tema.test.ts`
(que ningún fichero escriba un color fuera del tema y el contraste de cada pareja texto-fondo
nueva), extendidos a los colores nuevos.

### E4 · La portada como cubierta (`RF-11`, `RF-12`)

`pages/portada`: la cubierta con el título y la dedicatoria, «Empezar a leer», «Ver el índice»
y **«Descargar en PDF» solo si el backend dice que hay**; si no hay, se dice el motivo y no hay
botón. La barra de progreso de `PLAN-22` se conserva.

**Prueba que falla primero:** `Portada › con PDF disponible ofrece descargarlo`. Además
`› sin PDF no ofrece el botón y dice por qué`, y las de hoy (dedicatoria, sin dedicatoria), que
siguen en verde.

### E5 · Pedir un cambio (`RF-08`)

`features/pedir-cambio`: el panel en el estilo nuevo. El fragmento va como cita, cada hecho o
nombre como una tarjeta de opción, y la caja para las palabras del lector. **No cambia ningún
comportamiento**: las pruebas de hoy (`VER-111`) son la red. **Prueba nueva que falla
primero:** `PedirCambio › el fragmento seleccionado se ve como cita`.

### E6 · Qué se reescribe (`RF-09`)

La propuesta, pintada como una balda con los capítulos de la obra, **resaltados exactamente los
de `capitulos_propuestos`**, y la promesa y su punto ciego juntos. **Prueba que falla
primero:** `PedirCambio › la balda resalta solo los capítulos propuestos`. Confirmar sigue
mandando la lista recibida (`VER-111`).

### E7 · La versión nueva (`RF-10`)

- **El índice:** el selector de versión como interruptor y «cambió» en su etiqueta.
- **El capítulo cambiado de una versión que nació de una petición** abre con el aviso «Este
  capítulo se reescribió por tu cambio: «…»» y el enlace a cómo era antes.
- **Estado y hallazgos**, por el hallazgo 1: se quedan, rediseñados.

**Prueba que falla primero:** `Capitulo › un capítulo cambiado dice qué petición lo cambió`.
Además:
- `› un capítulo compartido no lleva aviso`;
- `› una versión sin petición no lleva aviso`;
- las de `VER-112`, que siguen en verde.

### E8 · Inspección real y `docs/` al día

- **Inspección:** el recorrido en Edge sin cabeza, sin agente ni modelo, sobre una base
  inventada (`SPEC-34` `RF-09`), con una versión 2 nacida de una petición y una obra publicada.
  Puertos 8010 y 5183. Se miran las capturas, no solo las comprobaciones.
- **Documentación:** el registro en `docs/proceso/claude-code.md`, y las filas `VER-xx` y
  `AGENTS.md` que toquen.

## Qué queda para la segunda tanda

La entrevista con Xime (`RF-04`), el cuaderno (`RF-05`, `RF-06`) y el cuaderno completo
(`RF-07`). Esperan al plan de `SPEC-34`, que decide cómo se piden los nombres fuera del modelo.

## Lo que este plan no hace

- No quita el estado ni los hallazgos de una escena mostrada con su texto: `CLAUDE.md`.
- No toca la estantería, la generación ni la administración.
- No hace un diseño móvil.


---

# Segunda tanda (v3)

Mismas reglas que la primera: cada paso empieza por la prueba que falla y deja en verde las
suites enteras (backend, harness, contrato, frontend, `tsc` y steiger). **Ningún paso llama al
modelo.**

## Lo que se encontró al preparar la segunda tanda

1. **`F-206`: la página de la generación da un 404 mientras se planifica.** La obra entra en
   la tabla `obra` al montarse, después de que el Revisor apruebe el plan, y
   `GET /obras/{id}/generacion` solo mira esa tabla. Durante los primeros minutos de una
   novela de verdad, justo cuando quien la encargó acaba de pulsar «Sí, escribir la novela»,
   la página enseña «la API contestó 404». Las pruebas no lo ven porque sus bases ya tienen
   la obra montada.
2. **Si el lanzamiento falla antes de escribir nada** (sin `claude`, sin modelos en
   `sistema.json`), el motivo se queda en la tabla `trabajo` y la página no lo enseña: sin
   ninguna fila de progreso, los diez capítulos dicen «no empezado» para siempre.
3. **El historial no trae la ficha** (`SPEC-35` `RF-05`), y la web no puede contar campos
   (`CLAUDE.md`). El cuaderno lo tiene que dar el backend: lo que se sabe, con palabras de
   persona («cumpleaños», no `cumpleanos`: `RF-02`), lo que falta y cuánto.
4. **La cabecera sigue diciendo «Novela regalo · lectura»**, que era el nombre de la
   primera web, cuando solo leía.

## Pasos

### F0 · `SPEC-35` v5 y este plan

Documental: no lleva prueba.

### F1 · El cuaderno, del backend (`RF-05`, `RF-07`)

`features/entrevista/`: el historial trae `cuaderno`, con `sabido` (cada campo con su
etiqueta y su valor en palabras de persona: los elementos por su descripción, los campos en
`otro` con las palabras del comprador), `falta` (las etiquetas, en el orden de `que_falta`),
`total` y `faltan`, y `propuesta` (título, premisa y dedicatoria, o nulos). Contrato
regenerado.

**Prueba que falla primero:** `test_el_cuaderno_dice_lo_que_se_sabe_y_lo_que_falta`. Además
`test_el_cuaderno_habla_con_palabras_de_persona` y
`test_el_cuaderno_trae_la_propuesta_para_el_cuaderno_completo`.

### F2 · La generación, del backend (`RF-13`, `F-206`)

`features/regalo/`: `GET /obras/{id}/generacion` responde también con una obra que tiene
entrevista o progreso y todavía no se ha montado (sin capítulos); trae `fase_de_la_obra` (la
última de su progreso) y `motivo_del_fallo` (el del último lanzamiento, si terminó fallido o
abandonado). Contrato regenerado.

**Prueba que falla primero:** `test_una_obra_que_se_esta_planificando_no_es_404`. Además
`test_un_lanzamiento_fallido_trae_su_motivo` y `test_la_generacion_trae_la_fase_de_la_obra`.

### F3 · El cliente y las fixtures

`shared/api/cliente.ts`: `declararNombres` y `confirmarAviso`; los tipos nuevos
(`npm run contrato`). `shared/testing/regalo.ts`: el historial con `nombres` y `cuaderno`, y la
generación con sus dos campos nuevos, validados contra el congelado como las demás.

**Prueba que falla primero:** las de `regalo.test.ts`, que validan cada fixture con el
congelado.

### F4 · La entrevista con Xime y el cuaderno (`RF-04`, `RF-05`, `RF-06`)

`shared/config`: `ENTREVISTADORA = { nombre: "Xime" }`. `pages/entrevista`:
- **La conversación**, con Xime: su cara (una inicial en un círculo, CSS, sin imagen) y su
  nombre en cada pregunta. El modelo no finge ser nadie: el nombre lo pone la web.
- **El cuaderno lateral**: lo que se sabe y lo que falta, con «faltan N de M», tal como llega.
- **Los nombres** (`RF-06`): mientras no hay destinatario, la primera respuesta se escribe en
  el campo del nombre; después, el cuaderno deja añadir y quitar personas y mascotas (nombre,
  tipo, relación), quién regala y los nombres que no deben aparecer, y confirmar cada aviso de
  nombre. **Siempre el nombre real.** Un turno `fuera_del_modelo` se ve como tal.

**Prueba que falla primero:** `Entrevista › la primera respuesta es el nombre y va al campo
de nombres`. Además:
- `› cada pregunta la firma Xime, con el nombre de la configuración`;
- `› el cuaderno enseña lo sabido y lo que falta tal como llega`;
- `› añadir una mascota manda los nombres completos`;
- `› un aviso de nombre se confirma desde el cuaderno`;
- las de hoy (`VER-131`), que siguen en verde o se reescriben diciendo qué comprobaban.

### F5 · El cuaderno completo (`RF-07`)

Con `puede_cerrar`: el repaso de la ficha, el título, la premisa y la dedicatoria propuestos,
«Quiero cambiar algo» (vuelve a la conversación) y «Cerrar la ficha», que avisa de que **no
tiene vuelta atrás**. Cerrada, la confirmación de gasto de `SPEC-33` `RF-12`, sin quitarle
nada.

**Prueba que falla primero:** `CuadernoCompleto › con puede_cerrar enseña la propuesta y el
aviso de que cerrar no tiene vuelta atrás`. Además `› quiero cambiar algo vuelve a la
conversación` y las de `ConfirmarGeneracion`, que siguen en verde.

### F6 · La generación, de noche (`RF-13`)

`pages/generacion`: el estilo noche con los tokens de `shared/ui/tema`; el motivo del último
lanzamiento si falló; y al terminar, «Leer la novela» (publicada) o «Leer lo escrito» con el
motivo de que no se publicara, que da `GET /obras/{id}/pdf/disponible`. Sin capítulos todavía
(planificando), lo dice en vez de pintar una fila vacía.

**Prueba que falla primero:** `Generacion › un lanzamiento fallido enseña su motivo`. Además
`› publicada lleva a leer la novela`, `› sin publicar lleva a leer lo escrito y dice por qué` y
`› planificando, sin capítulos, lo dice`.

### F7 · La cabecera

`shared/ui/cabecera`: «Novelas para regalar». **Prueba que falla primero:** la de
`App.test.tsx` que lee la cabecera.

### F8 · Inspección real y `docs/` al día

- **Inspección:** Edge sin cabeza sobre la base de la semilla (`semilla_regalo.py`, datos
  inventados, `SPEC-34` `RF-09`), sin modelo y sin gastar: la estantería, una entrevista
  nueva hasta el campo del nombre, la entrevista a medias con su cuaderno, la cerrada con su
  cuaderno completo y la confirmación, la generación en curso y la publicada. Se miran las
  capturas.
- **Documentación:** `docs/verification.md` (`VER-137`, `F-206`), `docs/proceso/claude-code.md`
  y `AGENTS.md`.

## Lo que la segunda tanda no hace

- No quita el estado ni los hallazgos del índice y el capítulo (`CLAUDE.md`, hallazgo 1).
- No lanza ninguna generación de verdad: gasta, y lo decide el autor.
- No hace la estantería de madera ni la administración.
