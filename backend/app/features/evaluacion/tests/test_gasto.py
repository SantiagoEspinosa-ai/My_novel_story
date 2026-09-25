"""`PLAN-31` E5: el libro de gasto de la evaluacion y el techo (`SPEC-31` `RF-06`).

El techo se comprueba **contra lo gastado**, nunca contra una prevision: el coste de una
novela con el pipeline actual esta sin medir. Y un total con delegaciones sin coste es un
suelo, y se dice donde se enseña el numero.
"""

import json
import pathlib
import sqlite3

import pytest

from app.commons import config
from app.commons.configuracion import carga
from app.features.evaluacion import repository as libro


@pytest.fixture
def con():
    return sqlite3.connect(":memory:")


def _anotar(con, ejecucion="brief-base-antes-1", capitulo="1", usd=1.0, delegaciones=5,
            sin_coste=0, **kw):
    libro.anotar(con, ejecucion=ejecucion, brief=kw.get("brief", "brief-base"),
                 pasada=kw.get("pasada", "antes"), capitulo=capitulo, usd=usd,
                 delegaciones=delegaciones, sin_coste=sin_coste)


def test_no_empieza_una_ejecucion_con_el_techo_alcanzado(con):
    assert libro.puede_empezar(con, techo=150)
    _anotar(con, capitulo="1", usd=100.0)
    _anotar(con, capitulo="2", usd=49.0)
    assert libro.puede_empezar(con, techo=150)
    _anotar(con, capitulo="3", usd=1.5)
    assert not libro.puede_empezar(con, techo=150), "150,5 gastados de 150"


def test_con_delegaciones_sin_coste_el_total_se_informa_como_suelo(con):
    _anotar(con, capitulo="1", usd=2.0, delegaciones=5, sin_coste=0)
    _anotar(con, capitulo="2", usd=1.5, delegaciones=5, sin_coste=2)
    total = libro.gastado(con)
    assert total.usd == 3.5 and total.delegaciones == 10 and total.sin_coste == 2
    assert total.es_suelo
    texto = libro.texto_del_total(total)
    assert "3.5000 USD" in texto and "SUELO" in texto and "2 delegaciones sin coste" in texto


def test_un_tramo_sin_ninguna_delegacion_con_coste_se_guarda_sin_medir(con):
    """Un cero ahi se leeria como un tramo gratis."""
    _anotar(con, capitulo="plan", usd=0.0, delegaciones=3, sin_coste=3)
    fila = libro.filas(con)[0]
    assert fila["usd"] is None
    assert libro.texto_del_total(libro.gastado(con)).startswith("sin medir")


def test_anotar_dos_veces_el_mismo_tramo_suma_los_dos_gastos(con):
    """`F-119`: esta prueba decia lo contrario -«anotar dos veces no lo suma»-, y esa regla
    es la que, al reanudar, dejo que los capitulos saltados pisaran lo medido. Se reescribe:
    cada anotacion es gasto nuevo (el intento parado y el que termina), y lo que no gasto
    nada no se anota."""
    _anotar(con, capitulo="1", usd=1.0)
    _anotar(con, capitulo="1", usd=1.0)
    assert libro.gastado(con).usd == 2.0



def test_la_pasada_es_antes_o_despues(con):
    with pytest.raises(ValueError):
        _anotar(con, pasada="durante")


def test_el_mayor_coste_de_una_novela_completa_es_sin_medir_hasta_que_haya_una(con):
    """Una ejecucion sin `cierre` no es una novela completa: su coste no sirve de medida
    de lo que cuesta una."""
    _anotar(con, ejecucion="a", capitulo="1", usd=4.0)
    assert libro.mayor_coste_de_novela_completa(con) is None
    _anotar(con, ejecucion="b", capitulo="1", usd=3.0)
    _anotar(con, ejecucion="b", capitulo="cierre", usd=1.0)
    assert libro.mayor_coste_de_novela_completa(con) == 4.0


def test_el_techo_es_una_decision_de_presupuesto_de_121_usd():
    """`SPEC-31`: lo fija el autor. No es una medida y no caduca con nada. v6 (2026-09-25): el
    autor lo baja de 150 a 121 para que el libro pare en sus 150 reales, porque 28,86 USD de lo
    gastado no pasan por el libro. La prueba se reescribio con el valor, no se borro."""
    assert config.TECHO_DE_GASTO_EVALUACION_USD == 121
    assert carga.cargar_sistema().evaluacion.techo_de_gasto_usd == 121
    fuente = (pathlib.Path(config.__file__)).read_text(encoding="utf-8")
    bloque = fuente[:fuente.index("TECHO_DE_GASTO_EVALUACION_USD")].rsplit("\n\n", 1)[-1]
    assert "presupuesto" in bloque and "no medida" in bloque
    sistema = json.loads((pathlib.Path(carga.__file__).resolve().parents[3] / "config"
                          / "sistema.json").read_text(encoding="utf-8"))
    assert sistema["evaluacion"]["techo_de_gasto_usd"] == 121
