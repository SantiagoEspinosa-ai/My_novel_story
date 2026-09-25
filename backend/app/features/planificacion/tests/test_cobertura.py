"""`SPEC-26` `RF-06`: lo que se comprueba del plan sin juicio.

Cada condicion tiene su plan roto y su hueco nombrado. Un hueco con un mensaje
vago devuelve al Planificador sin decirle que arreglar, y vuelve a fallar igual.
"""

import pytest
from pydantic import ValidationError

from app.features.planificacion.cobertura import huecos
from app.features.planificacion.tests.conftest import ficha, plan, plan_dict


def test_un_plan_correcto_no_tiene_huecos():
    assert huecos(plan(), ficha()) == []


def test_menos_de_diez_capitulos_es_un_hueco():
    assert any("10 capitulos" in h for h in huecos(
        plan(capitulos=plan_dict()["capitulos"][:9]), ficha()))


def test_un_capitulo_con_dos_escenas_es_un_hueco():
    caps = plan_dict()["capitulos"]
    caps[3]["escenas"] = caps[3]["escenas"] * 2
    assert any("cap-04" in h and "una escena" in h
               for h in huecos(plan(capitulos=caps), ficha()))


def test_un_imprescindible_de_la_ficha_sin_asignar_es_un_hueco():
    imps = plan_dict()["imprescindibles"][:2]
    assert huecos(plan(imprescindibles=imps), ficha()) == [
        "el imprescindible «un galgo muy lento» no tiene capitulo en el plan"]


def test_un_imprescindible_sin_palabras_clave_no_se_puede_declarar():
    imps = plan_dict()["imprescindibles"]
    imps[0] = dict(imps[0], palabras_clave=[])
    with pytest.raises(ValidationError):
        plan(imprescindibles=imps)


def test_un_imprescindible_en_un_capitulo_que_no_existe_no_se_puede_declarar():
    imps = plan_dict()["imprescindibles"]
    imps[0] = dict(imps[0], capitulo="cap-99")
    with pytest.raises(ValidationError):
        plan(imprescindibles=imps)


def test_el_destinatario_con_otro_nombre_es_un_hueco():
    d = plan_dict()
    d["mundo"]["personajes"][0]["nombre"] = "Irena Valdés"
    hs = huecos(plan(mundo=d["mundo"]), ficha())
    # `SPEC-40` `RF-03`: la objecion vuelve al Planificador, y ahi es «el protagonista».
    assert any("Irene Valdés" in h and "protagonista" in h for h in hs)


def test_una_mascota_imprescindible_mal_escrita_es_un_hueco():
    d = plan_dict()
    d["mundo"]["personajes"][1]["nombre"] = "Brissa"
    assert any("Brisa" in h for h in huecos(plan(mundo=d["mundo"]), ficha()))


def test_una_palabra_vetada_en_el_plan_es_un_hueco():
    caps = plan_dict()["capitulos"]
    caps[6]["escenas"][0]["sinopsis"] = "Irene acaba en el hospital."
    assert any("hospital" in h and "cap-07" in h
               for h in huecos(plan(capitulos=caps), ficha()))


def test_un_nombre_vetado_en_el_plan_es_un_hueco():
    caps = plan_dict()["capitulos"]
    caps[2]["escenas"][0]["sinopsis"] = "Aparece Tomas."
    assert any("Tomas" in h for h in huecos(plan(capitulos=caps), ficha()))


def test_una_exclusion_prevista_de_un_personaje_que_no_existe_no_se_declara():
    with pytest.raises(ValidationError):
        plan(exclusiones_previstas=[{"personaje": "per-nadie", "capitulo": "cap-09",
                                     "estado_vital": "muerto"}])
