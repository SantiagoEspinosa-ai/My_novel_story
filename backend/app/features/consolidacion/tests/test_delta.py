"""C5 — La consolidacion, que es donde se corta la propagacion del error.

`INV-05`: hasta que el delta no esta aplicado, el estado del mundo no ha
cambiado y la escena siguiente **no puede generarse**.

La prueba que abre el paso es la del delta a medias, porque es la unica
categoria de fallo de la que no se sale reintentando: los demas detienen el
trabajo y dejan el estado intacto; este lo corrompe, y todo lo que se genere
encima hereda la corrupcion sin que nada avise.
"""

import sqlite3

import pytest

from app.features.consolidacion import aplicar


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    aplicar.asegurar_tablas(c)
    aplicar.sembrar(c, {"marta": ("vivo", "salon")})
    return c


def test_un_delta_que_falla_a_mitad_no_deja_el_estado_a_medias(con):
    """LA prueba del paso. Atomicidad, no buena intencion."""
    delta = {
        "movimientos": [{"personaje": "marta", "a": "cocina"}],
        "cambios_de_estado_vital": [{"personaje": "nadie", "de": "vivo", "a": "muerto"}],
    }
    with pytest.raises(aplicar.DeltaIncompatible):
        aplicar.consolidar(con, "e1", delta)

    # El primer cambio no puede haber quedado escrito.
    assert aplicar.estado(con)["marta"] == ("vivo", "salon")


def test_un_delta_valido_se_aplica_entero(con):
    aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "marta", "a": "cocina"}]})
    assert aplicar.estado(con)["marta"] == ("vivo", "cocina")


def test_la_escena_siguiente_no_se_genera_sin_el_delta_aplicado(con):
    """`INV-05` e `INV-19` del proceso: la puerta que corta la propagacion."""
    assert aplicar.puede_generarse_la_siguiente(con, "e1") is False
    aplicar.consolidar(con, "e1", {"movimientos": []})
    assert aplicar.puede_generarse_la_siguiente(con, "e1") is True


def test_consolidar_dos_veces_la_misma_escena_no_duplica(con):
    aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "marta", "a": "cocina"}]})
    with pytest.raises(aplicar.YaConsolidada):
        aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "marta", "a": "sotano"}]})
    assert aplicar.estado(con)["marta"] == ("vivo", "cocina")
