"""Los capitulos donde aparece una entidad, calculados en un solo sitio."""

import json
import sqlite3

import pytest

from app.commons.obra import apariciones


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE capitulo (id TEXT, obra TEXT, orden INTEGER)")
    c.execute("CREATE TABLE escena (id TEXT, obra TEXT, orden INTEGER, capitulo TEXT, "
              "lugar TEXT, personajes_presentes TEXT)")
    c.executemany("INSERT INTO capitulo VALUES (?, ?, ?)",
                  [("cap-02", "o", 1), ("cap-01", "o", 2), ("cap-x", "p", 1)])
    filas = [("e1", "o", 1, "cap-01", "l1", ["p1"]), ("e2", "o", 1, "cap-02", "l1", ["p1"]),
             ("e3", "p", 1, "cap-x", "l1", ["p1"])]
    for fila in filas:
        c.execute("INSERT INTO escena VALUES (?, ?, ?, ?, ?, ?)",
                  fila[:5] + (json.dumps(fila[5]),))
    return c


def test_por_orden_de_capitulo_y_sin_otra_obra(con):
    lugares = apariciones.de_lugares(con, "o")
    assert [c["id"] for c in lugares["l1"]] == ["cap-02", "cap-01"]
    personajes, declarados = apariciones.de_personajes(con, "o")
    assert declarados
    assert [c["id"] for c in personajes["p1"]] == ["cap-02", "cap-01"]


def test_una_escena_sin_presentes_deja_las_listas_sin_declarar(con):
    con.execute("INSERT INTO escena VALUES ('e4', 'o', 2, 'cap-01', 'l1', NULL)")
    assert apariciones.de_personajes(con, "o")[1] is False
