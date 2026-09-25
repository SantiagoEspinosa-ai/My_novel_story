---
id: PLAN-45
spec: SPEC-45
titulo: El cambio del lector desde la web
estado: aprobada
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo lo demás»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-45

### C1 · El worker con agentes (`RF-01`, `RF-02`)

- `orquestacion/router._atender` pasa a `regeneracion.atender`:
  - los agentes de `regalo.agentes` (o `app.state.agentes_regalo` en las pruebas), con `gasto.anotador`;
  - `VerificadorLean` (o `app.state.lean_regalo`);
  - el `sistema` de la web;
  - la carpeta de reglas.
- `POST /obras/{id}/cambios` responde `409` con el techo alcanzado.

**Pruebas que fallan primero:**
- `test_el_cambio_desde_la_api_escribe_la_version_con_los_agentes_del_worker`
- `test_con_el_techo_alcanzado_no_se_encola_el_cambio`

La prueba vieja `test_sin_agentes_el_worker_no_escribe_nada_y_lo_dice` pasa a comprobar la cascada sin agentes llamándola directamente, no por la API.

### C2 · El detalle en la administración (`RF-04`)

- `features/regalo`: `GET /admin/obras/{id}/cambios` devuelve `[{texto, creada_en, estado, motivo}]`, de `peticion_de_cambio` y su `trabajo`.
- `pages/historia-de-obra` pinta «Cambios pedidos» en la pestaña de la línea de tiempo.

**Pruebas que fallan primero:**
- `test_los_cambios_pedidos_con_su_estado_y_su_motivo`
- `HistoriaDeObra › cambios pedidos con su motivo`

### C3 · El lector (`RF-03`)

- `features/pedir-cambio` deja de pintar `trabajo.motivo`.
- Si el cambio falla, dice que no se aplicó, que la novela sigue como estaba y que quien administra la web tiene el detalle.

**Prueba que falla primero:** `PedirCambio › si falla, el lector ve un mensaje que se entiende y no el motivo técnico`.

### C4 · `docs/`

`F-126` cerrado; `VER-111` (pedir el cambio desde la web, ejercido); `AGENTS.md`; la spec pasa a `aplicada`.
