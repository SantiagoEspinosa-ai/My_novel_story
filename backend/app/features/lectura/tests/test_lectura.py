"""D1 — Las consultas, con las dos reglas de presentacion que son contrato.

`RF-23`: una escena se devuelve siempre con su **estado** y sus **hallazgos
abiertos**. Nunca el texto solo: un texto suelto induce a darlo por bueno, que
es exactamente el fallo que las puertas evitan.

`RF-25`: un dato que no se ha medido se devuelve **ausente y distinguible de
cero**. Un cero se lee como un dato y un hueco no.
"""

from app.features.lectura import vista


def test_una_escena_nunca_se_devuelve_sin_estado_ni_hallazgos():
    v = vista.escena({"id": "e1", "texto": "La puerta.", "estado": "en_revision"},
                     hallazgos=[{"invariante": "INV-07", "severidad": "mayor"}])
    assert v["estado"] == "en_revision"
    assert len(v["hallazgos_abiertos"]) == 1


def test_una_escena_sin_hallazgos_devuelve_lista_vacia_no_ausencia():
    """Vacia es informacion: "se miro y no habia". Ausente seria "no se sabe"."""
    v = vista.escena({"id": "e1", "texto": "x", "estado": "aceptada"}, hallazgos=[])
    assert v["hallazgos_abiertos"] == []


def test_una_escena_rendida_se_distingue_de_una_aceptada_limpia():
    """`SPEC-10`: el delta de una escena rendida entra igual al canon."""
    v = vista.escena({"id": "e1", "texto": "x", "estado": "aceptada_por_rendicion"},
                     hallazgos=[{"invariante": "INV-07", "severidad": "mayor"}])
    assert v["estado"] == "aceptada_por_rendicion"
    assert v["se_acepto_rindiendose"] is True


def test_un_dato_sin_medir_sale_ausente_y_no_en_cero():
    """El caso negativo de `VER-19`."""
    sin = vista.consumo({"tokens_declarados": None})
    con_cero = vista.consumo({"tokens_declarados": 0})
    assert sin["tokens"] == "sin medir"
    assert con_cero["tokens"] == 0


def test_un_trabajo_devuelve_intentos_y_el_motivo_del_ultimo_fallo():
    """`RF-24` con la respuesta de `SPEC-08`: el ultimo, no el historial."""
    v = vista.trabajo({"id": "t1", "estado": "fallido", "intentos": 3,
                       "motivo_ultimo_fallo": "delta fuera de esquema"})
    assert v["intentos"] == 3
    assert v["motivo_ultimo_fallo"] == "delta fuera de esquema"
    assert "historial" not in v
