"""`PLAN-40` Q1 (`SPEC-40`): la vista de la ficha que ven los agentes. Datos inventados."""

import json

from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.politica import vista_de_agentes as vista


def _ficha():
    return FichaDeEntrevista.model_validate({
        "destinatario": {"nombre": "Olivia Carranza", "edad": 9, "elementos": [
            {"tipo": "mascota", "descripcion": "su perro", "nombre": "Tino"}]},
        "regalado_por": "Ramón", "dedicatoria": "Para Olivia", "nombres_vetados": ["Marcos"],
        "genero": "aventura", "vetadas": ["hospital"]})


def test_la_vista_lleva_al_protagonista_y_nada_del_regalo():
    v = vista.ficha_para_agentes(_ficha())
    assert v["protagonista"]["nombre"] == "Olivia Carranza"
    for fuera in ("destinatario", "regalado_por", "dedicatoria", "nombres_vetados"):
        assert fuera not in v, fuera
    assert v["genero"] == "aventura" and v["vetadas"] == ["hospital"]
    assert not vista.PALABRAS_DEL_REGALO.search(json.dumps(v, ensure_ascii=False))


def test_una_ficha_con_protagonista_se_lee_como_destinatario():
    v = vista.ficha_para_agentes(_ficha())
    d = vista.ficha_desde_agentes(v)
    assert d["destinatario"]["nombre"] == "Olivia Carranza" and "protagonista" not in d
    # Una ficha que ya viene con `destinatario` (un doble, un guion) se deja tal cual.
    assert vista.ficha_desde_agentes({"destinatario": {"nombre": "X"}}) == {"destinatario": {"nombre": "X"}}


def test_la_guarda_caza_las_palabras_del_regalo():
    for texto in ("para regalar", "el Destinatario", "la dedicatoria", "el comprador", "regalo"):
        assert vista.PALABRAS_DEL_REGALO.search(texto), texto
    assert not vista.PALABRAS_DEL_REGALO.search("la protagonista encarga un mapa")
