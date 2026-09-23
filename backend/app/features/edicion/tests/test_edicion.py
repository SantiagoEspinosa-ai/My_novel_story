"""`SPEC-20`: que se puede editar a mano sin invalidar lo ya firmado.

LA REGLA, EN UNA FRASE
-----------------------
Se puede editar todo lo no consolidado, mas el plan. Se puede editar lo que
ninguna escena consolidada haya usado todavia. **El estado consolidado no se
toca a mano nunca.**

POR QUE EL ESTADO NO SE TOCA
-----------------------------
Es **derivado**: se reconstruye acumulando los deltas en orden y no se relee del
texto (`CLAUDE.md`). Un estado editado a mano deja de ser reconstruible, y a
partir de ahi nadie puede saber si el canon sale de la obra o de una correccion
que alguien hizo un martes.
"""

import sqlite3

import pytest

from app.features.edicion import permisos

# `A-02`: esta feature no importa de ninguna otra, **ni en sus pruebas**. Quien
# usa cada objeto llega como parametro, y quien lo calcula es `orquestacion/`
# -probado en `orquestacion/tests/`-. La primera version de este fichero
# importaba de `consolidacion` y de `escaleta` para sembrar el escenario, y el
# comprobador de importaciones lo cazó.
USADO = ["e1"]
LIBRE = []


@pytest.fixture
def con():
    return sqlite3.connect(":memory:")


def test_el_plan_siempre_se_puede_editar():
    """La escaleta es **entrada**, no resultado. Corregirla es replanificar.

    Se puede editar **aunque escenas consolidadas la hayan usado**: eso es
    replanificar, y el plan es lo unico que admite cambiarse con la obra en
    marcha."""
    assert permisos.se_puede_editar("escaleta", "cap-1", usado_por=USADO).permitido


def test_un_hecho_que_ninguna_escena_consolidada_uso_se_puede_editar():
    assert permisos.se_puede_editar("hecho", "hec-libre", usado_por=LIBRE).permitido


def test_un_hecho_que_una_escena_consolidada_uso_ya_no():
    """En cuanto una escena lo usa deja de ser editable: cambiarlo cambiaria
    retroactivamente lo que esa escena revelo."""
    assert not permisos.se_puede_editar("hecho", "hec-usado", usado_por=USADO).permitido


def test_el_veredicto_dice_quien_lo_impide_y_no_solo_que_no():
    """Un "no se puede" sin decir quien lo impide obliga a ir a buscarlo a
    mano, que es justo el coste que `F-38` existia para quitar."""
    v = permisos.se_puede_editar("hecho", "hec-usado", usado_por=USADO)
    assert v.usado_por == ["e1"]
    assert "e1" in v.motivo


def test_una_escena_no_consolidada_se_puede_editar():
    assert permisos.se_puede_editar("escena", "e2", usado_por=LIBRE).permitido


def test_una_escena_consolidada_no():
    assert not permisos.se_puede_editar("escena", "e1", usado_por=["e1"]).permitido


def test_el_estado_del_mundo_no_se_puede_editar_nunca():
    """Ni siquiera con la obra vacia: es derivado, y la via correcta para
    arreglarlo es rehacer la escena que lo produjo."""
    v = permisos.se_puede_editar("estado_del_mundo", "per-marta", usado_por=LIBRE)
    assert not v.permitido
    assert "derivado" in v.motivo or "delta" in v.motivo


def test_el_texto_de_un_borrador_tampoco():
    """Un borrador es lo que devolvio el agente. Editado deja de serlo, y
    `VER-60` -que compara el manuscrito con el borrador auditado- dejaria de
    significar nada."""
    assert not permisos.se_puede_editar("borrador", "e1", usado_por=LIBRE).permitido


def test_una_clase_desconocida_se_niega_en_vez_de_permitirse():
    """Lo que no se ha pensado no se autoriza: al reves, cada clase nueva del
    dominio nacería editable sin que nadie lo hubiera decidido."""
    v = permisos.se_puede_editar("cualquier_cosa_nueva", "x")
    assert not v.permitido


def test_una_edicion_deja_rastro_con_motivo(con):
    """Sin esto, una obra con diecisiete intervenciones es indistinguible de
    una que salio sola, y lo que `VER-64` mide deja de significar nada."""
    permisos.registrar_edicion(con, "hecho", "hec-libre", quien="santiago",
                               motivo="el enunciado decia sotano y era desvan")
    rastro = permisos.ediciones_de(con, "hecho", "hec-libre")
    assert len(rastro) == 1
    assert rastro[0]["quien"] == "santiago"
    assert "desvan" in rastro[0]["motivo"]


def test_registrar_sin_motivo_falla(con):
    with pytest.raises(ValueError, match="motivo"):
        permisos.registrar_edicion(con, "hecho", "hec-libre", quien="x", motivo=" ")


def test_registrar_algo_que_no_se_puede_editar_falla(con):
    """El rastro no legitima lo prohibido: si se pudiera registrar una edicion
    del estado consolidado, el registro seria la coartada."""
    with pytest.raises(permisos.EdicionProhibida):
        permisos.registrar_edicion(con, "estado_del_mundo", "per-marta",
                                   quien="x", motivo="lo arreglo a mano")
