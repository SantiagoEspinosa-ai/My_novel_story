"""D2 — La maquina de estados: la unica feature autorizada a componer otras.

`VER-28`: no existe ningun camino de `planificada` a `consolidada` que no pase
por `en_verificacion`. Se comprueba **explorando la maquina entera**, no
probando un camino: un camino que pasa no dice nada de los otros.
"""

import pytest

from app.commons.dominio.enumeraciones import EstadoDeEscena as E
from app.features.orquestacion import maquina


def test_ningun_camino_de_planificada_a_consolidada_salta_la_puerta():
    """El caso negativo de `VER-28`, por exploracion exhaustiva."""
    caminos = maquina.todos_los_caminos(E.PLANIFICADA, E.CONSOLIDADA)
    assert caminos, "tiene que haber al menos un camino"
    for c in caminos:
        assert E.EN_VERIFICACION in c, "camino que salta la puerta: {0}".format(
            [e.value for e in c])


def test_una_transicion_ilegal_se_rechaza():
    with pytest.raises(maquina.TransicionIlegal):
        maquina.mover(E.PLANIFICADA, E.CONSOLIDADA)


def test_no_hay_rendicion_desde_rechazada():
    """`SPEC-10`: una bloqueante no se rinde nunca. El delta de una escena
    rendida entra igual al canon."""
    assert E.ACEPTADA_POR_RENDICION not in maquina.destinos(E.RECHAZADA)


def test_hay_rendicion_desde_en_revision():
    assert E.ACEPTADA_POR_RENDICION in maquina.destinos(E.EN_REVISION)


def test_aceptar_lleva_a_consolidada_y_rendirse_es_terminal():
    """`SPEC-30` v4 `RF-11`: la rendicion no pasa a `consolidada`, porque ese
    paso la borraba. Que la escena rendida esta consolidada lo dice
    `escena_consolidada`, no el estado."""
    assert maquina.destinos(E.ACEPTADA) == {E.CONSOLIDADA}
    assert maquina.destinos(E.ACEPTADA_POR_RENDICION) == set()


def test_consolidada_es_terminal():
    assert maquina.destinos(E.CONSOLIDADA) == set()


def test_quien_dispara_cada_transicion_esta_declarado():
    """Si no se declara, `VER-29` no puede comprobar que el worker no acepte."""
    for (origen, destino), quien in maquina.DISPARADORES.items():
        assert quien, "{0} -> {1} no dice quien la dispara".format(origen, destino)
    assert maquina.DISPARADORES[(E.ACEPTADA, E.CONSOLIDADA)] == "Consolidador"
    assert maquina.DISPARADORES[(E.RECHAZADA, E.GENERADA)] == "Persona desde el frontend"
