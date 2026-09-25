---
id: PLAN-38
spec: SPEC-38
titulo: Implementación de la matriz por capítulo de cada novela
estado: aprobada
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo […]»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-38

Cada paso empieza por la prueba que falla y deja en verde backend, harness, contrato,
frontend, `tsc` y steiger. **Ningún paso llama al modelo.**

### M1 · La matriz, del backend (`RF-01`..`RF-03`, `RF-07`)

`features/regalo/historia.py`: la atribución se saca a una función que usan la historia y la
matriz; `matriz(con, obra, umbral, techo, version)` y `GET /admin/obras/{id}/matriz?version=N`
→ `{obra, titulo, version, versiones, cifras, filas, totales, paradas, puerta, por_agente,
abiertos, atribucion}`. Contrato regenerado.

**Prueba que falla primero:** `test_la_matriz_trae_una_fila_por_capitulo_con_sus_seis_notas`.
Además `test_un_capitulo_compartido_cuesta_lo_de_la_version_que_lo_escribio`,
`test_la_fila_de_totales_trae_medias_y_sumas`, `test_las_cifras_de_arriba`,
`test_la_version_que_no_existe_es_404`.

### M2 · Los colores de las notas (`RF-04`, `RF-07`)

`shared/ui/tema/tokens.ts`: `NOTA_DEL_EDITOR`, del 1 al 5, con su contraste en `tema.test.ts`.

### M3 · La página (`RF-01`..`RF-06`)

`pages/historia-de-obra`: pestañas «Por capítulo» (por defecto) y «Línea de tiempo»
(`?vista=linea`); la matriz con su selector de versión (`?version=N`), la leyenda, las paradas y
la puerta, y el panel del coste por agente y los abiertos. Las pruebas de la línea de tiempo se
quedan, abiertas en su pestaña.

**Prueba que falla primero:** `Matriz › una fila por capítulo con las seis notas escritas y
en color`. Además `› la fila de medias y totales`, `› la leyenda explica cada color`, `› las
cuatro cifras de arriba`, `› cambiar de versión pide esa versión` y `› la línea de tiempo es la
segunda pestaña`.

### M4 · Inspección y `docs/`

Edge sin cabeza; `VER-140`, `AGENTS.md`, `SPEC-38` a `aplicada`.
