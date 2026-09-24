"""`PLAN-22` E14 — lo que la pagina necesita para pedir un cambio (`VER-110`).

Al seleccionar un fragmento, la pagina ofrece **los hechos que usa esa escena**
(`uso_de_hecho`, `SPEC-21` C-2) con su enunciado, y **los personajes presentes**; el
lector elige uno y lo que viaja al backend es el hecho o el personaje, no el ancla de
texto (`PLAN-22` reparto con `PLAN-23`).

Datos inventados. El mismo `id` de hecho existe en **dos obras** con enunciados
distintos, a proposito: una consulta que no filtre por la obra de la escena devolveria
los dos, y con un solo hecho por id la prueba no lo distinguiria (Regla 11).
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.features.lectura.tests.conftest import OBRA, OTRA, sembrar
from app.main import app


def _hechos_y_usos(ruta):
    con = sqlite3.connect(ruta)
    with con:
        for id_h, obra, enunciado in (
                ("hec-faro", OBRA, "El faro existe (inventado)."),
                ("hec-llave", OBRA, "La llave abre el faro (inventado)."),
                ("hec-sin-usar", OBRA, "Nadie lo usa (inventado)."),
                ("hec-faro", OTRA, "Otro faro, de la otra obra (inventado).")):
            con.execute("INSERT INTO hecho_canonico (id, obra, enunciado) VALUES (?, ?, ?)",
                        (id_h, obra, enunciado))
        # esc-b1 usa hec-faro dos veces (dos tipos) y hec-llave una. esc-z1, de la otra
        # obra, usa su propio hec-faro. esc-a2 no usa ninguno.
        for hecho, escena, capitulo, tipo in (
                ("hec-faro", "esc-b1", "cap-b", "establece"),
                ("hec-faro", "esc-b1", "cap-b", "depende"),
                ("hec-llave", "esc-b1", "cap-b", "menciona"),
                ("hec-faro", "esc-z1", "cap-z", "menciona")):
            con.execute("INSERT INTO uso_de_hecho (hecho, escena, capitulo, tipo, origen) "
                        "VALUES (?, ?, ?, ?, 'regla')", (hecho, escena, capitulo, tipo))
    con.close()


@pytest.fixture
def cliente_con_hechos(tmp_path):
    ruta = str(tmp_path / "lectura.db")
    sembrar(ruta)
    _hechos_y_usos(ruta)
    anterior = getattr(app.state, "ruta_db", None)
    app.state.ruta_db = ruta
    try:
        yield TestClient(app)
    finally:
        app.state.ruta_db = anterior


def test_los_hechos_de_una_escena_son_los_de_sus_usos_y_de_su_obra(cliente_con_hechos):
    r = cliente_con_hechos.get("/escenas/esc-b1/hechos")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["escena"] == "esc-b1"
    # Uno por hecho aunque se use con dos tipos; con el enunciado de **su** obra, y sin
    # el hecho que ninguna escena usa.
    assert cuerpo["hechos_que_usa"] == [
        {"id": "hec-faro", "enunciado": "El faro existe (inventado)."},
        {"id": "hec-llave", "enunciado": "La llave abre el faro (inventado)."},
    ]
    otra = cliente_con_hechos.get("/escenas/esc-z1/hechos").json()
    assert otra["hechos_que_usa"] == [
        {"id": "hec-faro", "enunciado": "Otro faro, de la otra obra (inventado)."}]


def test_una_escena_sin_usos_devuelve_una_lista_vacia_y_no_nula(cliente_con_hechos):
    cuerpo = cliente_con_hechos.get("/escenas/esc-a2/hechos").json()
    assert cuerpo == {"escena": "esc-a2", "hechos_que_usa": []}


def test_los_hechos_de_una_escena_que_no_existe_son_404(cliente_con_hechos):
    assert cliente_con_hechos.get("/escenas/no-existe/hechos").status_code == 404
    # Un id de capitulo no es una escena (`RF-37`).
    assert cliente_con_hechos.get("/escenas/cap-b/hechos").status_code == 404


def test_la_escena_trae_sus_personajes_presentes_y_sin_declarar_es_nulo(cliente_con_hechos):
    """Los que la pagina ofrece para renombrar. `[]` es «no hay nadie»; `None`, «no se
    declaro», que no es lo mismo (`RF-44`)."""
    assert cliente_con_hechos.get("/escenas/esc-b1").json()["personajes_presentes"] == [
        "per-uno", "per-dos"]
    assert cliente_con_hechos.get("/escenas/esc-a2").json()["personajes_presentes"] == []
    assert cliente_con_hechos.get("/escenas/esc-z1").json()["personajes_presentes"] is None
