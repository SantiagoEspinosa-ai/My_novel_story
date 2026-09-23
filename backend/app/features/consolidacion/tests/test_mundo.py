"""F1 y F2 — El estado circula y el conocimiento se escribe.

Se prueban juntas porque la segunda no significa nada sin la primera: que
`INV-03` acepte en la escena 2 lo revelado en la 1 exige que el mundo de la 2
salga de los deltas y no de un fixture.
"""

import sqlite3

import pytest

from app.features.consolidacion import aplicar, mundo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    aplicar.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon"),
                        "per-ana": ("vivo", "lug-cocina")})
    mundo.sembrar_lugares(c, {"lug-salon": ["lug-cocina", "lug-sotano"],
                              "lug-cocina": ["lug-salon"], "lug-sotano": ["lug-salon"]})
    return c


def test_el_mundo_leido_refleja_el_delta_de_la_escena_anterior(con):
    """F1. Sin esto la escena 2 genera contra el mundo de la 1."""
    assert mundo.leer(con)["ubicaciones"]["per-marta"] == "lug-salon"
    aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "per-marta",
                                                    "a": "lug-sotano"}]})
    assert mundo.leer(con)["ubicaciones"]["per-marta"] == "lug-sotano"


def test_una_revelacion_queda_sabida_a_partir_de_su_escena(con):
    """F2. `INV-03` lo lee y hasta ahora nadie lo escribia."""
    assert mundo.leer(con)["conocimiento"] == {}
    aplicar.consolidar(con, "e1", {"revelaciones": [{"sujeto": "per-marta",
                                                     "hecho": "hec-llave"}]})
    c = mundo.leer(con)["conocimiento"]
    assert c[("per-marta", "hec-llave")]["desde"] == "e1"


def test_que_uno_lo_revele_no_hace_que_lo_sepa_otro(con):
    """Media novela de terror vive en esta distincion."""
    aplicar.consolidar(con, "e1", {"revelaciones": [{"sujeto": "per-marta",
                                                     "hecho": "hec-llave"}]})
    c = mundo.leer(con)["conocimiento"]
    assert ("per-marta", "hec-llave") in c
    assert ("per-ana", "hec-llave") not in c


def test_inv03_deja_de_bloquear_lo_que_ya_se_revelo(con):
    """La prueba que une F1 y F2: el circuito entero."""
    from app.features.verificacion import puertas

    escena = {"id": "e2", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
              "personajes_presentes": ["per-marta"], "lugar": "lug-salon"}
    delta = {"revelaciones": [{"sujeto": "per-marta", "hecho": "hec-llave"}]}

    antes = puertas.verificar(escena, delta, mundo.leer(con))
    assert any(h.invariante == "INV-03" for h in antes), "sin registro, bloquea"

    aplicar.consolidar(con, "e1", delta)
    despues = puertas.verificar(escena, delta, mundo.leer(con))
    assert not any(h.invariante == "INV-03" for h in despues), "con registro, pasa"


def test_el_conocimiento_no_sobrevive_a_un_delta_que_falla(con):
    """Va en la misma transaccion, o quedaria sabido algo que no paso."""
    with pytest.raises(aplicar.DeltaIncompatible):
        aplicar.consolidar(con, "e1", {
            "revelaciones": [{"sujeto": "per-marta", "hecho": "hec-llave"}],
            "movimientos": [{"personaje": "per-nadie", "a": "lug-salon"}]})
    assert mundo.leer(con)["conocimiento"] == {}
