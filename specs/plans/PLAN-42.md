---
id: PLAN-42
spec: SPEC-42
titulo: La administración enseña la estantería
estado: aprobada
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo lo demás»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-42

### P1 · El backend (`RF-01`, `RF-03`)

`features/regalo/service.administracion` recorre `estanteria(con)["obras"]`, la misma lista y en el mismo orden, en vez de `obras_de_la_estanteria`. El campo `retirada` sale de `ObraEnLaAdministracion`: ya no puede tener valor. El contrato se regenera.

**Prueba que falla primero:** `test_la_administracion_ensena_la_estanteria_en_su_orden_y_sin_retiradas`. La prueba de `SPEC-41` que pedía ver la retirada en la administración se reescribe: la retirada sigue en la base (`repo.retiradas`) y no sale en la administración. Además, `test_devolver_una_retirada_la_devuelve_a_la_administracion`.

### P2 · El frontend

`pages/administracion` deja de pintar el bloque «retirada de la estantería». Los tipos salen del contrato. Su prueba de la retirada se retira; se añade la prueba de que la tabla sigue el orden que llega.

### P3 · `docs/`

`AGENTS.md` (`SPEC-42`, `PLAN-42`); `docs/verification.md`, `VER-143`, a lo que dice `SPEC-42`.
