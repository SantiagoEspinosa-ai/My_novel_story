"""El prompt: lo que lleva y lo que no.

Existe porque `prompt.py` no tenia ninguna prueba y se quedo roto un rato sin
que nada fallara: ningun test lo importaba. Un modulo sin prueba no es un
modulo verificado, es uno que nadie ha ejecutado.
"""

from app.features.generacion import prompt


def _p(**kw):
    base = dict(parametros={"genero": "terror"}, estado={"marta": "viva"},
                objetivo="Marta baja al sotano")
    base.update(kw)
    return prompt.construir(**base)


def test_lleva_los_identificadores_disponibles():
    """Sin saber que ids existen, se le pide lo imposible."""
    texto = _p(personajes=["per-marta"], hechos=["hec-reloj"])
    assert "per-marta" in texto and "hec-reloj" in texto


def test_sin_identificadores_lo_dice_en_vez_de_callar():
    assert "(ninguno)" in _p()


def test_no_lleva_las_reglas_del_proyecto():
    """El Escritor escribe; quien comprueba es otro."""
    texto = _p()
    for prohibido in ("INV-", "bloqueante", "invariante"):
        assert prohibido not in texto


def test_los_problemas_del_intento_anterior_entran_en_el_prompt():
    """En la otra rama el aviso lo leia el orquestador y no el escritor."""
    texto = _p(problemas=[{"invariante": "INV-17", "descripcion": "944 palabras"}])
    assert "944 palabras" in texto


def test_el_mismo_contexto_da_el_mismo_hash():
    """Si no fuera determinista, el hash no detectaria nada."""
    assert prompt.hash_de(_p()) == prompt.hash_de(_p())
    assert prompt.hash_de(_p()) != prompt.hash_de(_p(objetivo="otra cosa"))
