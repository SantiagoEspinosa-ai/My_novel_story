"""`PLAN-22` E13c (`SPEC-22` `RF-60`, `VER-128`): en que punto va una generacion.

`novela.escribir` deja una fila de `progreso_de_generacion` al entrar en cada fase, y una
generacion que se para lo dice con su motivo. Con dobles de los agentes: nada llama al
modelo.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.features.orquestacion import novela, progreso
from app.features.orquestacion.tests.test_novela import (
    _agentes, _agentes_para_la_novela_entera, _Fijo, _LeanFijo)
from app.features.planificacion.tests.conftest import ficha


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _fases(con, obra="obra-x"):
    return [(f["fase"], f["capitulo"], f["total_de_capitulos"], f["motivo"])
            for f in progreso.historia(con, obra)]


def _comprimida(fases):
    salida = []
    for f in fases:
        if not salida or salida[-1][:2] != f[:2]:
            salida.append(f)
    return salida


def test_escribir_deja_la_fase_de_cada_paso_en_orden(con, tmp_path):
    r = novela.escribir(con, "obra-x", ficha(), _agentes_para_la_novela_entera(),
                        carpeta_de_reglas=str(tmp_path), lean=_LeanFijo())
    fases = _comprimida(_fases(con))
    nombres = [f[0] for f in fases]
    assert nombres[:5] == ["planificando", "revisando_plan", "escribiendo", "editando",
                           "resumiendo"], nombres[:8]
    escribiendo = [f for f in fases if f[0] == "escribiendo"]
    capitulos = [f[1] for f in escribiendo]
    assert capitulos == sorted(capitulos) and capitulos[0] == 1 and capitulos[-1] == 10
    assert all(f[2] == 10 for f in escribiendo)
    puerta = nombres.index("en_la_puerta")
    assert "planificando" not in nombres[puerta:]
    final = "publicada" if r["publicacion"].publicada else "esperando_revision"
    assert nombres[-1] == final
    assert progreso.actual(con, "obra-x")["fase"] == final


def test_con_hasta_capitulo_termina_esperando_revision(con, tmp_path):
    novela.escribir(con, "obra-x", ficha(), _agentes(), hasta_capitulo=1,
                    carpeta_de_reglas=str(tmp_path))
    assert progreso.actual(con, "obra-x")["fase"] == "esperando_revision"
    assert "en_la_puerta" not in [f[0] for f in _fases(con)]


def test_una_generacion_parada_dice_parada_y_su_motivo(con, tmp_path):
    agentes = _agentes()
    agentes["planificador"] = _Fijo({"titulo": "t", "premisa": "p", "plan": {"roto": True}})
    agentes["revisor"] = _Fijo({"aprobado": False, "objeciones": ["no vale (inventado)"]})
    with pytest.raises(Exception):
        novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    actual = progreso.actual(con, "obra-x")
    assert actual["fase"] == "parada"
    assert actual["motivo"], "una parada sin motivo no dice que arreglar"


def test_una_parada_del_capitulo_dice_parada_con_el_motivo_de_la_generacion(con, tmp_path):
    agentes = _agentes()
    # Un Escritor que no devuelve delta: el contrato lo rechaza hasta agotar los intentos.
    agentes["escritor"] = _Fijo({"texto": "sin delta"})
    r = novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    assert r["generacion"].parada is not None
    actual = progreso.actual(con, "obra-x")
    assert actual["fase"] == "parada"
    assert actual["motivo"] == str(r["generacion"].parada["motivo"])
