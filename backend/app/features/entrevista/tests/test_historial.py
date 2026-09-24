"""`SPEC-33` `RF-10`, `PLAN-33` E1: el historial de la entrevista.

La conversacion en la web sobrevive a recargar la pagina porque el historial es
estado del backend. Cada turno guarda la respuesta del comprador, la pregunta que
vino despues y lo que el codigo dijo en ese turno: lo que falta, los avisos y las
contradicciones. Lleva datos personales, asi que se borra con la ficha.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.features.entrevista import repository as repo
from app.features.entrevista.service import PRIMERA_PREGUNTA
from app.features.entrevista.tests.conftest import ficha_completa
from app.main import app, preparar_base


class Guion:
    """Un Entrevistador doble que contesta cada turno con la siguiente respuesta."""

    nombre = "doble"

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)

    def llamar(self, prompt):
        return self.respuestas.pop(0)


def _dice(ficha, pregunta):
    return {"ficha": ficha.model_dump(mode="json"), "pregunta": pregunta}


# El primer turno deja la ficha con un nombre vetado que coincide de pila con la
# mascota: eso es un aviso. El segundo la deja completa y sin avisos.
CON_AVISO = ficha_completa(nombres_vetados=["Brisa Ortega"])
PRIMERO = _dice(CON_AVISO, "¿Quien es Brisa Ortega?")
SEGUNDO = _dice(ficha_completa(), "¿Algo mas?")


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    guion = Guion([PRIMERO, SEGUNDO])
    app.state.entrevistador = lambda: guion
    yield TestClient(app)
    del app.state.entrevistador


def _dos_turnos(cliente):
    e = cliente.post("/entrevistas").json()
    for respuesta in ("Irene, 34 años", "No, eso es todo"):
        r = cliente.post("/entrevistas/{0}/turnos".format(e["id"]),
                         json={"respuesta": respuesta})
        assert cliente.get("/trabajos/" + r.json()["id_trabajo"]).json()["estado"] == \
            "terminado"
    return e


def test_el_historial_trae_cada_turno_con_sus_avisos_y_contradicciones(cliente):
    e = _dos_turnos(cliente)
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"]))
    assert h.status_code == 200, h.text
    primero, segundo = h.json()["turnos"]
    assert primero["respuesta"] == "Irene, 34 años"
    assert primero["pregunta"] == "¿Quien es Brisa Ortega?"
    assert primero["avisos"], "el aviso del nombre de pila tenia que quedar en su turno"
    assert primero["contradicciones_abiertas"] == []
    assert primero["falta"] == []
    assert primero["cuando"]
    assert segundo["avisos"] == []


def test_el_historial_esta_en_el_orden_de_los_turnos_y_trae_la_primera_pregunta(cliente):
    e = _dos_turnos(cliente)
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert h["primera_pregunta"] == PRIMERA_PREGUNTA
    assert [t["orden"] for t in h["turnos"]] == [1, 2]
    assert [t["respuesta"] for t in h["turnos"]] == ["Irene, 34 años", "No, eso es todo"]


def test_el_historial_de_una_entrevista_que_no_existe_es_404(cliente):
    assert cliente.get("/entrevistas/ent-no-existe/turnos").status_code == 404


def test_un_turno_de_antes_de_la_migracion_trae_sus_avisos_como_no_guardados(tmp_path):
    """Una fila vieja no tiene avisos guardados: eso no es lo mismo que no tenerlos."""
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    con = sqlite3.connect(ruta)
    e = repo.crear(con)
    con.execute("INSERT INTO turno_de_entrevista (entrevista, orden, respuesta, pregunta) "
                "VALUES (?, 1, 'hola', '¿y?')", (e.id,))
    con.commit()
    t = repo.turnos(con, e.id)[0]
    assert t["avisos"] is None and t["contradicciones_abiertas"] is None and t["falta"] is None


def test_borrar_la_ficha_borra_tambien_los_avisos_del_historial(cliente):
    """Guarda: las columnas nuevas llevan datos personales y no sobreviven a la ficha."""
    e = _dos_turnos(cliente)
    con = sqlite3.connect(app.state.ruta_db)
    repo.borrar_de_la_obra(con, e["obra"])
    assert con.execute("SELECT COUNT(*) FROM turno_de_entrevista").fetchone()[0] == 0
