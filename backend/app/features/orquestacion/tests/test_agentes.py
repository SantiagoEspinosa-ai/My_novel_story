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


def test_solo_el_escritor_y_el_editor_declaran_herramientas_y_son_las_permitidas():
    """`SPEC-28` `RF-03`: el Escritor y el Editor declaran sus tres tools de lectura de
    la story bible y nada mas; el resto sigue con `tools: []`. El frontmatter es la
    ultima de cuatro barreras (`PLAN-28` `D-2`): no se confia solo en el."""
    from app.commons.politica.herramientas import PERMITIDAS
    for nombre in DEL_PIPELINE:
        _, cabecera = _cabecera(nombre)
        assert "name: " + nombre in cabecera
        if nombre in PERMITIDAS:
            assert "tools: " + ", ".join(PERMITIDAS[nombre]) in cabecera, nombre
        else:
            assert "tools: []" in cabecera, nombre


def test_el_escritor_sabe_que_el_delta_sigue_en_su_respuesta():
    """`RF-04`: las tools son de solo lectura; el delta no se escribe con una tool."""
    cuerpo, _ = _cabecera("escritor")
    assert "solo lectura" in cuerpo and "delta" in cuerpo


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
