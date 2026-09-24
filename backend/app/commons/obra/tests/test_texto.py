"""La regla del texto elegido, en un solo sitio (`PLAN-22` DP-5).

La que dice `Escena.borrador_aceptado`; si no consta, la ultima. La necesitan la lectura
web y el manuscrito, y dos copias divergen.
"""

import sqlite3

import pytest

from app.commons.obra import texto


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE borrador (escena TEXT, version INTEGER, texto TEXT, "
              "modelo TEXT, prompt_hash TEXT, PRIMARY KEY (escena, version))")
    for v, t in ((1, "uno"), (2, "dos"), (3, "tres")):
        c.execute("INSERT INTO borrador VALUES ('e1', ?, ?, 'x', 'h')", (v, t))
    return c


def test_el_elegido_manda_sobre_el_ultimo(con):
    assert texto.elegido(con, "e1", 2) == texto.Elegido(version=2, texto="dos")


def test_sin_elegido_el_ultimo(con):
    assert texto.elegido(con, "e1", None) == texto.Elegido(version=3, texto="tres")


def test_un_elegido_que_no_existe_cae_al_ultimo(con):
    assert texto.elegido(con, "e1", 9).version == 3


def test_sin_borradores_no_hay_texto(con):
    assert texto.elegido(con, "e2", None) is None
