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


# --- La otra mitad del par: con que BRIEF se genero -----------------------

def test_la_base_registra_con_que_brief_se_genero(con):
    """`procedencia` ya decia **con que codigo**. Con el brief dice tambien
    **con que forma de obra**, y con las dos una tanda se puede repetir
    exactamente en vez de aproximadamente."""
    procedencia.registrar(con, version="aaaaaaa", brief="huella123456")
    p = procedencia.leer(con)
    assert p["version"] == "aaaaaaa"
    assert p["brief"] == "huella123456"


def test_una_base_sin_brief_lo_dice(con):
    """Las anteriores a esto no lo llevan, y leer esa ausencia como "el mismo
    brief" seria el silencio de siempre (Regla 8)."""
    procedencia.registrar(con, version="aaaaaaa")
    assert procedencia.leer(con)["brief"] is None


def test_se_avisa_si_la_tanda_corrio_con_otro_brief(con):
    """Mismo codigo y distinta forma de obra **no es la misma tanda**, y
    comparar sus numeros seria comparar dos novelas distintas."""
    procedencia.registrar(con, version="aaaaaaa", brief="huella-A")
    aviso = procedencia.comprobar(con, version="aaaaaaa", brief="huella-B")
    assert aviso is not None
    assert "huella-A" in aviso and "huella-B" in aviso


def test_el_brief_tampoco_se_pisa(con):
    procedencia.registrar(con, version="aaaaaaa", brief="huella-A")
    procedencia.registrar(con, version="aaaaaaa", brief="huella-B")
    assert procedencia.leer(con)["brief"] == "huella-A"


def test_tambien_consta_con_que_configuracion_de_sistema_corrio(con):
    """`MF-28`: dos artefactos con el mismo commit y **distinta configuracion**
    eran indistinguibles. El brief ya constaba; el sistema -modelos, topes,
    techo- no, y es lo que explica por que dos tandas de la misma novela dieron
    numeros distintos."""
    procedencia.registrar(con, version="aaaaaaa", brief="huella-B",
                          sistema="huella-S")
    p = procedencia.leer(con)
    assert p["sistema"] == "huella-S"


def test_cambiar_de_modelo_no_es_la_misma_tanda(con):
    """Mismo codigo, mismo brief y otro modelo **no se puede comparar**: el
    coste y la calidad cambian por el modelo, no por la novela."""
    procedencia.registrar(con, version="aaaaaaa", brief="B", sistema="S1")
    aviso = procedencia.comprobar(con, version="aaaaaaa", brief="B", sistema="S2")
    assert aviso is not None and "S1" in aviso and "S2" in aviso


def test_una_base_sin_huella_de_sistema_lo_dice(con):
    procedencia.registrar(con, version="aaaaaaa")
    assert procedencia.leer(con)["sistema"] is None
