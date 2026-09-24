"""`PLAN-29` E2: el limite de `SPEC-29`, escrito como tipos.

Lo que sube a Langfuse son estos cuatro modelos y nada mas. Un campo que no esta en la
columna izquierda de la tabla de la spec no se puede construir.
"""

import pydantic
import pytest

from app.commons.observabilidad import envio


def test_un_span_no_acepta_campos_fuera_de_la_lista():
    with pytest.raises(pydantic.ValidationError):
        envio.SpanEnviado(id="s1", traza="t1", nombre="escritor", tipo="rol",
                          respuesta="el texto del capitulo")
    with pytest.raises(pydantic.ValidationError):
        envio.SpanEnviado(id="s1", traza="t1", nombre="escritor", tipo="rol",
                          input="el prompt rellenado")


def test_un_dato_ausente_se_queda_ausente_y_no_en_cero():
    s = envio.SpanEnviado(id="s1", traza="t1", nombre="escritor", tipo="rol",
                          tokens_entrada=120, coste_usd=None)
    enviado = s.a_enviar()
    assert enviado["tokens_entrada"] == 120
    assert "coste_usd" not in enviado and "tokens_salida" not in enviado


def test_la_sesion_es_una_huella_opaca_y_estable_de_la_obra():
    a = envio.sesion_de("obra-irene-garcia")
    assert a == envio.sesion_de("obra-irene-garcia")
    assert a != envio.sesion_de("obra-otra")
    assert a.startswith("ses-") and len(a) == len("ses-") + 16
    assert "irene" not in a


def test_un_score_sin_veredicto_no_es_un_aprobado():
    s = envio.ScoreEnviado(traza="t1", nombre="INV-28", categoria="sin_veredicto")
    assert s.categoria is envio.Categoria.SIN_VEREDICTO
    assert s.categoria is not envio.Categoria.PASA
    with pytest.raises(pydantic.ValidationError):
        envio.ScoreEnviado(traza="t1", nombre="INV-28", categoria="aprobado_por_defecto")


def test_un_score_no_lleva_valor_y_categoria_a_la_vez():
    with pytest.raises(pydantic.ValidationError):
        envio.ScoreEnviado(traza="t1", nombre="INV-26.voz", valor=4, categoria="pasa")
    with pytest.raises(pydantic.ValidationError):
        envio.ScoreEnviado(traza="t1", nombre="INV-26.voz")


def test_el_termino_de_una_vetada_solo_viaja_si_es_global():
    """`RF-06`: una vetada de novela puede ser el nombre de una persona."""
    envio.ScoreEnviado(traza="t1", nombre="INV-21", categoria="falla", nivel="global",
                       termino="sangre")
    with pytest.raises(pydantic.ValidationError):
        envio.ScoreEnviado(traza="t1", nombre="INV-21", categoria="falla", nivel="novela",
                           termino="marisa")


def test_una_version_de_prompt_es_rol_huella_y_plantilla():
    v = envio.VersionDePrompt(rol="escritor", version="a1b2c3d4e5f6", plantilla="Eres...")
    assert v.a_enviar() == {"rol": "escritor", "version": "a1b2c3d4e5f6",
                            "plantilla": "Eres..."}
