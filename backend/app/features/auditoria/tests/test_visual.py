"""`PLAN-22` E13b (`VER-119`): el veredicto del inspector visual, `INV-30`.

El inspector es un agente: su respuesta se valida con esquema y, si no se puede leer, es
`sin_veredicto`, **nunca** `pasa` (Regla 8). Una pieza que falla deja un hallazgo `INV-30`
con su motivo.
"""

import pytest

from app.features.auditoria import visual

BUENO = {"comprobaciones": [
    {"pieza": p, "veredicto": "pasa", "motivo": "se ve bien (inventado)"}
    for p in visual.PIEZAS]}


def _con(pieza, veredicto, motivo="motivo inventado"):
    v = {"comprobaciones": [dict(c) for c in BUENO["comprobaciones"]]}
    for c in v["comprobaciones"]:
        if c["pieza"] == pieza:
            c.update(veredicto=veredicto, motivo=motivo)
    return v


def test_un_veredicto_limpio_pasa_y_no_deja_hallazgo():
    r = visual.juzgar(BUENO)
    assert r.estado == "pasa" and r.hallazgo is None
    assert [c.pieza for c in r.comprobaciones] == list(visual.PIEZAS)


def test_una_pieza_que_falla_deja_inv30_abierto_con_su_motivo():
    r = visual.juzgar(_con("fichas", "falla", "un enlace lleva al capitulo 3 y dice 2"))
    assert r.estado == "falla"
    assert r.hallazgo["invariante"] == "INV-30"
    assert r.hallazgo["estado"] == "abierto" and r.hallazgo["severidad"] == "mayor"
    assert "fichas" in r.hallazgo["descripcion"] and "capitulo 3" in r.hallazgo["descripcion"]


@pytest.mark.parametrize("bruto", [
    None, "no es json", {}, {"comprobaciones": []},
    {"comprobaciones": BUENO["comprobaciones"][:4]},
    {"comprobaciones": BUENO["comprobaciones"] + [BUENO["comprobaciones"][0]]},
    _con("indice", "quizas"),
    _con("indice", "pasa", ""),
    {"comprobaciones": BUENO["comprobaciones"], "extra": 1},
], ids=["nada", "texto", "vacio", "sin_piezas", "falta_una", "repetida",
        "veredicto_fuera", "sin_motivo", "campo_de_mas"])
def test_un_veredicto_ilegible_es_sin_veredicto_y_no_pasa(bruto):
    r = visual.juzgar(bruto)
    assert r.estado == "sin_veredicto"
    assert r.comprobaciones == []
    assert r.hallazgo["invariante"] == "INV-30" and r.hallazgo["estado"] == "sin_veredicto"


def test_el_prompt_pide_la_url_las_cinco_piezas_y_el_json():
    p = visual.prompt("http://localhost:5199/obras/obra-x")
    assert "http://localhost:5199/obras/obra-x" in p
    for pieza in visual.PIEZAS:
        assert pieza in p
    assert '"comprobaciones"' in p and "captura" in p and "consola" in p
