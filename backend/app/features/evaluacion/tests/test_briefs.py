"""`PLAN-31` E1: el formato de los briefs de evaluacion (`SPEC-31` `RF-01`).

Cada brief lleva `_meta`, una ficha **o** un guion de entrevista —nunca las dos— y
`que_deberia_pasar`. Punto ciego declarado: «inventados» es una declaracion del fichero,
no algo que esta prueba pueda comprobar.
"""

import json
import pathlib

import pytest

from app.features.evaluacion import briefs

EVALS = pathlib.Path(__file__).resolve().parents[5] / "harness" / "evals"


def _ficheros():
    return sorted(EVALS.glob("brief-*.json"))


def _datos_de(nombre):
    return json.loads((EVALS / nombre).read_text(encoding="utf-8"))


def test_cada_brief_de_harness_evals_carga_con_su_esquema():
    assert _ficheros(), "no hay ningun brief en harness/evals"
    for ruta in _ficheros():
        b = briefs.cargar(ruta)
        assert b.meta.id == ruta.stem, ruta.name
        assert (b.ficha is None) != (b.guion is None), ruta.name
        assert b.que_deberia_pasar, ruta.name


def test_un_brief_sin_datos_inventados_declarados_no_carga():
    datos = _datos_de("brief-incoherencia-temporal.json")
    del datos["_meta"]["datos"]
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)
    datos["_meta"]["datos"] = "reales"
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)


def test_un_brief_con_ficha_y_guion_a_la_vez_no_carga():
    datos = _datos_de("brief-incoherencia-temporal.json")
    datos["guion"] = {"turnos": [{"respuesta": "se llama Ana"}, {"cerrar": True}]}
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)


def test_un_brief_sin_ficha_ni_guion_no_carga():
    datos = _datos_de("brief-incoherencia-temporal.json")
    del datos["ficha"]
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)


def test_el_brief_temporal_es_una_ficha_de_misterio_y_conserva_sus_ganchos():
    b = briefs.cargar(EVALS / "brief-incoherencia-temporal.json")
    assert b.ficha.genero.value == "misterio"
    assert set(b.por_que_provoca_cada_incoherencia) == {"L-1", "L-2", "L-3", "L-4"}
