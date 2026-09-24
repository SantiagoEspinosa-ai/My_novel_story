"""Una base con dos novelas regalo de diez capitulos, para las lecturas de `features/regalo/`.

Se siembra **por SQL**, como `lectura/tests/`: una feature no importa de otra, tampoco en sus
pruebas (`test_una_feature_no_importa_de_otra_feature`). Los datos son **inventados**. Hay
dos obras a proposito, con identificadores de capitulo que no coinciden con su orden: una
lectura que no filtrara por obra, o que ordenara por id, pasaria con una sola.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app, preparar_base

OBRA = "obra-regalo-a"
OTRA = "obra-regalo-b"
CRITERIOS = ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion")


def id_capitulo(obra, numero):
    # El id ordena al reves que el orden de lectura (Regla 11).
    return "{0}-cap-{1:02d}".format(obra, 11 - numero)


def id_escena(obra, numero):
    return id_capitulo(obra, numero) + "-e1"


def montar(con, obra, titulo="El mapa de Irene", dedicatoria=None):
    with con:
        con.execute("INSERT INTO obra (id, titulo, premisa, dedicatoria) VALUES (?, ?, ?, ?)",
                    (obra, titulo, "Una premisa inventada.", dedicatoria))
        for n in range(1, 11):
            con.execute("INSERT INTO capitulo (id, obra, orden, estado) VALUES (?, ?, ?, "
                        "'abierto')", (id_capitulo(obra, n), obra, n))
            con.execute("INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, beats, "
                        "pov, lugar, capitulo) VALUES (?, ?, 1, 'planificada', '{}', '[]', "
                        "'per-x', 'lug-x', ?)", (id_escena(obra, n), obra, id_capitulo(obra, n)))


def fijar_fase(con, obra, fase, capitulo=None, total=10, motivo=None):
    with con:
        con.execute("INSERT INTO progreso_de_generacion (obra, fase, capitulo, "
                    "total_de_capitulos, motivo) VALUES (?, ?, ?, ?, ?)",
                    (obra, fase, capitulo, total, motivo))


def valorar(con, escena, version, notas):
    with con:
        for c, n in zip(CRITERIOS, notas):
            con.execute("INSERT INTO valoracion_del_editor (escena, version, criterio, nota, "
                        "justificacion, instruccion) VALUES (?, ?, ?, ?, ?, '')",
                        (escena, version, c, n, "porque " + c))


def aceptar(con, escena, version):
    with con:
        con.execute("UPDATE escena SET estado = 'aceptada', borrador_aceptado = ? WHERE id = ?",
                    (version, escena))


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "regalo.db")
    con = preparar_base(r)
    montar(con, OBRA, dedicatoria="Para Irene, que siempre llega.")
    montar(con, OTRA, titulo="La otra novela")
    con.close()
    return r


@pytest.fixture
def con(ruta):
    c = sqlite3.connect(ruta)
    yield c
    c.close()


@pytest.fixture
def cliente(ruta):
    app.state.ruta_db = ruta
    return TestClient(app)
