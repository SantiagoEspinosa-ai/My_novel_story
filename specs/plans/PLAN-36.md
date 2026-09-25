---
id: PLAN-36
spec: SPEC-36
titulo: Implementación de la estantería de madera, el escritor en su mesa y la administración
estado: aprobada
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo […]»), tras su elección de las propuestas"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-36

Cada paso empieza por la prueba que falla y deja en verde backend, harness, contrato,
frontend, `tsc` y steiger. **Ningún paso llama al modelo.** Rama `web-de-principio-a-fin`.

## Pasos

### G1 · El backend: el título en la generación y la administración (`RF-02`, `RF-03`)

- `features/regalo/`: `GeneracionEnVivo.titulo` (de `obra`, nulo sin montar).
- `features/regalo/`: `GET /admin/obras` → `{gastado, techo_usd, obras: [{id, titulo, fase,
  coste, hallazgos: {bloqueante, mayor, menor}, codigo_lean}]}`, por SQL. Contrato regenerado.

**Prueba que falla primero:** `test_la_administracion_trae_cada_obra_con_su_coste_y_hallazgos`.
Además `test_la_generacion_trae_el_titulo_de_la_obra`, `test_sin_montar_el_titulo_es_nulo`,
`test_el_codigo_de_lean_es_el_del_ultimo_veredicto`.

### G2 · La estantería de lomos (`RF-01`)

`pages/estanteria`: baldas de lomos (color del lomo por presentación, estable por obra), la
ficha del lomo elegido al lado, «Encargar una novela». **Las pruebas de hoy se reescriben
diciendo qué comprobaban**: lo que estaba en la tarjeta está ahora en el lomo (título, estado)
o en su ficha (dedicatoria, destinatario, enlaces).

**Prueba que falla primero:** `Estanteria › pulsar un lomo abre su ficha con dedicatoria,
destinatario y lo que se puede hacer`.

### G3 · El escritor en su mesa (`RF-02`)

`pages/generacion`: la escena (CSS), el título, «Escribiendo el capítulo N de M» y la fila de
hojas; debajo, lo de hoy. **Prueba que falla primero:** `Generacion › la mesa dice qué
capítulo se escribe y el título de la novela`. Además `› la fila de hojas marca las escritas y
la actual` y `› sin título todavía lo dice`.

### G4 · La administración (`RF-03`)

`pages/administracion`, ruta `/admin`, enlace en la cabecera. **Prueba que falla primero:**
`Administracion › cada novela con su fase, coste, hallazgos y Lean, tal como llegan`. Además `›
un coste con suelo lo dice` y la de la ruta.

### G5 · Inspección y `docs/`

Edge sin cabeza sobre `backend/web.db` (datos inventados): la estantería con una ficha abierta,
la mesa, la administración. `docs/verification.md` (`VER-138`), `AGENTS.md`, `SPEC-36` a
`aplicada`.
