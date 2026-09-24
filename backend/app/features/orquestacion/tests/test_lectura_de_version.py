"""`PLAN-22` E15 — leer una version (`SPEC-22` `RF-52`..`RF-54`; amplia `VER-104`, `VER-105`).

Las lecturas de una version **componen** dos features -la lectura de `lectura/` y la
marca y la reverificacion de `regeneracion`-, y por eso viven en `orquestacion/`, la
unica autorizada a componer (`A-02`). La marca de «cambio» y el `estado_de_verificacion`
**llegan de `regeneracion`**: aqui no se comparan textos ni se recalculan.

Dos versiones sembradas con el repositorio de `PLAN-23` (`_dos_versiones`, la misma que
`test_router_versiones.py`): la 2 sustituye el capitulo 2 y comparte el 1 y el 3.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.features.orquestacion import regeneracion
from app.features.orquestacion.tests import obra_regenerable as o
from app.features.orquestacion.tests.test_router_versiones import _dos_versiones
from app.main import app, preparar_base


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta).close()
    con = o.conexion()
    ids, nuevo = _dos_versiones(con)
    # Solo se reverifica la 1: en la 2, el capitulo 3 compartido hereda un verde que
    # **no cuenta** (`D-1`), y el 1 tampoco se ha vuelto a pasar.
    regeneracion.reverificar(con, "obra-a", 1)
    destino = sqlite3.connect(ruta)
    con.backup(destino)
    destino.close()
    con.close()
    anterior = getattr(app.state, "ruta_db", None)
    app.state.ruta_db = ruta
    try:
        yield TestClient(app), ids, nuevo
    finally:
        app.state.ruta_db = anterior


def test_la_version_anterior_se_sigue_leyendo_entera(cliente):
    c, ids, nuevo = cliente
    v1 = c.get("/obras/obra-a/versiones/1/indice")
    assert v1.status_code == 200, v1.text
    v1 = v1.json()
    assert (v1["numero"], v1["anterior"]) == (1, None)
    assert [x["id"] for x in v1["capitulos"]] == ids
    assert [x["orden"] for x in v1["capitulos"]] == [1, 2, 3]
    # Cada capitulo de la 1 se lee entero, con el texto que tenia: el 2 viejo sigue ahi.
    for x in v1["capitulos"]:
        cap = c.get("/obras/obra-a/versiones/1/capitulos/{0}".format(x["id"]))
        assert cap.status_code == 200, cap.text
        escenas = cap.json()["escenas"]
        assert [e["id"] for e in escenas] == [e["id"] for e in x["escenas"]]
        assert escenas[0]["borrador"]["texto"] == "texto de {0}".format(x["id"])
    v2 = c.get("/obras/obra-a/versiones/2/indice").json()
    assert [x["id"] for x in v2["capitulos"]] == [ids[0], nuevo, ids[2]]
    assert [x["orden"] for x in v2["capitulos"]] == [1, 2, 3]
    assert c.get("/obras/obra-a/versiones/2/capitulos/{0}".format(nuevo)).json()[
        "escenas"][0]["borrador"]["texto"] == "texto de c2"


def test_un_capitulo_que_no_es_de_la_version_da_404(cliente):
    c, ids, nuevo = cliente
    assert c.get("/obras/obra-a/versiones/1/capitulos/{0}".format(nuevo)).status_code == 404
    assert c.get("/obras/obra-a/versiones/2/capitulos/{0}".format(ids[1])).status_code == 404
    assert c.get("/obras/obra-a/versiones/9/indice").status_code == 404


def test_cada_capitulo_trae_su_marca_de_cambio_y_no_se_calcula_aqui(cliente, monkeypatch):
    c, ids, nuevo = cliente
    v2 = c.get("/obras/obra-a/versiones/2/indice").json()
    assert [x["compartido"] for x in v2["capitulos"]] == [True, False, True]
    # Sin anterior no hay con que comparar: nulo, no «cambio».
    v1 = c.get("/obras/obra-a/versiones/1/indice").json()
    assert [x["compartido"] for x in v1["capitulos"]] == [None, None, None]
    # La marca es la de `regeneracion`: si dijera otra cosa, la lectura diria lo mismo.
    monkeypatch.setattr(regeneracion, "comparar", lambda con, obra, a, b: [
        {"orden": n, "capitulo": x, "compartido": n == 2}
        for n, x in enumerate([ids[0], nuevo, ids[2]], 1)])
    v2 = c.get("/obras/obra-a/versiones/2/indice").json()
    assert [x["compartido"] for x in v2["capitulos"]] == [False, True, False]
    cap = c.get("/obras/obra-a/versiones/2/capitulos/{0}".format(nuevo)).json()
    assert cap["compartido"] is True


def test_una_escena_con_verde_heredado_no_sale_como_verificada(cliente):
    c, ids, nuevo = cliente
    v2 = c.get("/obras/obra-a/versiones/2/indice").json()
    tercera = v2["capitulos"][2]["escenas"][0]
    # Consolidada, y aun asi sin reverificar en la 2: su verde es de la 1 (`RF-54`).
    assert (tercera["estado"], tercera["estado_de_verificacion"]) == (
        "consolidada", EV.SIN_REVERIFICAR.value)
    leida = c.get("/obras/obra-a/versiones/2/capitulos/{0}".format(ids[2])).json()
    assert leida["escenas"][0]["estado_de_verificacion"] == EV.SIN_REVERIFICAR.value
    # La misma escena, en la 1 que si se reverifico, esta verificada.
    v1 = c.get("/obras/obra-a/versiones/1/indice").json()
    assert v1["capitulos"][2]["escenas"][0]["estado_de_verificacion"] == EV.VERIFICADA.value
    # Y cada escena sigue llevando su estado y sus hallazgos (`VER-105`).
    for x in v2["capitulos"]:
        for e in x["escenas"]:
            assert e["estado"] and isinstance(e["hallazgos_abiertos"], list)


def test_el_indice_sin_version_es_el_de_la_vigente_y_no_tiene_dos_capitulos_2(cliente):
    """Con dos versiones, `capitulo` tiene el 2 viejo y el nuevo, los dos con `orden` 2.
    El indice de siempre sacaba los cuatro: dos «Capitulo 2» (`VER-104`)."""
    c, ids, nuevo = cliente
    indice = c.get("/obras/obra-a/indice").json()
    assert [x["id"] for x in indice["capitulos"]] == [ids[0], nuevo, ids[2]]
    assert [x["orden"] for x in indice["capitulos"]] == [1, 2, 3]
