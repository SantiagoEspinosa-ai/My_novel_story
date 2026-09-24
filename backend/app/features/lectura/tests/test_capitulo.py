"""`PLAN-22` E4 — la lectura de un capitulo y de una escena (`SPEC-22` `RF-39`..`RF-41`, `VER-105`).

Ninguna escena sale sin su estado ni sus hallazgos, tampoco dentro de la lectura continua;
y su texto es **byte a byte** el del borrador elegido, con su version (`VER-60`).
"""

from app.features.lectura.tests.conftest import OBRA, TEXTO_ELEGIDO


def _capitulo(cliente, id_capitulo):
    r = cliente.get("/capitulos/{0}".format(id_capitulo))
    assert r.status_code == 200, r.text
    return r.json()


def test_ninguna_escena_de_la_lectura_de_un_capitulo_sale_sin_estado_ni_hallazgos(cliente):
    for id_capitulo in ("cap-b", "cap-a"):
        escenas = _capitulo(cliente, id_capitulo)["escenas"]
        assert escenas
        for e in escenas:
            assert e["estado"], e
            assert isinstance(e["hallazgos_abiertos"], list), e


def test_el_texto_de_cada_escena_es_byte_a_byte_el_del_borrador_elegido_con_su_version(cliente):
    b1 = _capitulo(cliente, "cap-b")["escenas"][0]
    assert b1["id"] == "esc-b1"
    # Elegida la version 1 aunque haya una 2: el elegido, no el ultimo.
    assert b1["borrador"] == {"version": 1, "texto": TEXTO_ELEGIDO}
    assert b1["borrador"]["texto"].encode("utf-8") == TEXTO_ELEGIDO.encode("utf-8")
    a1 = _capitulo(cliente, "cap-a")["escenas"][0]
    assert a1["borrador"]["version"] == 1, "sin elegido, el ultimo que hay"


def test_una_escena_planificada_sale_con_texto_nulo_y_su_estado(cliente):
    a2 = _capitulo(cliente, "cap-a")["escenas"][1]
    assert (a2["id"], a2["estado"], a2["borrador"]) == ("esc-a2", "planificada", None)
    assert a2["hallazgos_abiertos"] == []


def test_un_sin_veredicto_viaja_con_su_estado_y_no_como_abierto(cliente):
    a1 = cliente.get("/escenas/esc-a1").json()
    assert [(h["invariante"], h["estado"], h["severidad"]) for h in a1["hallazgos_abiertos"]] \
        == [("INV-27", "sin_veredicto", "mayor")]


def test_una_rendida_consolidada_sigue_saliendo_rendida(cliente):
    b2 = cliente.get("/escenas/esc-b2").json()
    assert (b2["estado"], b2["se_acepto_rindiendose"]) == ("aceptada_por_rendicion", True)


def test_get_escena_devuelve_lo_mismo_que_la_escena_dentro_del_capitulo(cliente):
    for id_capitulo in ("cap-b", "cap-a"):
        for e in _capitulo(cliente, id_capitulo)["escenas"]:
            assert cliente.get("/escenas/{0}".format(e["id"])).json() == e


def test_un_id_de_obra_pedido_como_capitulo_o_como_escena_da_404(cliente):
    """`RF-37`, por el lado del capitulo: la obra no es un capitulo."""
    assert cliente.get("/capitulos/{0}".format(OBRA)).status_code == 404
    assert cliente.get("/escenas/{0}".format(OBRA)).status_code == 404
    assert cliente.get("/escenas/cap-b").status_code == 404


def test_el_capitulo_trae_su_orden_y_estado_y_solo_sus_escenas(cliente):
    cap = _capitulo(cliente, "cap-a")
    assert (cap["id"], cap["orden"], cap["estado"]) == ("cap-a", 2, "abierto")
    assert [e["id"] for e in cap["escenas"]] == ["esc-a1", "esc-a2"]
