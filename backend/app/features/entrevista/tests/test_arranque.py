"""`F-70`: la API arrancada como la arranca `uvicorn` conserva lo que guarda.

Las pruebas del router fijan `app.state.ruta_db` a mano, y por eso no veian que el
arranque real no lo fijaba: cada peticion abria una base en memoria nueva, y una
entrevista creada no existia en la peticion siguiente. Aqui no se fija nada: la
base la decide el arranque, con `TestClient` como gestor de contexto para que corra.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def arranque_real(tmp_path, monkeypatch):
    ruta = str(tmp_path / "harness.db")
    monkeypatch.setenv("HARNESS_BASE", ruta)
    # Otras pruebas dejan `ruta_db` puesta en el `app` compartido; el arranque real
    # empieza sin ella.
    monkeypatch.delattr(app.state, "ruta_db", raising=False)
    with TestClient(app) as cliente:
        yield cliente, ruta
    monkeypatch.delattr(app.state, "ruta_db", raising=False)


def test_una_entrevista_creada_existe_en_la_peticion_siguiente(arranque_real):
    cliente, _ = arranque_real
    creada = cliente.post("/entrevistas", json={})
    assert creada.status_code == 201, creada.text
    leida = cliente.get("/entrevistas/" + creada.json()["id"])
    assert leida.status_code == 200, leida.text


def test_el_arranque_prepara_la_base_en_la_ruta_configurada(arranque_real):
    cliente, ruta = arranque_real
    cliente.post("/entrevistas", json={})
    con = sqlite3.connect(ruta)
    tablas = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    con.close()
    assert "esquema_version" in tablas and "procedencia" in tablas
