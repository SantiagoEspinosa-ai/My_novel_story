---
id: PLAN-41
spec: SPEC-41
titulo: Implementación de retirar de la estantería y del techo entre capítulos
estado: aplicada
fecha_aplicacion: 2026-09-25
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo lo demás»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-41

### R1 · Retirar (`RF-01`, `RF-02`)

`docs/definitions.md`: la clase `RetiradaDeLaEstanteria` (obra, motivo, quien, cuando).
Migración 20, la tabla. `features/regalo/`: la estantería no enseña las retiradas; la
administración las trae con `retirada: {motivo, quien, cuando}`. `POST /admin/obras/{id}/retirada`
(con el motivo) y `DELETE` para deshacer. Contrato regenerado. La web de la administración
enseña el motivo.

**Prueba que falla primero:** `test_una_obra_retirada_no_sale_en_la_estanteria_y_si_en_admin`.
Además `test_retirar_exige_motivo`, `test_retirar_se_deshace`, y en el frontend
`Administracion › una novela retirada lo dice con su motivo`.

### R2 · El techo entre capítulos (`RF-03`)

`orquestacion/regalo.generar` pasa a `novela.escribir` un `seguir` que mira lo gastado en la
base contra el techo de la web. **Prueba que falla primero:**
`test_la_generacion_web_se_para_entre_capitulos_al_llegar_al_techo`.

### R3 · `docs/`

`VER-143`, `AGENTS.md`, `SPEC-41` a `aplicada`.
