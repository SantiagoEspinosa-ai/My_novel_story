"""`PLAN-22` E11: la semilla de la lectura web, montada como la monta la novela regalo.

Datos **inventados** y marcados como tales, sin modelo. La obra se monta con
`novela.montar` y sus escenas avanzan por las funciones del repositorio, nunca con un
`UPDATE` a mano: es lo que comprueba que la forma que leen las pruebas de `lectura/` es
la que dejan los que escriben. Se lee con la API arrancada como la arranca `uvicorn`
(`HARNESS_BASE`, como `test_arranque.py`).
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

import semilla_lectura
from app.main import app


@pytest.fixture
def api_sobre_la_semilla(tmp_path, monkeypatch):
    ruta = str(tmp_path / "semilla.db")
    assert semilla_lectura.sembrar(ruta) is True
    monkeypatch.setenv("HARNESS_BASE", ruta)
    monkeypatch.delattr(app.state, "ruta_db", raising=False)
    with TestClient(app) as cliente:
        yield cliente, ruta
    monkeypatch.delattr(app.state, "ruta_db", raising=False)


def test_la_semilla_deja_una_obra_de_dos_capitulos_que_la_api_lee_entera(api_sobre_la_semilla):
    cliente, _ = api_sobre_la_semilla
    r = cliente.get("/obras/{0}/indice".format(semilla_lectura.OBRA))
    assert r.status_code == 200, r.text
    indice = r.json()
    assert len(indice["capitulos"]) >= 2
    assert indice["dedicatoria"]
    estados = []
    for c in indice["capitulos"]:
        cap = cliente.get("/capitulos/{0}".format(c["id"]))
        assert cap.status_code == 200, cap.text
        assert [e["id"] for e in cap.json()["escenas"]] == [e["id"] for e in c["escenas"]]
        for e in cap.json()["escenas"]:
            estados.append(e["estado"])
            assert cliente.get("/escenas/{0}".format(e["id"])).json() == e
    assert {"consolidada", "aceptada_por_rendicion", "generada", "planificada"} <= set(estados)
    generadas = [e for c in indice["capitulos"] for e in c["escenas"] if e["estado"] == "generada"]
    assert any(e["hallazgos_abiertos"] for e in generadas)
    fichas = cliente.get("/obras/{0}/fichas".format(semilla_lectura.OBRA))
    assert fichas.status_code == 200, fichas.text
    assert fichas.json()["personajes"] and fichas.json()["lugares"]


def test_la_semilla_no_escribe_en_una_base_que_ya_tiene_esa_obra(tmp_path):
    ruta = str(tmp_path / "semilla.db")
    assert semilla_lectura.sembrar(ruta) is True
    con = sqlite3.connect(ruta)
    antes = [con.execute("SELECT COUNT(*) FROM {0}".format(t)).fetchone()[0]
             for t in ("borrador", "hallazgo", "escena", "capitulo")]
    con.close()
    assert semilla_lectura.sembrar(ruta) is False
    con = sqlite3.connect(ruta)
    despues = [con.execute("SELECT COUNT(*) FROM {0}".format(t)).fetchone()[0]
               for t in ("borrador", "hallazgo", "escena", "capitulo")]
    con.close()
    assert despues == antes


def test_la_semilla_no_escribe_sql_a_mano():
    import pathlib
    import re
    fuente = pathlib.Path(semilla_lectura.__file__).read_text(encoding="utf-8")
    assert not re.search(r"(UPDATE\s+\w+\s+SET|INSERT\s+INTO|DELETE\s+FROM)", fuente, re.I)


# --- `PLAN-22` E18: una segunda version, sembrada sin modelo ---------------------------

def test_la_semilla_deja_dos_versiones_y_la_segunda_sustituye_el_capitulo_1(api_sobre_la_semilla):
    """La 2 sale de una peticion de hecho inventada, con el repositorio de `PLAN-23`: el
    capitulo 1 es nuevo y los demas se comparten, asi que la vigente sigue teniendo una
    escena de cada estado (la prueba de arriba). Es lo que la inspeccion de E18
    recorre: la seleccion, los capitulos, las marcas y la version anterior."""
    cliente, _ = api_sobre_la_semilla
    obra = semilla_lectura.OBRA
    versiones = cliente.get("/obras/{0}/versiones".format(obra)).json()["versiones"]
    assert [(v["numero"], v["anterior"]) for v in versiones] == [(1, None), (2, 1)]
    assert versiones[1]["peticion"] is not None
    v2 = cliente.get("/obras/{0}/versiones/2/indice".format(obra)).json()
    assert [c["compartido"] for c in v2["capitulos"]] == [False, True, True, True]
    assert [c["id"] for c in v2["capitulos"]] == ["cap-01-v2", "cap-02", "cap-03", "cap-04"]
    # La 1 se sigue leyendo entera, con su texto de antes.
    v1 = cliente.get("/obras/{0}/versiones/1/indice".format(obra)).json()
    assert [c["id"] for c in v1["capitulos"]] == ["cap-01", "cap-02", "cap-03", "cap-04"]
    viejo = cliente.get("/obras/{0}/versiones/1/capitulos/cap-01".format(obra)).json()
    assert viejo["escenas"][0]["borrador"]["texto"] == semilla_lectura.TEXTOS["cap-01-e1"]
    # La escena nueva ofrece el hecho, y proponer cambiarlo contesta sin modelo.
    hechos = cliente.get("/escenas/cap-01-v2-e1/hechos").json()["hechos_que_usa"]
    assert [h["id"] for h in hechos] == ["hec-faro"]
    r = cliente.post("/obras/{0}/cambios/propuesta".format(obra), json={
        "clase": "hecho", "hecho": "hec-faro", "enunciado_nuevo": "Otro (inventado).",
        "texto": "Palabras inventadas."})
    assert r.status_code == 200, r.text
    assert r.json()["capitulos"]["selectiva"] == ["cap-01-v2"]
    # La 2 no se ha reverificado y la 1 si: las dos caras de `RF-54` en la web.
    assert {e["estado_de_verificacion"] for c in v2["capitulos"] for e in c["escenas"]}         == {"sin_reverificar"}
    # En la 1, el capitulo 1 -el unico con delta- se reverifico: su estado es el de las
    # puertas, no el heredado.
    assert v1["capitulos"][0]["escenas"][0]["estado_de_verificacion"] != "sin_reverificar"
