---
id: PLAN-35
spec: SPEC-35
titulo: Implementación de las seis pantallas rediseñadas — primera tanda
estado: aprobada
aprobada_por: "autor del proyecto, en sesión («si escribe el plan y ejecutalo»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 2
---

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
