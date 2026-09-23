"""B2 — El cliente del modelo y la traza, con la independencia que VER-41 pide.

LA PRUEBA QUE ABRE EL PASO
--------------------------
`tokens_declarados` no lo escribe el codigo que calcula `tokens_estimados`.
Si los dos salieran del mismo sitio, `VER-41` compararia un numero consigo
mismo: pasaria siempre, seria un eco, y `PC-8` dejaria de ser "los dos podrian
equivocarse igual" para ser "no hay segunda fuente" -que es peor y que ademas
nadie veria, porque el validador estaria en verde-.

Se comprueba de forma **estatica**, mirando quien escribe que, porque una
prueba de comportamiento no distingue dos numeros iguales por casualidad de
dos numeros iguales por construccion.
"""

import inspect
import re

import pytest

from app.commons.modelo import cliente, presupuesto, traza


def test_el_que_estima_no_escribe_el_declarado():
    """La condicion que impide el eco. `SPEC-08` C-4, regla 2.

    Busca **escrituras**, no menciones. La primera version de esta prueba
    buscaba la cadena suelta y fallo contra el docstring que explica por que el
    modulo no escribe ese campo: un validador que no distingue una cita de un
    uso marca el texto que explica el defecto. Es `F-15` de
    `docs/verification.md`, que se descubrio con los acentos graves de un
    documento y resulta valer igual para el codigo.
    """
    fuente = inspect.getsource(presupuesto)
    escrituras = re.findall(r"tokens_declarados\s*=[^=]", fuente)
    assert escrituras == [], (
        "el modulo que calcula la estimacion no puede escribir el campo que "
        "viene del proveedor: VER-41 compararia un numero consigo mismo"
    )


def test_el_declarado_se_copia_y_no_se_calcula():
    """Regla 1: si el proveedor no lo manda, queda **ausente**, no en cero."""
    t = traza.nueva(agente="escritor", escena="esc-1", trabajo="tr-1")
    traza.registrar_respuesta(t, respuesta={"texto": "hola"})   # sin `usage`
    assert t.tokens_declarados is None, "un cero se lee como un dato y un hueco no"

    t2 = traza.nueva(agente="escritor", escena="esc-1", trabajo="tr-1")
    traza.registrar_respuesta(t2, respuesta={"texto": "hola", "usage": {"total_tokens": 1234}})
    assert t2.tokens_declarados == 1234


def test_son_tres_numeros_y_no_dos():
    """`SPEC-12` C-3. El de recortar es una estimacion; los otros dos, exactos."""
    campos = set(traza.Traza.__dataclass_fields__)
    assert {"tokens_para_recortar", "tokens_reservados", "tokens_estimados",
            "tokens_declarados"} <= campos


def test_la_traza_registra_los_recortes_distinguiendo_reduccion_de_eliminacion():
    """`SPEC-11` C-2. Desde `SPEC-12` reducir y eliminar no son lo mismo."""
    t = traza.nueva(agente="escritor", escena="esc-1", trabajo="tr-1")
    traza.registrar_recorte(t, bloque="resumenes", clase="reduccion")
    traza.registrar_recorte(t, bloque="fichas", clase="eliminacion")
    assert [r.clase for r in t.recortes] == ["reduccion", "eliminacion"]
    with pytest.raises(ValueError):
        traza.registrar_recorte(t, bloque="x", clase="apaño")


def test_una_llamada_que_falla_tambien_deja_traza():
    """`T-2`. Y con la salida entera si fue fallo de contrato: es pequena,
    no se reconstruye, y es lo unico que permite diagnosticarlo."""
    t = traza.nueva(agente="escritor", escena="esc-1", trabajo="tr-1")
    traza.registrar_fallo(t, clase="contrato", salida='{"delta": ')
    assert t.resultado == "fallo"
    assert t.salida_fallida == '{"delta": '

    t2 = traza.nueva(agente="escritor", escena="esc-1", trabajo="tr-1")
    traza.registrar_fallo(t2, clase="transporte", salida=None)
    assert t2.salida_fallida is None


def test_la_traza_guarda_ids_y_no_texto():
    """`SPEC-08` C-3: los identificadores que entraron, con su `version_en_t`.

    El indice vectorial crece al consolidar y los empates KNN no tienen orden,
    asi que sin los ids no se sabe cuales entraron aunque su contenido siga ahi.
    """
    t = traza.nueva(agente="escritor", escena="esc-1", trabajo="tr-1")
    traza.registrar_entrada(t, fichas=[("per-marta", 7)], setups=["set-1"],
                            resumenes=["res-3"], prompt_hash="ab12")
    assert t.fichas == [("per-marta", 7)]
    assert t.prompt_hash == "ab12"
    assert not hasattr(t, "texto_del_contexto")


def test_los_reintentos_solo_son_de_transporte():
    """`O-3`: un fallo de contrato no se reintenta, repetirlo repite el error."""
    assert cliente.se_reintenta("transporte") is True
    assert cliente.se_reintenta("contrato") is False
