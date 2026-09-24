"""`SPEC-33` `RF-11`, `RF-13`, `PLAN-33` E11: lanzar una generacion desde la web.

Lanzar arranca un trabajo y devuelve su identificador; no bloquea (`CLAUDE.md`). Es el
mismo pipeline que `novela_regalo.py`: `novela.escribir` con `regalo.agentes`. El backend
impone las tres reglas -entrevista cerrada, una sola a la vez, el techo-; el boton de la web
es su cara visible, no la regla. Las sesiones son `SesionDelegada` con un proceso doble.
"""

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.modelo import gasto
from app.commons.trabajos import cola
from app.features.entrevista import repository as entrevistas
from app.features.entrevista.tests.conftest import ficha_completa
from app.features.orquestacion import regalo
from app.features.orquestacion.tests.test_novela import (
    _agentes_para_la_novela_entera, _LeanFijo)
from app.features.orquestacion.tests.test_regalo import _proceso
from app.main import app, preparar_base


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "web.db")
    preparar_base(r).close()
    app.state.ruta_db = r
    app.state.agentes_regalo = lambda sistema, entorno, anotar: regalo.agentes(
        sistema, entorno, anotar=anotar, ejecutar=_proceso(_agentes_para_la_novela_entera()))
    app.state.lean_regalo = _LeanFijo()
    yield r
    del app.state.agentes_regalo
    del app.state.lean_regalo


@pytest.fixture
def cliente(ruta):
    return TestClient(app)


def _entrevista(ruta, cerrada=True):
    con = sqlite3.connect(ruta)
    e = entrevistas.crear(con)
    e.ficha = ficha_completa()
    e.cerrada = cerrada
    entrevistas.guardar(con, e)
    con.close()
    return e


def _lanzar(cliente, obra):
    return cliente.post("/obras/{0}/generaciones".format(obra))


def test_lanzar_devuelve_un_trabajo_y_no_bloquea(cliente, ruta):
    e = _entrevista(ruta)
    r = _lanzar(cliente, e.obra)
    assert r.status_code == 202, r.text
    t = cliente.get("/trabajos/" + r.json()["id_trabajo"]).json()
    assert t["tipo"] == "generacion_regalo"
    assert t["estado"] == "terminado", t["motivo"]
    assert r.json()["generacion"].startswith("gen-")


def test_la_generacion_anota_su_gasto_con_su_identificador(cliente, ruta):
    e = _entrevista(ruta)
    generacion = _lanzar(cliente, e.obra).json()["generacion"]
    con = sqlite3.connect(ruta)
    filas = con.execute("SELECT DISTINCT obra, generacion FROM gasto_de_delegacion").fetchall()
    assert filas == [(e.obra, generacion)]


def test_sin_entrevista_cerrada_es_409_con_motivo(cliente, ruta):
    e = _entrevista(ruta, cerrada=False)
    r = _lanzar(cliente, e.obra)
    assert r.status_code == 409
    assert "cerrada" in r.json()["detail"]
    assert _lanzar(cliente, "obra-sin-entrevista").status_code == 409


def test_una_segunda_generacion_en_curso_es_409(cliente, ruta):
    e = _entrevista(ruta)
    con = sqlite3.connect(ruta)
    id_t = cola.encolar(con, "generacion_regalo", {"obra": e.obra})
    cola.tomar(con, id_t)
    con.close()
    r = _lanzar(cliente, e.obra)
    assert r.status_code == 409
    assert "en curso" in r.json()["detail"]


def test_con_lo_gastado_en_el_techo_es_409_con_motivo(cliente, ruta):
    e = _entrevista(ruta)
    con = sqlite3.connect(ruta)
    gasto.anotador(con, "otra-obra", "gen-vieja")("escritor", 50.0)
    con.close()
    r = _lanzar(cliente, e.obra)
    assert r.status_code == 409
    assert "techo" in r.json()["detail"] and "50" in r.json()["detail"]


def test_una_generacion_que_falla_deja_su_motivo_en_el_trabajo(cliente, ruta):
    e = _entrevista(ruta)

    def revienta(*a, **k):
        raise RuntimeError("el proceso no arranco")

    app.state.agentes_regalo = lambda sistema, entorno, anotar: regalo.agentes(
        sistema, entorno, anotar=anotar, ejecutar=revienta)
    t = cliente.get("/trabajos/" + _lanzar(cliente, e.obra).json()["id_trabajo"]).json()
    assert t["estado"] == "fallido"
    assert t["motivo"]
