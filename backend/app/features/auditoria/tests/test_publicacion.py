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


# --- E7: que capitulos implica cada fallo -----------------------------------------

from app.features.auditoria.publicacion import capitulos_implicados  # noqa: E402

CAPITULOS = {"ev-1": "cap-02", "ev-2": "cap-03", "ev-3a": "cap-04", "ev-3b": "cap-05"}


def test_una_inversion_entre_cap02_y_cap03_implica_solo_cap03():
    """`L-1` se imputa al evento **posterior** en el discurso, con la misma regla que
    la puerta de capitulo: es donde el lector encuentra la inversion."""
    r = capitulos_implicados([{"invariante": "L-1", "eventos": ["ev-1", "ev-2"],
                               "detalle": "va antes"}], CAPITULOS, [])
    assert list(r.por_capitulo) == ["cap-03"]


def test_dos_lugares_a_la_vez_implica_los_dos_capitulos():
    r = capitulos_implicados([{"invariante": "L-3", "eventos": ["ev-3a", "ev-3b"],
                               "detalle": "en dos sitios"}], CAPITULOS, [])
    assert sorted(r.por_capitulo) == ["cap-04", "cap-05"]


def test_un_hallazgo_de_obra_implica_el_capitulo_donde_se_guardo():
    r = capitulos_implicados([], CAPITULOS, [
        {"invariante": "INV-27", "capitulo": "cap-10", "descripcion": "final abrupto"}])
    assert r.por_capitulo == {"cap-10": ["INV-27: final abrupto"]}


def test_un_evento_sin_capitulo_se_informa_y_no_se_pierde():
    r = capitulos_implicados([{"invariante": "L-1", "eventos": ["ev-1", "ev-9"],
                               "detalle": "va antes"}], CAPITULOS, [])
    assert r.por_capitulo == {}
    assert r.sin_capitulo == ["L-1: va antes"]


def test_un_capitulo_que_el_editor_no_juzgo_no_publica():
    """`F-113`, decision del autor (2026-09-24): un `INV-26` `sin_veredicto` -el Editor no
    devolvio un juicio legible- impide publicar. *«No auditarse nunca gana por defecto.»*
    Es el camino de `F-76` en `R0`: un capitulo aceptado sin que nadie lo juzgara."""
    d = decidir(rendidos=[], hallazgos=[_h("INV-26", S.MAYOR, estado=EH.SIN_VEREDICTO)],
                lean=LIMPIO)
    assert not d.publica
    c = d.condiciones[0]
    assert (c.invariante, c.capitulo, c.reintentable) == ("INV-26", "cap-03", True)


def test_una_nota_baja_del_editor_abierta_no_bloquea_la_publicacion():
    """El control: un `INV-26` abierto es un juicio que se hizo y dio nota baja; sigue
    siendo `mayor` y no impide publicar. Lo que impide es que no hubiera juicio."""
    d = decidir(rendidos=[], hallazgos=[_h("INV-26", S.MAYOR)], lean=LIMPIO)
    assert d.publica
