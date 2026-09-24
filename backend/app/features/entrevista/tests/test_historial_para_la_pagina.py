"""`SPEC-33` `RF-08`, `RF-09`, `PLAN-33` E3: lo que la pagina necesita del historial.

La web no calcula si se puede cerrar ni lee la ficha: el historial trae `puede_cerrar`,
`cerrada` y los hechos propuestos con su estado, resueltos por el backend (`CLAUDE.md`:
la interfaz muestra estado, no lo calcula). Los endpoints de `PLAN-25` devuelven un campo
`contradicciones` que no puede entrar en el congelado (`RF-57`), asi que la pagina lee
de aqui y no de ellos.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.dominio.destinatario import HechoPropuesto
from app.features.entrevista import repository as repo
from app.features.entrevista.texto_libre import anadir_propuestos

from app.features.entrevista.tests.conftest import ficha_completa
from app.main import app, preparar_base


class Guion:
    nombre = "doble"

    def __init__(self, respuestas):
        self.respuestas = list(respuestas)

    def llamar(self, prompt):
        return self.respuestas.pop(0)


def _dice(ficha, pregunta="¿Algo mas?"):
    return {"ficha": ficha.model_dump(mode="json"), "pregunta": pregunta}


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    guion = Guion([_dice(ficha_completa(nombres_vetados=["Brisa Ortega"])),
                   _dice(ficha_completa())])
    app.state.entrevistador = lambda: guion
    yield TestClient(app)
    del app.state.entrevistador


def _turno(cliente, id_e, respuesta):
    r = cliente.post("/entrevistas/{0}/turnos".format(id_e), json={"respuesta": respuesta})
    assert cliente.get("/trabajos/" + r.json()["id_trabajo"]).json()["estado"] == "terminado"
    return cliente.get("/entrevistas/{0}/turnos".format(id_e)).json()


def test_el_historial_dice_si_se_puede_cerrar(cliente):
    e = cliente.post("/entrevistas").json()
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert h["puede_cerrar"] is False, "sin turnos falta todo"
    assert _turno(cliente, e["id"], "Irene")["puede_cerrar"] is False, "hay un aviso"
    assert _turno(cliente, e["id"], "Brisa es otra")["puede_cerrar"] is True


def _sembrar_hecho(id_e):
    """Los hechos propuestos solo salen del texto libre (`SPEC-25`): el Entrevistador no
    los puede crear. Se siembran como lo haria el texto libre."""
    con = sqlite3.connect(app.state.ruta_db)
    e = repo.leer(con, id_e)
    e.ficha = anadir_propuestos(e.ficha, [HechoPropuesto(
        id="hp-1", texto="aprendio a nadar a los 30")])
    repo.guardar(con, e)
    con.close()


def test_el_historial_trae_los_hechos_propuestos_con_su_estado(cliente):
    e = cliente.post("/entrevistas").json()
    _turno(cliente, e["id"], "Irene")
    _sembrar_hecho(e["id"])
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert h["hechos_propuestos"] == [
        {"id": "hp-1", "texto": "aprendio a nadar a los 30", "estado": "propuesto"}]
    cliente.post("/entrevistas/{0}/hechos/hp-1/confirmar".format(e["id"]))
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert h["hechos_propuestos"][0]["estado"] == "confirmado"


def test_el_historial_dice_si_la_entrevista_esta_cerrada(cliente):
    e = cliente.post("/entrevistas").json()
    _turno(cliente, e["id"], "Irene")
    assert _turno(cliente, e["id"], "Brisa es otra")["cerrada"] is False
    assert cliente.post("/entrevistas/{0}/cerrar".format(e["id"])).status_code == 200
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert h["cerrada"] is True and h["obra"] == e["obra"]
