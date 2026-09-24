"""`PLAN-22` E3 — portada e indice por la API (`SPEC-22` `RF-37`, `RF-38`, `RF-40`, `RF-46`).

El indice llega **resuelto**: por `capitulo.orden`, sin mezclar obras, con el estado de
cada capitulo y de cada escena, la rendicion ya decidida y los hallazgos abiertos de cada
escena con su estado. La interfaz no calcula nada (`NF-06`). `VER-104`.
"""

from app.features.lectura.tests.conftest import OBRA, OTRA


def test_el_indice_de_una_obra_de_dos_capitulos_pone_cada_escena_bajo_el_suyo_y_en_orden(cliente):
    r = cliente.get("/obras/{0}/indice".format(OBRA))
    assert r.status_code == 200, r.text
    capitulos = r.json()["capitulos"]
    assert [[e["id"] for e in c["escenas"]] for c in capitulos] == \
        [["esc-b1", "esc-b2"], ["esc-a1", "esc-a2"]]
    for c in capitulos:
        assert all(e["capitulo"] == c["id"] for e in c["escenas"])
        assert c["estado"] == "abierto"
    b1, b2 = capitulos[0]["escenas"]
    assert (b1["estado"], b1["se_acepto_rindiendose"], b1["hallazgos_abiertos"]) == \
        ("consolidada", False, [])
    assert (b2["estado"], b2["se_acepto_rindiendose"]) == ("aceptada_por_rendicion", True)
    assert [(h["invariante"], h["estado"]) for h in b2["hallazgos_abiertos"]] == \
        [("INV-17", "abierto")]
    a1 = capitulos[1]["escenas"][0]
    assert [(h["invariante"], h["estado"]) for h in a1["hallazgos_abiertos"]] == \
        [("INV-27", "sin_veredicto")], "un resuelto no es abierto; un sin_veredicto si cuenta"


def test_el_indice_ordena_por_capitulo_orden_y_no_por_id(cliente):
    capitulos = cliente.get("/obras/{0}/indice".format(OBRA)).json()["capitulos"]
    assert [(c["id"], c["orden"]) for c in capitulos] == [("cap-b", 1), ("cap-a", 2)]


def test_con_dos_obras_en_la_base_el_indice_no_mezcla_capitulos(cliente):
    mia = cliente.get("/obras/{0}/indice".format(OBRA)).json()
    ajena = cliente.get("/obras/{0}/indice".format(OTRA)).json()
    assert [c["id"] for c in mia["capitulos"]] == ["cap-b", "cap-a"]
    assert [c["id"] for c in ajena["capitulos"]] == ["cap-z"]
    assert [e["id"] for c in ajena["capitulos"] for e in c["escenas"]] == ["esc-z1"]


def test_un_id_de_obra_pedido_como_capitulo_da_404(cliente):
    """Los dos identificadores no se sustituyen (`RF-37`): un capitulo no es una obra."""
    assert cliente.get("/obras/cap-b/indice").status_code == 404
    assert cliente.get("/obras/no-existe/indice").status_code == 404


def test_la_portada_trae_la_dedicatoria_de_la_obra_y_nula_si_no_hay(cliente):
    mia = cliente.get("/obras/{0}/indice".format(OBRA)).json()
    ajena = cliente.get("/obras/{0}/indice".format(OTRA)).json()
    assert (mia["id"], mia["titulo"], mia["dedicatoria"]) == \
        (OBRA, "Titulo inventado", "Para nadie real")
    assert "dedicatoria" in ajena and ajena["dedicatoria"] is None
