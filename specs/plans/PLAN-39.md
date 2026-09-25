---
id: PLAN-39
spec: SPEC-39
titulo: Implementación de publicar y reanudar desde la web
estado: aplicada
fecha_aplicacion: 2026-09-25
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo […]»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-39

Cada paso empieza por la prueba que falla. **Ningún paso llama al modelo**: los agentes y Lean
son dobles.

### P1 · Las acciones posibles, del backend (`RF-01`..`RF-05`, `RF-07`)

`orquestacion/acciones.py` y `GET /obras/{id}/acciones` → `{publicar, reanudar}`, cada una con
`posible`, `motivo`; publicar con `lean_disponible`, `lean_motivo` y el coste medio del Editor;
reanudar con `desde_capitulo`, `faltan`, `coste_por_capitulo` y su `fuente`, y `estimacion_usd`.

**Prueba que falla primero:** `test_una_novela_escrita_sin_publicar_se_puede_publicar`. Además
`test_sin_lake_publicar_no_es_posible_y_dice_por_que`, `test_una_parada_se_puede_reanudar_desde_su_capitulo`,
`test_la_estimacion_usa_lo_medido_o_la_referencia`, `test_con_algo_en_curso_no_se_puede_nada`.

### P2 · Publicar (`RF-01`..`RF-03`)

`POST /obras/{id}/publicaciones` → `202` con un trabajo, o `409` con el motivo (sin Lean, sin
ficha, sin terminar). El trabajo hace una ronda de `publicacion.evaluar` con el Editor aislado y
pseudonimizado, y deja `{publicada, ronda, condiciones, lean}`. Las vetadas de la versión salen
de una función nueva de `novela.py` que ya usa `escribir_version`.

**Prueba que falla primero:** `test_publicar_pasa_la_puerta_y_publica`. Además
`test_si_no_pasa_dice_que_condicion_fallo`, `test_sin_lake_es_409_y_no_llama_al_editor`.

### P3 · Las huérfanas (`RF-06`, `F-208`)

`orquestacion/regalo.abandonar_huerfanas`, llamada al arrancar. **Prueba que falla primero:**
`test_al_arrancar_una_generacion_en_curso_queda_abandonada_y_la_obra_parada`.

### P4 · La web (`RF-01`..`RF-05`)

`features/acciones-de-obra`: el bloque de publicar y el de reanudar, en la generación y en la
página de la novela de la administración. **Prueba que falla primero:** `AccionesDeObra ›
publicar avisa del Editor y enseña la condición que falló`. Además `› sin Lean lo dice y no hay
botón`, `› reanudar dice desde qué capítulo y cuánto, y no se lanza sin confirmar`.

### P5 · Inspección y `docs/`

Edge sin cabeza; `VER-141`, `F-208`, `AGENTS.md`, `SPEC-39` a `aplicada`.
