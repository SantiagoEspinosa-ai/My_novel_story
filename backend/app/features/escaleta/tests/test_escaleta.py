"""C2 — La escaleta, y las invariantes "en su forma prevista".

El Escaletador comprueba `INV-01`, `INV-07`, `INV-12` e `INV-16` **contra la
`Escaleta`, antes de que exista ningun texto**. Es la misma invariante sobre el
plan en vez de sobre la obra, y por eso **no sustituye** a la comprobacion del
Auditor: un plan correcto que se ejecuta mal sigue fallando.
"""

import pytest

from app.features.escaleta import plan


def test_una_escena_planificada_sin_cambio_de_valor_no_pasa():
    """`INV-01` en su forma prevista. El caso negativo."""
    with pytest.raises(plan.EscaletaInvalida, match="INV-01"):
        plan.validar([{"id": "esc-1", "cambio_de_valor": None, "beats": ["b1"]}])


def test_una_escena_sin_beat_que_sirva_a_un_arco_no_pasa():
    """`INV-07` en su forma prevista."""
    with pytest.raises(plan.EscaletaInvalida, match="INV-07"):
        plan.validar([{"id": "esc-1",
                       "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
                       "beats": []}])


def test_un_eje_fuera_de_la_enumeracion_no_pasa():
    with pytest.raises(plan.EscaletaInvalida):
        plan.validar([{"id": "esc-1",
                       "cambio_de_valor": {"eje": "dinero", "signo": "negativo"},
                       "beats": ["b1"]}])


def test_una_escaleta_valida_pasa():
    escenas = [{"id": "esc-1",
                "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
                "beats": ["b1"]}]
    assert plan.validar(escenas) == escenas


def test_la_forma_prevista_no_sustituye_al_barrido():
    """Lo dice el documento y aqui queda como prueba: son dos momentos."""
    assert plan.INVARIANTES_PREVISTAS == ("INV-01", "INV-07", "INV-12", "INV-16")
    assert plan.SUSTITUYE_AL_AUDITOR is False


def test_una_obra_que_no_es_de_terror_no_preve_la_curva_de_miedo():
    """`SPEC-26` `RF-20`: `INV-12` e `INV-16` son del plano Terror."""
    assert plan.invariantes_previstas("aventura") == ("INV-01", "INV-07")
    assert plan.invariantes_previstas("terror") == (
        "INV-01", "INV-07", "INV-12", "INV-16")
