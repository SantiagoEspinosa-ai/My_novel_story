"""`PLAN-22` E13c (`SPEC-22` `RF-60`): el progreso de una generacion por la API.

Los segundos desde la ultima actividad los calcula **el servidor**, con su reloj: la
interfaz los pinta y no resta fechas. Sin ninguna fila de progreso, la obra no se esta
generando y la respuesta es `404`, no una fase inventada.
"""

from app.features.lectura.tests.conftest import OBRA, OTRA
from app.main import app
import sqlite3


def _con():
    return sqlite3.connect(app.state.ruta_db)


def _fijar(fase, hace, capitulo=None, total=None, motivo=None, obra=OBRA):
    con = _con()
    with con:
        con.execute(
            "INSERT INTO progreso_de_generacion (obra, fase, capitulo, total_de_capitulos, "
            "motivo, desde) VALUES (?, ?, ?, ?, ?, datetime('now', ?))",
            (obra, fase, capitulo, total, motivo, "-{0} seconds".format(hace)))
    con.close()


def test_el_progreso_trae_los_segundos_desde_la_ultima_actividad_calculados_en_el_servidor(cliente):
    _fijar("planificando", 900)
    _fijar("escribiendo", 600, capitulo=2, total=10)
    r = cliente.get("/obras/{0}/progreso".format(OBRA))
    assert r.status_code == 200, r.text
    p = r.json()
    assert (p["fase"], p["capitulo"], p["total_de_capitulos"]) == ("escribiendo", 2, 10)
    assert 600 <= p["segundos_desde_la_ultima_actividad"] < 660
    # Una traza de delegacion mas reciente, de una escena de la obra, es actividad.
    con = _con()
    with con:
        con.execute("CREATE TABLE IF NOT EXISTS traza_de_delegacion (escena TEXT NOT NULL, "
                    "agente TEXT NOT NULL, prompt_hash TEXT NOT NULL DEFAULT '', "
                    "cuando TEXT NOT NULL DEFAULT (datetime('now')))")
        con.execute("INSERT INTO traza_de_delegacion (escena, agente, cuando) VALUES "
                    "('esc-b1', 'escritor', datetime('now', '-30 seconds'))")
        # La de otra obra no cuenta.
        con.execute("INSERT INTO traza_de_delegacion (escena, agente, cuando) VALUES "
                    "('esc-z1', 'escritor', datetime('now', '-1 seconds'))")
    con.close()
    p = cliente.get("/obras/{0}/progreso".format(OBRA)).json()
    assert 30 <= p["segundos_desde_la_ultima_actividad"] < 90
    assert p["desde"] < p["ultima_actividad"]


def test_una_parada_viaja_con_su_motivo(cliente):
    _fijar("parada", 5, motivo="tope_delegaciones")
    p = cliente.get("/obras/{0}/progreso".format(OBRA)).json()
    assert (p["fase"], p["motivo"]) == ("parada", "tope_delegaciones")


def test_sin_generacion_el_progreso_es_404_y_no_una_fase_inventada(cliente):
    assert cliente.get("/obras/{0}/progreso".format(OBRA)).status_code == 404
    _fijar("escribiendo", 5, capitulo=1, total=1, obra=OTRA)
    assert cliente.get("/obras/{0}/progreso".format(OBRA)).status_code == 404
    assert cliente.get("/obras/no-existe/progreso").status_code == 404
