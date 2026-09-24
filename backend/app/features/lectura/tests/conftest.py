"""Una base con **dos obras**, y la primera con **dos capitulos**, para toda la lectura.

Regla 11 y `SPEC-22` `NF-05`: con un capitulo por obra, una consulta que pregunte por obra
devuelve lo correcto y la prueba no distingue nada. Los identificadores de capitulo se
eligen para que su orden alfabetico sea **el contrario** del de lectura (`cap-b` va
primero), y ninguno coincide con el de una obra. Todo es inventado.
"""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app, preparar_base

OBRA = "obra-inventada"
OTRA = "obra-ajena"
DATOS = {"titulo": "Titulo inventado", "premisa": "Premisa inventada",
         "dedicatoria": "Para nadie real"}
TEXTO_ELEGIDO = "Primer texto  inventado,\ncon dos espacios y el elegido.\n"


def _escena(con, id_escena, obra, orden, capitulo, estado, lugar="lug-faro",
            presentes=None, aceptado=None):
    con.execute(
        "INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, beats, pov, lugar, "
        "capitulo, personajes_presentes, borrador_aceptado) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (id_escena, obra, orden, estado, json.dumps({"eje": "seguridad", "signo": "negativo"}),
         json.dumps(["b1"]), "per-uno", lugar, capitulo,
         json.dumps(presentes) if presentes is not None else None, aceptado))


def _borrador(con, escena, version, texto):
    con.execute("INSERT INTO borrador (escena, version, texto, modelo, prompt_hash) "
                "VALUES (?, ?, ?, 'doble', 'h')", (escena, version, texto))


def _hallazgo(con, invariante, verificador, escena, severidad, estado, descripcion):
    con.execute("INSERT INTO hallazgo (invariante, verificador, escena, severidad, estado, "
                "descripcion) VALUES (?, ?, ?, ?, ?, ?)",
                (invariante, verificador, escena, severidad, estado, descripcion))


def sembrar(ruta):
    """Por SQL y no con los repositorios de `brief/` y `escaleta/`: una feature no importa
    de otra, tampoco en sus pruebas (`A-02`, `test_una_feature_no_importa_de_otra_feature`).
    Que los que escriben dejan esta forma lo comprueba la semilla de `PLAN-22` E11, que
    monta la obra con `novela.montar` y la lee por esta misma API."""
    con = preparar_base(ruta)
    with con:
        con.execute("INSERT INTO obra (id, titulo, premisa, dedicatoria) VALUES (?, ?, ?, ?)",
                    (OBRA, DATOS["titulo"], DATOS["premisa"], DATOS["dedicatoria"]))
        con.execute("INSERT INTO obra (id, titulo, premisa) VALUES (?, 'Otra', 'Otra')", (OTRA,))
        # `cap-b` es el primero en leerse y `cap-a` el segundo: ordenar por id los invierte.
        for id_c, obra, orden in (("cap-b", OBRA, 1), ("cap-a", OBRA, 2), ("cap-z", OTRA, 1)):
            con.execute("INSERT INTO capitulo (id, obra, orden, estado) VALUES (?, ?, ?, 'abierto')",
                        (id_c, obra, orden))
        # esc-b1: consolidada, con un texto elegido que no es el ultimo.
        _escena(con, "esc-b1", OBRA, 1, "cap-b", "consolidada", lugar="lug-casa",
                presentes=["per-uno", "per-dos"], aceptado=1)
        _borrador(con, "esc-b1", 1, TEXTO_ELEGIDO)
        _borrador(con, "esc-b1", 2, "Un intento posterior que nadie eligio.")
        # esc-b2: rendida (y consolidada: una rendida no pasa a consolidada), con un mayor.
        _escena(con, "esc-b2", OBRA, 2, "cap-b", "aceptada_por_rendicion",
                presentes=["per-uno"], aceptado=1)
        _borrador(con, "esc-b2", 1, "Texto rendido inventado.")
        _hallazgo(con, "INV-17", "regla", "esc-b2", "mayor", "abierto",
                  "fuera de rango (inventado)")
        # esc-a1: generada, presentes sin declarar, un sin_veredicto y un resuelto.
        _escena(con, "esc-a1", OBRA, 1, "cap-a", "generada")
        _borrador(con, "esc-a1", 1, "Texto generado inventado.")
        _hallazgo(con, "INV-27", "juez_llm", "esc-a1", "mayor", "sin_veredicto",
                  "el juez no contesto (inventado)")
        _hallazgo(con, "INV-03", "regla", "esc-a1", "bloqueante", "resuelto",
                  "ya arreglado (inventado)")
        # esc-a2: planificada, sin ningun borrador.
        _escena(con, "esc-a2", OBRA, 2, "cap-a", "planificada", presentes=[])
        # La otra obra: un capitulo, una escena en el mismo lugar que esc-b1.
        _escena(con, "esc-z1", OTRA, 1, "cap-z", "generada", lugar="lug-casa",
                presentes=["per-dos"])
        _borrador(con, "esc-z1", 1, "Texto de la otra obra.")
    con.close()


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "lectura.db")
    sembrar(ruta)
    anterior = getattr(app.state, "ruta_db", None)
    app.state.ruta_db = ruta
    try:
        yield TestClient(app)
    finally:
        app.state.ruta_db = anterior


@pytest.fixture
def ruta_sembrada(tmp_path):
    ruta = str(tmp_path / "lectura.db")
    sembrar(ruta)
    return ruta

