"""`PLAN-34` E3: los nombres entran fuera del modelo (`SPEC-34` `RF-01`, `RF-07`).

Datos inventados. El doble del Entrevistador **hace lo que haria el modelo**: devuelve la
ficha que recibio en el prompt, con lo que el comprador dijo, y usa los nombres que ve.
"""

import json
import re
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.configuracion.esquemas import ReglasDeContradiccion
from app.commons.db import migraciones
from app.commons.politica import pseudonimos
from app.features.entrevista import repository as repo
from app.features.entrevista import service
from app.features.entrevista.schemas import NombresEntrada
from app.main import app, preparar_base

REGLAS = ReglasDeContradiccion()
REALES = ("Olivia", "Carranza", "Tino", "Ramón", "Marcos", "Ledesma")


def _diminutivo(nombre):
    """«Elena» -> «Elenita», «Inés» -> «Inésita»: sin la ultima vocal, si la tiene."""
    return (nombre[:-1] if nombre[-1] in "aeiou" else nombre) + "ita"


class EntrevistadorEco:
    """Lee la ficha del prompt y la devuelve con la edad; pregunta usando el nombre."""

    nombre = "doble-entrevistador"

    def __init__(self, cambiar=None):
        self.prompts, self.cambiar = [], cambiar

    def llamar(self, prompt):
        self.prompts.append(prompt)
        bloque = prompt.split("FICHA ACTUAL\n", 1)[1].split("\n\nLO QUE FALTA", 1)[0]
        ficha = json.loads(bloque)
        ficha["destinatario"]["edad"] = 9
        if self.cambiar:
            self.cambiar(ficha)
        pila = " ".join((ficha["destinatario"]["nombre"] or "").split()[:1])
        return {"ficha": ficha, "pregunta": "¿Con qué motivo regalas la novela a {0}?".format(
            pila)}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    repo.asegurar_tablas(c)
    return c


def _nombres(**kw):
    datos = {"destinatario": "Olivia Carranza"}
    datos.update(kw)
    return NombresEntrada.model_validate(datos)


def test_declarar_el_nombre_no_llama_al_agente_y_registra_el_turno(con):
    e = service.crear(con)
    t = service.declarar_nombres(con, e.id, _nombres(), REGLAS, 2026)
    assert t.ficha.destinatario.nombre == "Olivia Carranza"
    assert "nombre" not in t.falta
    turnos = repo.turnos(con, e.id)
    assert len(turnos) == 1
    assert turnos[0]["respuesta"] == "Olivia Carranza"
    assert turnos[0]["fuera_del_modelo"] is True
    assert "Olivia" in turnos[0]["pregunta"]  # la pregunta fija lo nombra: el comprador lo lee
    assert pseudonimos.de_la_obra(con, e.obra).pares.keys() == {"Olivia", "Carranza"}


def test_el_entrevistador_recibe_pseudonimos_y_la_ficha_guarda_los_reales(con):
    e = service.crear(con)
    service.declarar_nombres(con, e.id, _nombres(
        otros=[{"nombre": "Tino", "tipo": "mascota", "relacion": "su perro"}],
        regalado_por="Ramón"), REGLAS, 2026)
    agente = EntrevistadorEco()
    t = service.turno(con, e.id, "Olivia tiene 9 años y adora a Tino", agente, REGLAS, 2026)
    for real in REALES[:4]:
        assert not re.search(r"\b{0}\b".format(real), agente.prompts[0]), real
    assert t.ficha.destinatario.nombre == "Olivia Carranza"
    assert t.ficha.destinatario.edad == 9
    assert [el.nombre for el in t.ficha.destinatario.elementos] == ["Tino"]
    assert t.ficha.regalado_por == "Ramón"
    # La pregunta se restituye: el comprador lee el nombre real.
    assert "Olivia" in t.pregunta
    guardada = repo.leer(con, e.id).ficha
    assert guardada.destinatario.nombre == "Olivia Carranza"


def test_el_modelo_no_puede_cambiar_un_nombre_declarado(con):
    e = service.crear(con)
    service.declarar_nombres(con, e.id, _nombres(
        otros=[{"nombre": "Tino", "tipo": "mascota", "relacion": "su perro"}]), REGLAS, 2026)

    def cambiar(ficha):
        ficha["destinatario"]["nombre"] = "[NOMBRE_ANONIMIZADO]"
        ficha["destinatario"]["elementos"] = []
        ficha["nombres_vetados"] = ["Otro"]

    t = service.turno(con, e.id, "tiene 9", EntrevistadorEco(cambiar), REGLAS, 2026)
    assert t.ficha.destinatario.nombre == "Olivia Carranza"
    assert [el.nombre for el in t.ficha.destinatario.elementos] == ["Tino"]
    assert t.ficha.nombres_vetados == []


