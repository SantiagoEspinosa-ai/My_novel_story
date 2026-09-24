"""`SPEC-33` `RF-01`..`RF-03`, `PLAN-33` E13: la estanteria.

Todas las obras de la base, cada una con su portada (titulo y dedicatoria), el nombre del
destinatario y su estado. El estado es la ultima fase de progreso, o nada: una obra sin
generacion no tiene una fase inventada. Con la ficha borrada, el destinatario falta y la
dedicatoria sigue, porque es de la obra (`SPEC-32`).
"""

import json

from app.features.regalo.tests.conftest import OBRA, OTRA, fijar_fase


def _entrevista(con, obra, nombre, cerrada=True, id_e="ent-a"):
    ficha = {"destinatario": {"nombre": nombre, "edad": 34, "elementos": []}}
    with con:
        con.execute("INSERT INTO entrevista (id, obra, ficha, cerrada) VALUES (?, ?, ?, ?)",
                    (id_e, obra, json.dumps(ficha), int(cerrada)))


def _estanteria(cliente):
    r = cliente.get("/obras")
    assert r.status_code == 200, r.text
    return {o["id"]: o for o in r.json()["obras"]}


def test_la_estanteria_trae_todas_las_obras(cliente, con):
    _entrevista(con, OBRA, "Irene Valdés")
    obras = _estanteria(cliente)
    assert set(obras) == {OBRA, OTRA}
    a = obras[OBRA]
    assert (a["titulo"], a["dedicatoria"], a["destinatario"]) == (
        "El mapa de Irene", "Para Irene, que siempre llega.", "Irene Valdés")
    assert (a["entrevista"], a["entrevista_cerrada"]) == ("ent-a", True)


def test_el_estado_es_la_ultima_fase(cliente, con):
    fijar_fase(con, OBRA, "escribiendo", 2)
    fijar_fase(con, OBRA, "publicada")
    fijar_fase(con, OTRA, "parada", 3, motivo="FalloDeTransporte")
    obras = _estanteria(cliente)
    assert obras[OBRA]["fase"] == "publicada" and obras[OTRA]["fase"] == "parada"


def test_una_obra_sin_progreso_viene_sin_estado(cliente):
    assert _estanteria(cliente)[OBRA]["fase"] is None


def test_con_la_ficha_borrada_el_destinatario_viene_ausente_y_la_dedicatoria_sigue(cliente):
    a = _estanteria(cliente)[OBRA]
    assert a["destinatario"] is None and a["entrevista"] is None
    assert a["dedicatoria"] == "Para Irene, que siempre llega."


def test_una_obra_que_solo_tiene_entrevista_tambien_esta(cliente, con):
    """Al pulsar «Generar novela» nace una entrevista con su obra, que aun no esta montada:
    tiene que verse en la estanteria para poder volver a ella."""
    _entrevista(con, "obra-nueva", "Nerea", cerrada=False, id_e="ent-n")
    n = _estanteria(cliente)["obra-nueva"]
    assert (n["titulo"], n["destinatario"], n["entrevista_cerrada"]) == (None, "Nerea", False)
