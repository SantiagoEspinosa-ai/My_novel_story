"""`PLAN-34` E6: el inspector visual mira datos inventados (`SPEC-34` `RF-09`).

La web enseña los nombres reales, y el inspector es un agente que la recorre: sobre una
novela de verdad veria a personas reales. Solo inspecciona una base marcada como inventada,
y la marcan las semillas.
"""

import sqlite3

import pytest

import inspeccion_visual
from app.commons.db import procedencia


def test_una_base_marcada_es_de_datos_inventados(tmp_path):
    con = sqlite3.connect(str(tmp_path / "a.db"))
    assert not procedencia.son_datos_inventados(con)
    procedencia.marcar_datos_inventados(con, "semilla_lectura")
    assert procedencia.son_datos_inventados(con)


def test_la_inspeccion_se_niega_sobre_una_base_que_no_es_inventada(tmp_path):
    ruta = str(tmp_path / "real.db")
    sqlite3.connect(ruta).close()
    with pytest.raises(SystemExit) as e:
        inspeccion_visual.main([ruta, "obra-x", "http://127.0.0.1:1"])
    assert "RF-09" in str(e.value) and "inventad" in str(e.value)


def test_las_semillas_marcan_su_base(tmp_path):
    import semilla_lectura
    ruta = str(tmp_path / "semilla.db")
    semilla_lectura.sembrar(ruta)
    assert procedencia.son_datos_inventados(sqlite3.connect(ruta))
