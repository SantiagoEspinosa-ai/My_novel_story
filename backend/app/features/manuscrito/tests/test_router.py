"""`SPEC-35` `RF-12` y cuestión 2, `PLAN-35` E1: descargar el PDF desde la portada.

La ruta usa `exportar_pdf` tal como es, que ya se niega a exportar lo que la puerta no
publicó (`SPEC-27` `RF-01`). La consulta de disponibilidad existe para que la portada no
ofrezca un botón que falla: dice si hay PDF y, si no, por qué, sin generarlo.
"""

import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.db import migraciones
from app.features.manuscrito.tests.test_libro import base_de_prueba
from app.main import app


@pytest.fixture
def ruta(tmp_path):
    r = str(tmp_path / "libro.db")
    origen = base_de_prueba()
    destino = sqlite3.connect(r)
    origen.backup(destino)
    destino.executescript(migraciones.VEREDICTO_SQL)
    destino.close()
    app.state.ruta_db = r
    return r


@pytest.fixture
def cliente(ruta):
    return TestClient(app)


def _veredicto(ruta, publica, condiciones=()):
    con = sqlite3.connect(ruta)
    n = con.execute("SELECT COUNT(*) FROM veredicto_de_publicacion").fetchone()[0]
    with con:
        con.execute("INSERT INTO veredicto_de_publicacion (obra, ronda, publica, condiciones, "
                    "codigo_lean, no_ejecutadas) VALUES ('o1', ?, ?, ?, 0, '[]')",
                    (n + 1, int(publica), json.dumps(list(condiciones))))
    con.close()


def test_una_obra_publicada_descarga_su_pdf(cliente, ruta):
    _veredicto(ruta, True)
    r = cliente.get("/obras/o1/pdf")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")
    assert "La ruta del gato" in r.headers.get("content-disposition", "")


def test_una_obra_sin_publicar_no_tiene_pdf_y_dice_por_que(cliente, ruta):
    _veredicto(ruta, False, [{"invariante": "INV-29", "capitulo": "o1-cap-02",
                              "detalle": "rendido"}])
    r = cliente.get("/obras/o1/pdf")
    assert r.status_code == 409
    assert "INV-29" in r.json()["detail"]


def test_disponible_dice_si_hay_pdf_sin_generarlo(cliente, ruta):
    d = cliente.get("/obras/o1/pdf/disponible").json()
    assert d["disponible"] is False and "puerta" in d["motivo"]
    _veredicto(ruta, True)
    assert cliente.get("/obras/o1/pdf/disponible").json() == {"disponible": True, "motivo": None}


def test_obra_que_no_existe_es_404(cliente):
    """Con su motivo: sin él, este 404 pasaba antes de existir la ruta."""
    for url in ("/obras/no-existe/pdf", "/obras/no-existe/pdf/disponible"):
        r = cliente.get(url)
        assert r.status_code == 404 and "no existe la obra" in r.json()["detail"], url


def _escena_sin_texto(ruta):
    """Una escena del libro sin borrador aceptado: la puerta pudo publicar y el libro no se
    puede componer. Lo encontro la inspeccion de `PLAN-35` E8 sobre la semilla de lectura."""
    con = sqlite3.connect(ruta)
    with con:
        con.execute("UPDATE escena SET borrador_aceptado = NULL WHERE id = 'o1-cap-02-e1'")
        con.execute("DELETE FROM borrador WHERE escena = 'o1-cap-02-e1'")
    con.close()


def test_un_libro_que_no_se_puede_componer_no_se_ofrece(cliente, ruta):
    _veredicto(ruta, True)
    _escena_sin_texto(ruta)
    d = cliente.get("/obras/o1/pdf/disponible").json()
    assert d["disponible"] is False and "sin texto" in d["motivo"]


def test_descargar_un_libro_incompleto_es_409_con_motivo_y_no_500(cliente, ruta):
    _veredicto(ruta, True)
    _escena_sin_texto(ruta)
    r = cliente.get("/obras/o1/pdf")
    assert r.status_code == 409, r.text
    assert "sin texto" in r.json()["detail"]


def test_la_conexion_se_puede_usar_desde_otro_hilo(tmp_path):
    """`F-202`: FastAPI puede abrir la conexion de la dependencia en un hilo y usarla en otro.
    Con el `check_same_thread` por defecto, el servidor real daba un 500 intermitente; el
    cliente de pruebas lo hace todo en un hilo y no lo veia."""
    import threading
    from types import SimpleNamespace

    from app.features.manuscrito.router import conexion

    peticion = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        ruta_db=str(tmp_path / "hilos.db"))))
    generador = conexion(peticion)
    con = next(generador)
    errores = []

    def usar():
        try:
            con.execute("SELECT 1").fetchone()
        except Exception as e:  # el fallo que se busca es precisamente este
            errores.append(e)

    hilo = threading.Thread(target=usar)
    hilo.start()
    hilo.join()
    generador.close()
    assert errores == []