def test_los_nombres_vetados_no_llegan_al_entrevistador(con):
    e = service.crear(con)
    service.declarar_nombres(con, e.id, _nombres(vetados=["Marcos Ledesma"]), REGLAS, 2026)
    agente = EntrevistadorEco()
    t = service.turno(con, e.id, "no quiero que salga Marcos Ledesma", agente, REGLAS, 2026)
    assert "Marcos" not in agente.prompts[0] and "Ledesma" not in agente.prompts[0]
    assert t.ficha.nombres_vetados == ["Marcos Ledesma"]


def test_un_aviso_de_nombre_se_confirma_fuera_del_modelo(con):
    e = service.crear(con)
    t = service.declarar_nombres(con, e.id, _nombres(vetados=["Olivia Pérez"]), REGLAS, 2026)
    assert len(t.avisos) == 1
    t = service.confirmar_aviso(con, e.id, "Olivia Pérez", REGLAS, 2026)
    assert t.avisos == []
    with pytest.raises(KeyError):
        service.confirmar_aviso(con, e.id, "Nadie", REGLAS, 2026)


def test_un_resto_en_la_ficha_es_un_aviso_del_turno(con):
    e = service.crear(con)
    service.declarar_nombres(con, e.id, _nombres(), REGLAS, 2026)
    derivada = _diminutivo(pseudonimos.de_la_obra(con, e.obra).pares["Olivia"])

    def cambiar(ficha):
        ficha["destinatario"]["elementos"] = [
            {"tipo": "rasgo", "descripcion": "la llaman {0}".format(derivada)}]

    service.turno(con, e.id, "la llaman así", EntrevistadorEco(cambiar), REGLAS, 2026)
    ultimo = repo.turnos(con, e.id)[-1]
    assert ultimo["fuera_del_modelo"] is False
    assert any(derivada in a for a in ultimo["avisos"])


def test_un_nombre_que_saca_el_modelo_sin_declarar_recibe_pseudonimo_despues(con):
    """El camino de siempre (la CLI de antes, un guion): el nombre llega en una respuesta.
    Desde el turno siguiente ya no sale."""
    e = service.crear(con)

    def poner(ficha):
        ficha["destinatario"]["nombre"] = "Olivia Carranza"

    service.turno(con, e.id, "Se llama Olivia Carranza", EntrevistadorEco(poner), REGLAS, 2026)
    segundo = EntrevistadorEco()
    service.turno(con, e.id, "cumpleaños", segundo, REGLAS, 2026)
    assert "Olivia" not in segundo.prompts[0]


# --- Por HTTP -----------------------------------------------------------------

@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    app.state.entrevistador = EntrevistadorEco
    yield TestClient(app)
    del app.state.entrevistador


def test_el_historial_dice_que_se_pidio_fuera_del_modelo(cliente):
    e = cliente.post("/entrevistas").json()
    r = cliente.put("/entrevistas/{0}/nombres".format(e["id"]), json={
        "destinatario": "Olivia Carranza", "regalado_por": "Ramón",
        "otros": [{"nombre": "Tino", "tipo": "mascota", "relacion": "su perro"}],
        "vetados": ["Olivia Pérez"]})
    assert r.status_code == 200, r.text
    t = cliente.post("/entrevistas/{0}/turnos".format(e["id"]), json={"respuesta": "9 años"})
    assert t.status_code == 202
    h = cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()
    assert [x["fuera_del_modelo"] for x in h["turnos"]] == [True, False]
    n = h["nombres"]
    assert n["destinatario"] == "Olivia Carranza" and n["regalado_por"] == "Ramón"
    assert n["otros"] == [{"nombre": "Tino", "tipo": "mascota", "relacion": "su perro",
                           "declarado": True}]
    assert n["vetados"] == ["Olivia Pérez"]
    assert [a["vetado"] for a in n["avisos"]] == ["Olivia Pérez"]
    r = cliente.post("/entrevistas/{0}/avisos/confirmar".format(e["id"]),
                     json={"vetado": "Olivia Pérez"})
    assert r.status_code == 200, r.text
    assert cliente.get("/entrevistas/{0}/turnos".format(e["id"])).json()["nombres"][
        "avisos"] == []


def test_los_nombres_de_una_entrevista_cerrada_no_cambian(cliente):
    e = cliente.post("/entrevistas").json()
    cliente.put("/entrevistas/{0}/nombres".format(e["id"]), json={"destinatario": "Olivia"})
    import sqlite3 as s
    c = s.connect(app.state.ruta_db)
    c.execute("UPDATE entrevista SET cerrada = 1 WHERE id = ?", (e["id"],))
    c.commit()
    c.close()
    r = cliente.put("/entrevistas/{0}/nombres".format(e["id"]), json={"destinatario": "X"})
    assert r.status_code == 409


def test_un_tipo_de_nombre_desconocido_es_422(cliente):
    e = cliente.post("/entrevistas").json()
    r = cliente.put("/entrevistas/{0}/nombres".format(e["id"]), json={
        "destinatario": "Olivia", "otros": [{"nombre": "X", "tipo": "rasgo"}]})
    assert r.status_code == 422
