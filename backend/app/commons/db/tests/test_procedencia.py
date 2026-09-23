"""Con que codigo se genero esta base.

EL CASO QUE LO ABRIO
---------------------
Una obra de diez capitulos arranco antes de que `uso_de_hecho` existiera. Su
proceso importo los modulos al lanzarse, asi que durante una hora estuvo
escribiendo con **codigo anterior al del arbol**. Preguntarle despues a esa
base *"que escenas leyeron este hecho"* habria devuelto una lista vacia
indistinguible de "ninguna" — y ese cero no se enseñaria, **se mediria**.

Lo que faltaba no era una comprobacion: era que **la base no guarda con que
codigo se escribio**. La traza guarda el modelo y `VER-62` vigila que sea
estable; del harness no habia nada.
"""

import sqlite3

import pytest

from app.commons.db import procedencia


@pytest.fixture
def con():
    return sqlite3.connect(":memory:")


def test_una_base_nueva_registra_con_que_codigo_se_creo(con):
    procedencia.registrar(con)
    p = procedencia.leer(con)
    assert p["version"], "algo tiene que constar"
    assert p["creada_en"]


def test_lo_que_no_se_puede_determinar_se_dice_y_no_se_inventa(con):
    """Si no hay repositorio, la version no se rellena con un valor plausible:
    un dato inventado que queda escrito ya no se distingue de uno medido."""
    procedencia.registrar(con, version=None)
    assert procedencia.leer(con)["version"] == procedencia.SIN_DETERMINAR


def test_la_primera_version_no_se_pisa(con):
    """Con que codigo se **creo** la base, no con cual se abrio la ultima vez.
    Sobrescribir contestaria la pregunta equivocada."""
    procedencia.registrar(con, version="aaaaaaa")
    procedencia.registrar(con, version="bbbbbbb")
    assert procedencia.leer(con)["version"] == "aaaaaaa"


def test_se_avisa_si_la_base_se_escribio_con_otro_codigo(con):
    procedencia.registrar(con, version="aaaaaaa")
    aviso = procedencia.comprobar(con, version="bbbbbbb")
    assert aviso is not None
    assert "aaaaaaa" in aviso and "bbbbbbb" in aviso


def test_sin_discrepancia_no_se_avisa_de_nada(con):
    procedencia.registrar(con, version="aaaaaaa")
    assert procedencia.comprobar(con, version="aaaaaaa") is None


def test_una_base_sin_procedencia_no_es_lo_mismo_que_una_coincidente(con):
    """Regla 8: la ausencia del dato no puede leerse como conformidad. Las
    bases anteriores a esto no tienen fila, y eso hay que decirlo."""
    aviso = procedencia.comprobar(con, version="aaaaaaa")
    assert aviso is not None
    assert "no consta" in aviso.lower()
