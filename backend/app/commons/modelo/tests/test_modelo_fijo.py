"""VER-62 — El modelo no cambia dentro de una obra.

El caso negativo es el que importa y ya no es hipotetico: un modelo puede
enrutar a otro por sus propias salvaguardas, asi que el cambio ocurre sin que
nadie lo pida.
"""

import pytest

from app.commons.modelo import modelo_fijo, traza as modulo_traza


def _t(trabajo, modelos):
    t = modulo_traza.nueva(agente="escritor", escena="e1", trabajo=trabajo)
    t.modelos = modelos
    return t


FABLE = ["claude-fable-5-1", "claude-haiku-4-5-20251001"]


def test_el_mismo_conjunto_en_todas_no_hay_discrepancia():
    """Una delegacion usa un conjunto, no un modelo: se midio `fable` + `haiku`."""
    disc, sin = modelo_fijo.comprobar([_t("t1", FABLE), _t("t2", list(reversed(FABLE)))])
    assert disc == [] and sin == [], "el orden no importa, el conjunto si"


def test_caso_negativo_el_conjunto_cambia_a_mitad_de_obra():
    """Si la escena 3 usa un conjunto y la 40 otro, dejan de ser comparables."""
    disc, _ = modelo_fijo.comprobar([_t("t1", FABLE), _t("t2", ["claude-opus-5"])])
    assert len(disc) == 1
    assert disc[0].encontrado == ("claude-opus-5",)


def test_no_se_compara_contra_el_declarado_porque_nunca_coincidiria():
    """El declarado es `fable` y el reportado `claude-fable-5-1`: manda el canonico."""
    disc, _ = modelo_fijo.comprobar([_t("t1", FABLE), _t("t2", FABLE)])
    assert disc == []


def test_exigir_levanta_y_dice_por_que_importa():
    with pytest.raises(modelo_fijo.ModeloCambiado, match="no son comparables"):
        modelo_fijo.exigir([_t("t1", FABLE), _t("t2", ["claude-opus-5"])])


def test_una_traza_sin_modelo_no_cuenta_como_conformidad():
    """Decir que todo cuadra con media muestra vacia es lo que `RF-25` prohibe."""
    disc, sin = modelo_fijo.comprobar([_t("t1", FABLE), _t("t2", None)])
    assert disc == []
    assert sin == ["t2"], "se devuelve aparte, no se da por bueno"
