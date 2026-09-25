---
id: PLAN-44
spec: SPEC-44
titulo: Generar o reanudar desde la administración
estado: aprobada
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo lo demás»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-44

### G1 · El backend (`RF-01`, `RF-02`, `RF-03`)

- `orquestacion/acciones.acciones` gana `generar: {posible, motivo, estimacion_usd, fuente}`.
- Una obra existe si está en `obra` **o** tiene entrevista.
- «Nunca lanzada» quiere decir sin filas en `progreso_de_generacion`.
- La estimación es la media de `gasto_de_delegacion` por obra publicada; sin ninguna publicada, `REFERENCIA_NOVELA_DE_EJEMPLO`.
- El esquema `AccionesDeObra` gana `Generar`, y se regenera el contrato.

**Pruebas que fallan primero:**
- `test_una_novela_solo_con_entrevista_tiene_acciones_y_se_puede_generar`
- `test_una_entrevista_abierta_no_se_puede_generar_y_dice_por_que`
- `test_una_lanzada_ya_no_se_genera_sino_que_se_reanuda`
- `test_la_estimacion_de_generar_es_la_media_de_las_publicadas`

### G2 · El frontend (`RF-03`, `RF-04`)

- `features/acciones-de-obra`: `AccionesDeObra` gana el bloque «Generar la novela», con su estimación y el gasto frente al techo. Lanza con `lanzar` y lleva a la página de la generación.
- Nuevo `BotonDeAccion`: lee las acciones de una obra y pinta «Generar», «Reanudar» o «Publicar» como enlace a `/admin/obras/:id`; si no hay ninguna posible, nada.
- `pages/administracion` lo pone en una columna «Acción».

**Pruebas que fallan primero:**
- `AccionesDeObra › una novela sin generar ofrece generarla con su estimación`
- `BotonDeAccion › ofrece la acción que toca`
- `Administracion › cada fila lleva su acción`

### G3 · `docs/`

`docs/verification.md`, fila `VER-144`; `AGENTS.md`; la spec pasa a `aplicada`.
