"""`PLAN-29` E4: los prompts, del repositorio a Langfuse (`SPEC-29` `RF-05`, `RF-13`)."""

import sqlite3

from app.commons.modelo.proveedor import RAIZ_DEL_REPOSITORIO
from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.commons.observabilidad.observacion import Observacion
from app.features.orquestacion import prompts

# `inspector_visual` entra con `PLAN-22` E13b (`INV-30`): es un agente con prompt propio y
# su version sube como la de los demas.
ROLES_DEL_PIPELINE = {"entrevistador", "planificador", "revisor_plan", "escritor", "editor",
                      "juez", "resumidor", "inspector_visual"}


def test_cada_agente_del_pipeline_tiene_su_version_de_prompt():
    r = prompts.registro()
    assert set(r) == ROLES_DEL_PIPELINE
    for rol, v in r.items():
        assert v.rol == rol and len(v.version) == 12
        int(v.version, 16)


def test_cada_fichero_de_claude_agents_esta_en_el_registro():
    ficheros = {p.stem for p in (RAIZ_DEL_REPOSITORIO / ".claude" / "agents").glob("*.md")}
    assert ficheros and ficheros == set(prompts.registro())


def test_la_version_cambia_si_cambia_una_coma_y_no_si_no_cambia():
    a = prompts.huella("Eres el escritor, y escribes.")
    assert a == prompts.huella("Eres el escritor, y escribes.")
    assert a != prompts.huella("Eres el escritor y escribes.")


def test_lo_que_sube_es_la_plantilla_sin_rellenar():
    from app.features.planificacion.service import PROMPT_PLANIFICADOR
    v = prompts.registro()["planificador"]
    assert PROMPT_PLANIFICADOR in v.plantilla
    assert "{" in PROMPT_PLANIFICADOR, "la prueba solo vale si la plantilla tiene huecos"
    definicion = (RAIZ_DEL_REPOSITORIO / ".claude" / "agents" / "planificador.md").read_text(
        encoding="utf-8")
    assert definicion in v.plantilla


def test_una_version_ya_enviada_no_se_reenvia():
    con = sqlite3.connect(":memory:")
    obs = Observacion(ExportadorEnMemoria(), con=con, obra="obra-a")
    primeras = prompts.enviar_nuevas(con, obs)
    segundas = prompts.enviar_nuevas(con, obs)
    enviadas = [e for t, e in obs.exportador.enviados if t == "prompt"]
    assert primeras == len(ROLES_DEL_PIPELINE) == len(enviadas)
    assert segundas == 0
