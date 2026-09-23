"""VER-62 — El modelo no cambia dentro de una obra.

El caso negativo es el que importa y ya no es hipotetico: un modelo puede
enrutar a otro por sus propias salvaguardas, asi que el cambio ocurre sin que
nadie lo pida.
"""

import pytest

from app.commons.modelo import modelo_fijo, traza as modulo_traza


def _t(trabajo, modelo):
    return modulo_traza.nueva(agente="escritor", escena="e1", trabajo=trabajo,
                              modelo=modelo)


def test_todas_con_el_mismo_modelo_no_hay_discrepancia():
    disc, sin = modelo_fijo.comprobar("fable", [_t("t1", "fable"), _t("t2", "fable")])
    assert disc == [] and sin == []


def test_caso_negativo_una_delegacion_enrutada_a_otro_modelo():
    """Lo que las salvaguardas del modelo pueden hacer sin avisar."""
    disc, _ = modelo_fijo.comprobar("fable", [_t("t1", "fable"), _t("t2", "opus")])
    assert len(disc) == 1
    assert disc[0].encontrado == "opus" and disc[0].esperado == "fable"


def test_exigir_levanta_y_dice_por_que_importa():
    with pytest.raises(modelo_fijo.ModeloCambiado, match="no son comparables"):
        modelo_fijo.exigir("fable", [_t("t1", "opus")])


def test_una_traza_sin_modelo_no_cuenta_como_conformidad():
    """Decir que todo cuadra con media muestra vacia es lo que `RF-25` prohibe."""
    disc, sin = modelo_fijo.comprobar("fable", [_t("t1", "fable"), _t("t2", None)])
    assert disc == []
    assert sin == ["t2"], "se devuelve aparte, no se da por bueno"
