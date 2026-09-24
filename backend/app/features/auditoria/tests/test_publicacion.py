"""`SPEC-30` v4, `PLAN-30` E4: la decision de la puerta de publicacion.

Funcion pura sobre datos ya resueltos, como `capitulo.cerrar`: no lee la base ni
ejecuta Lean. Cada condicion de `RF-01` tiene su caso que la dispara y su negativo.
"""

from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad as S
from app.features.auditoria.publicacion import ResultadoLean, decidir

LIMPIO = ResultadoLean(codigo=0)


def _h(invariante, severidad, estado=EH.ABIERTO, capitulo="cap-03"):
    return {"invariante": invariante, "severidad": severidad, "estado": estado,
            "capitulo": capitulo, "descripcion": "algo de " + invariante}


def _invariantes(d):
    return [c.invariante for c in d.condiciones]


def test_todo_limpio_publica():
    d = decidir(rendidos=[], hallazgos=[], lean=LIMPIO)
    assert d.publica and d.condiciones == []


def test_un_capitulo_rendido_no_publica_y_lo_nombra():
    """`INV-29`. Una decision nuestra, mas estricta que el enunciado: un capitulo
    que se rindio no es un capitulo que paso."""
    d = decidir(rendidos=["cap-02"], hallazgos=[], lean=LIMPIO)
    assert not d.publica
    c = d.condiciones[0]
    assert (c.invariante, c.capitulo, c.reintentable) == ("INV-29", "cap-02", False)


def test_una_bloqueante_de_obra_abierta_no_publica():
    d = decidir(rendidos=[], hallazgos=[_h("INV-24", S.BLOQUEANTE, capitulo=None)], lean=LIMPIO)
    assert not d.publica and _invariantes(d) == ["INV-24"]


def test_una_vetada_en_un_capitulo_no_publica():
    d = decidir(rendidos=[], hallazgos=[_h("INV-21", S.BLOQUEANTE)], lean=LIMPIO)
    assert not d.publica and _invariantes(d) == ["INV-21"]


def test_lean_1_no_publica():
    d = decidir(rendidos=[], hallazgos=[], lean=ResultadoLean(
        codigo=1, violaciones=[{"invariante": "L-1", "eventos": ["ev-2", "ev-1"]}]))
    assert not d.publica and _invariantes(d) == ["INV-28"]


def test_el_2_de_lean_bloquea_igual_que_el_1():
    """`RF-09`: «no habia bastante dato para mirar» no es «se miro y esta bien»."""
    d = decidir(rendidos=[], hallazgos=[], lean=ResultadoLean(codigo=2))
    assert not d.publica and _invariantes(d) == ["INV-28"]
    assert "sin veredicto" in d.condiciones[0].detalle


def test_lean_no_disponible_no_publica_y_no_es_reintentable():
    d = decidir(rendidos=[], hallazgos=[], lean=ResultadoLean(codigo=None))
    assert not d.publica
    assert not d.condiciones[0].reintentable


def test_un_fallo_de_lean_no_es_reintentable():
    """`C-2`: lo que Lean mira lo fija el plan, asi que reescribir la prosa no lo
    arregla. Vuelve al Editor y la generacion se detiene."""
    d = decidir(rendidos=[], hallazgos=[], lean=ResultadoLean(codigo=1))
    assert d.condiciones[0].reintentable is False


def test_un_inv27_abierto_no_publica():
    d = decidir(rendidos=[], hallazgos=[_h("INV-27", S.MAYOR)], lean=LIMPIO)
    assert not d.publica
    c = d.condiciones[0]
    assert (c.invariante, c.reintentable) == ("INV-27", True)


def test_un_inv27_sin_veredicto_no_publica():
    d = decidir(rendidos=[], hallazgos=[_h("INV-27", S.MAYOR, EH.SIN_VEREDICTO)], lean=LIMPIO)
    assert not d.publica and _invariantes(d) == ["INV-27"]


def test_un_menor_de_obra_no_bloquea():
    d = decidir(rendidos=[], hallazgos=[_h("INV-25", S.MENOR, capitulo=None)], lean=LIMPIO)
    assert d.publica


def test_un_mayor_de_capitulo_de_un_intento_anterior_no_bloquea():
    """`RF-01`.2 solo pide que no quede ninguna `bloqueante`; los `mayor` de escena
    ya los decidio la puerta de escena, y los de hoy nunca se cierran (hallazgo 2)."""
    d = decidir(rendidos=[], hallazgos=[_h("INV-26", S.MAYOR)], lean=LIMPIO)
    assert d.publica


def test_inv06_sale_como_no_ejecutada_y_no_bloquea():
    """`RF-12` (`C-4`): una decision nuestra, con su motivo, y visible."""
    d = decidir(rendidos=[], hallazgos=[], lean=LIMPIO)
    assert d.publica
    assert [n.invariante for n in d.no_ejecutadas] == ["INV-06"]
    assert "semantica" in d.no_ejecutadas[0].motivo


def test_se_listan_todas_las_condiciones_que_fallan_no_solo_la_primera():
    """`RF-04` informa de todo lo que falto, no de lo primero que encontro."""
    d = decidir(rendidos=["cap-01"], hallazgos=[_h("INV-24", S.BLOQUEANTE, capitulo=None),
                                                _h("INV-27", S.MAYOR)],
                lean=ResultadoLean(codigo=2))
    assert sorted(_invariantes(d)) == ["INV-24", "INV-27", "INV-28", "INV-29"]
