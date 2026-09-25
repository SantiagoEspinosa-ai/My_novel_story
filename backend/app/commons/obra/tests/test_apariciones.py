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


def test_con_dos_versiones_cada_capitulo_sale_una_vez_y_es_el_de_la_vigente():
    """`F-203`: con varias versiones, las fichas repetian cada capitulo una vez por
    version (en la demo, «Capitulo 4» tres veces), porque se leia la tabla `capitulo`
    entera. Es la misma familia que `F-132` y `F-150`: se leen los de la **vigente**."""
    from app.commons.db import migraciones
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    c.executescript(migraciones.VEREDICTO_SQL)
    c.execute("CREATE TABLE IF NOT EXISTS capitulo (id TEXT, obra TEXT, orden INTEGER, "
              "estado TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS escena (id TEXT, obra TEXT, orden INTEGER, "
              "capitulo TEXT, lugar TEXT, personajes_presentes TEXT)")
    for cap, orden in (("c1", 1), ("c2", 2), ("c2-v2", 2), ("c3", 3)):
        c.execute("INSERT INTO capitulo (id, obra, orden, estado) VALUES (?, 'o', ?, "
                  "'abierto')", (cap, orden))
        c.execute("INSERT INTO escena VALUES (?, 'o', 1, ?, 'l1', ?)",
                  (cap + "-e1", cap, json.dumps(["p1"])))
    for numero, caps in ((1, ["c1", "c2", "c3"]), (2, ["c1", "c2-v2", "c3"])):
        c.execute("INSERT INTO version_de_obra (obra, numero, \"commit\") VALUES ('o', ?, 'x')",
                  (numero,))
        for orden, cap in enumerate(caps, start=1):
            c.execute("INSERT INTO capitulo_de_version VALUES ('o', ?, ?, ?)",
                      (numero, orden, cap))
    personajes, _ = apariciones.de_personajes(c, "o")
    assert [x["id"] for x in personajes["p1"]] == ["c1", "c2", "c3"], "la 2 sin publicar"
    c.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
              "condiciones, no_ejecutadas) VALUES ('o', 2, 1, 1, '[]', '[]')")
    personajes, _ = apariciones.de_personajes(c, "o")
    assert [x["id"] for x in personajes["p1"]] == ["c1", "c2-v2", "c3"]
    assert [x["orden"] for x in personajes["p1"]] == [1, 2, 3]
    assert [x["id"] for x in apariciones.de_lugares(c, "o")["l1"]] == ["c1", "c2-v2", "c3"]
