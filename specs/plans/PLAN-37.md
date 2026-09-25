---
id: PLAN-37
spec: SPEC-37
titulo: Implementación de la historia de cada novela en la administración
estado: aplicada
fecha_aplicacion: 2026-09-25
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo […]»), tras su elección de la propuesta C"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-37

Cada paso empieza por la prueba que falla y deja en verde backend, harness, contrato,
frontend, `tsc` y steiger. **Ningún paso llama al modelo.**

## Pasos

### H1 · La historia, del backend (`RF-02`..`RF-04`)

`features/regalo/historia.py` (nuevo) y `GET /admin/obras/{id}/historia`: `totales`,
`por_agente`, `abiertos` y `eventos` (`entrevista`, `ronda_del_plan`, `capitulo`, `parada`,
`ronda_de_la_puerta`, `version`), por SQL. El coste de cada capítulo, atribuido por la última
fila de progreso anterior a cada gasto. Contrato regenerado.

**Prueba que falla primero:** `test_la_historia_cuenta_los_capitulos_con_sus_notas_y_su_coste`.
Además:
- `test_una_parada_trae_su_capitulo_su_motivo_y_sus_intentos`;
- `test_las_rondas_de_la_puerta_traen_lean_y_condiciones`;
- `test_una_version_nueva_trae_su_peticion_y_los_capitulos_que_cambiaron`;
- `test_el_coste_por_agente_y_los_abiertos_con_su_invariante`;
- `test_una_obra_que_no_existe_es_404`.

### H2 · La página (`RF-01`..`RF-03`)

`pages/historia-de-obra`, ruta `/admin/obras/:obra`; cada fila de `/admin` enlaza a ella.
**Prueba que falla primero:** `HistoriaDeObra › cuenta la novela en orden, con las seis notas
de cada capítulo`. Además `› una parada y una ronda que no publica se distinguen con texto`, `›
una versión trae su petición y sus capítulos`, `› el lateral trae el coste por agente y los
abiertos` y `› el coste atribuido dice cómo se atribuyó`.

### H3 · Inspección y `docs/`

Edge sin cabeza sobre `backend/web.db`; `docs/verification.md` (`VER-139`), `AGENTS.md` y
`SPEC-37` a `aplicada`.
