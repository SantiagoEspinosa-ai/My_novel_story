---
id: PLAN-40
spec: SPEC-40
titulo: Implementación del protagonista ante los agentes
estado: aplicada
fecha_aplicacion: 2026-09-25
aprobada_por: "sesión del 2026-09-25, por la delegación escrita del autor («Decide tú todo […]»), tras su elección de la opción B"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# PLAN-40

Cada paso empieza por la prueba que falla. **Ningún paso llama al modelo.**

### Q1 · La vista y la guarda (`RF-01`, `RF-04`, `RF-05`)

`commons/politica/vista_de_agentes.py`: `ficha_para_agentes`, `ficha_desde_agentes` y
`PALABRAS_DEL_REGALO`. **Prueba que falla primero:**
`test_la_vista_lleva_al_protagonista_y_nada_del_regalo`. Además
`test_una_ficha_con_protagonista_se_lee_como_destinatario`.

### Q2 · Los prompts (`RF-02`, `RF-03`)

La vista en el Entrevistador (`entrevista/service.py`) y en el Planificador y el Revisor
(`planificacion/service.py`); el texto de sus prompts, el del extractor, el bloque inmutable del
Escritor y el juicio de obra (`novela.py`), la rúbrica del Editor (`ciclo.py`), los prompts de la
puerta (`publicacion.py`) y las objeciones de la cobertura. **Prueba que falla primero:** en
`test_ningun_nombre_real_sale`, `ninguna palabra del regalo llega a los agentes`.

### Q3 · Las definiciones (`RF-02`)

`.claude/agents/`: entrevistador, planificador, revisor_plan, escritor, editor, juez y
resumidor. **Prueba que falla primero:**
`test_ninguna_definicion_de_agente_habla_del_regalo`.

### Q4 · `docs/`

`VER-142`, `F-146` con lo que se vio en real, `AGENTS.md` y `SPEC-40` a `aplicada`. La prueba
real barata queda para el autor.
