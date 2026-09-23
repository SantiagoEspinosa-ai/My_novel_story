"""`PLAN-26` E11: los agentes del pipeline y su configuracion."""

import json
import pathlib
import re

from app.commons.configuracion import carga

AGENTES = pathlib.Path(__file__).resolve().parents[5] / ".claude" / "agents"
DEL_PIPELINE = ["escritor", "juez", "resumidor", "entrevistador", "planificador",
                "revisor_plan", "editor"]


def _cabecera(nombre):
    texto = (AGENTES / (nombre + ".md")).read_text(encoding="utf-8")
    return texto, re.search(r"^---\n(.*?)\n---", texto, re.S).group(1)


def test_cada_agente_del_pipeline_existe_y_no_tiene_herramientas():
    """`SPEC-26` `RF-18`: el hook de policy es la segunda linea; la primera es
    que ninguno declare herramientas."""
    for nombre in DEL_PIPELINE:
        _, cabecera = _cabecera(nombre)
        assert "name: " + nombre in cabecera
        assert "tools: []" in cabecera, nombre


def test_solo_el_juez_de_terror_habla_de_terror():
    """`RF-20`: el genero llega en el prompt, no en la definicion del agente."""
    con_terror = [n for n in DEL_PIPELINE
                  if "terror" in _cabecera(n)[0].lower()]
    assert con_terror == ["juez"]


def test_el_editor_sabe_hacer_el_juicio_de_obra():
    texto, _ = _cabecera("editor")
    assert "arco_cerrado" in texto and "final_abrupto" in texto


def test_el_sistema_carga_los_modelos_y_topes_nuevos():
    s = carga.cargar_sistema()
    assert s.modelos.planificador and s.modelos.revisor_plan and s.modelos.editor
    assert s.topes.revisiones_de_plan == 3
    assert s.topes.reescrituras_del_editor == 3
    assert s.edicion.umbral_del_editor == 3
    assert s.edicion.umbral_repeticion_nombre == 12
    assert s.edicion.longitud_frase_repetida == 8
