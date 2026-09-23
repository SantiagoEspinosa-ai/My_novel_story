"""`SPEC-25` `RF-21`, `PLAN-25` E11: entregar borra la entrevista, no la novela.

Se conservan las vetadas de la novela y los hechos de la story bible, porque
las regeneraciones que pide el lector ocurren **despues** de la entrega y sin
ellos una regeneracion podria volver a meter el nombre de una expareja.
"""

import json
import sqlite3

import pytest

from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.politica import auditoria
from app.features.entrevista import repository as repo_entrevista
from app.features.entrevista import service as entrevista
from app.features.entrevista.tests.conftest import ficha_completa
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import entrega
from app.features.politica import repository as politica

CONVERSACION = "Mi hermana Irene odia los lunes"


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo_entrevista.asegurar_tablas(c)
    politica.asegurar_tablas(c)
    escaleta.asegurar_tablas(c)
    return c


@pytest.fixture
def entregable(con):
    e = repo_entrevista.crear(con)
    e.ficha = ficha_completa(vetadas=["hospital"], nombres_vetados=["Luis Pérez"])
    e.cerrada = True
    repo_entrevista.guardar(con, e, respuesta=CONVERSACION, pregunta="¿Y su edad?")
    escaleta.declarar_hechos(con, e.obra, [{"id": "hec-mapas",
                                            "enunciado": "colecciona mapas"}])
    return e


def test_entregar_borra_la_conversacion_y_la_ficha(con, entregable):
    entrega.entregar(con, entregable.obra)
    assert repo_entrevista.de_la_obra(con, entregable.obra) == []
    assert con.execute("SELECT COUNT(*) FROM turno_de_entrevista").fetchone()[0] == 0


def test_entregar_conserva_las_vetadas_de_la_novela(con, entregable):
    entrega.entregar(con, entregable.obra)
    formas = [v.forma for v in politica.vetadas_para(con, entregable.obra, 34, [])]
    assert formas == ["hospital", "Luis Pérez", "Luis"]


def test_entregar_conserva_los_hechos_de_la_story_bible(con, entregable):
    entrega.entregar(con, entregable.obra)
    assert [h["id"] for h in escaleta.hechos_declarados(con, entregable.obra)] == [
        "hec-mapas"]


def test_el_audit_log_dice_que_se_borro_pero_no_el_contenido(con, entregable):
    entrega.entregar(con, entregable.obra)
    [d] = [d for d in auditoria.decisiones(con, entregable.obra)
           if d["tipo"] == TD.BORRADO_AL_ENTREGAR]
    assert d["detalle"] == {"entrevistas": 1, "turnos": 1, "vetadas_conservadas": 3}
    volcado = json.dumps(auditoria.decisiones(con), ensure_ascii=False)
    assert CONVERSACION not in volcado and "Irene" not in volcado


def test_entregar_dos_veces_no_falla_ni_duplica(con, entregable):
    entrega.entregar(con, entregable.obra)
    entrega.entregar(con, entregable.obra)
    borrados = [d for d in auditoria.decisiones(con, entregable.obra)
                if d["tipo"] == TD.BORRADO_AL_ENTREGAR]
    assert len(borrados) == 1
    assert entrega.entregada(con, entregable.obra)


def test_no_se_entrega_una_obra_con_la_entrevista_abierta(con):
    """Borrar una ficha que el comprador no ha confirmado perderia lo que dijo
    antes de que sirviera para nada."""
    e = entrevista.crear(con)
    with pytest.raises(entrega.NoSePuedeEntregar):
        entrega.entregar(con, e.obra)
    assert repo_entrevista.de_la_obra(con, e.obra) == [e.id]


def test_el_endpoint_entrega_y_una_entrevista_abierta_es_409(tmp_path):
    from fastapi.testclient import TestClient

    from app.main import app, preparar_base
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    cliente = TestClient(app)
    abierta = cliente.post("/entrevistas").json()
    r = cliente.post("/obras/{0}/entregar".format(abierta["obra"]))
    assert r.status_code == 409 and "abierta" in r.json()["detail"]
    c = sqlite3.connect(ruta)
    e = repo_entrevista.leer(c, abierta["id"])
    e.ficha, e.cerrada = ficha_completa(vetadas=["hospital"]), True
    repo_entrevista.guardar(c, e)
    r = cliente.post("/obras/{0}/entregar".format(abierta["obra"]))
    assert r.status_code == 200
    assert r.json()["vetadas_conservadas"] == 1
