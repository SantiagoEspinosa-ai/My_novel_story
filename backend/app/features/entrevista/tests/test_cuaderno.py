"""`PLAN-35` F1: el cuaderno de la entrevista, resuelto por el backend (`SPEC-35` `RF-05`,
`RF-07`). La web no cuenta campos ni traduce valores: pinta lo que llega. Datos inventados.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.features.entrevista import repository as repo
from app.features.entrevista import service
from app.features.entrevista.tests.conftest import ficha_completa


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    repo.asegurar_tablas(c)
    return c


def _con_ficha(con, ficha):
    e = service.crear(con)
    entrevista = repo.leer(con, e.id)
    entrevista.ficha = ficha
    repo.guardar(con, entrevista)
    return e.id


def test_el_cuaderno_dice_lo_que_se_sabe_y_lo_que_falta(con):
    datos = ficha_completa().model_dump(mode="json")
    datos.update({"tono": None, "titulo": None})
    from app.commons.dominio.destinatario import FichaDeEntrevista
    id_e = _con_ficha(con, FichaDeEntrevista.model_validate(datos))
    c = service.historial(con, id_e)["cuaderno"]
    assert c["total"] == 11 and c["faltan"] == 2
    assert c["falta"] == ["Tono", "Título"]
    campos = [s["campo"] for s in c["sabido"]]
    assert campos == ["nombre", "edad", "ocasion", "genero", "extension", "papel", "rasgo",
                      "recuerdo", "premisa"]


def test_una_entrevista_nueva_tiene_todo_por_saber(con):
    e = service.crear(con)
    c = service.historial(con, e.id)["cuaderno"]
    assert c["sabido"] == [] and c["faltan"] == c["total"] == 11
    assert c["falta"][0] == "Nombre"


def test_el_cuaderno_habla_con_palabras_de_persona(con):
    """`SPEC-35` `RF-02`: nada de `cumpleanos` ni `drama_cotidiano`."""
    id_e = _con_ficha(con, ficha_completa(genero="drama_cotidiano"))
    valores = {s["campo"]: s["valores"] for s in service.historial(con, id_e)["cuaderno"]["sabido"]}
    assert valores["ocasion"] == ["cumpleaños"]
    assert valores["genero"] == ["drama cotidiano"]
    assert valores["edad"] == ["34 años"]
    assert valores["extension"][0].startswith("media: de 1150 a 1350 palabras")
    assert "colecciona mapas antiguos (imprescindible)" in valores["rasgo"]
    assert "el viaje en tren a Lisboa (a los 20 años) (imprescindible)" in valores["recuerdo"]


def test_otro_se_ensena_con_las_palabras_del_comprador(con):
    id_e = _con_ficha(con, ficha_completa(tono="otro",
                                          literales_de_otro={"tono": "agridulce, como ella"}))
    valores = {s["campo"]: s["valores"] for s in service.historial(con, id_e)["cuaderno"]["sabido"]}
    assert valores["tono"] == ["agridulce, como ella"]


def test_el_cuaderno_trae_la_propuesta_para_el_cuaderno_completo(con):
    id_e = _con_ficha(con, ficha_completa())
    p = service.historial(con, id_e)["cuaderno"]["propuesta"]
    assert p == {"titulo": "El mapa de Irene",
                 "premisa": "Un mapa antiguo devuelve a Irene al tren de Lisboa.",
                 "dedicatoria": "Para Irene, que siempre llega."}


def test_el_historial_por_http_trae_el_cuaderno(tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app, preparar_base
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    cliente = TestClient(app)
    e = cliente.post("/entrevistas").json()
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert h["cuaderno"]["total"] == 11 and h["cuaderno"]["propuesta"]["titulo"] is None
