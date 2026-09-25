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
    texto = _p(personajes=["per-marta"], ids_de_hechos=["hec-reloj"])
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


# --- SPEC-16 C-3 / Regla 5: el contrato dice que significan sus campos -----

def test_el_prompt_dice_que_significa_revelar_y_que_significa_actuar():
    """La causa de fondo de `F-31`: el prompt daba la **forma** de
    `revelaciones` y no su **significado**, asi que el modelo lo dedujo
    -correctamente- mientras el codigo suponia lo contrario. Las dos partes
    cumplian el contrato y el sistema estaba roto."""
    texto = prompt.construir(
        parametros={"escena": "e1", "longitud_objetivo": [300, 900]},
        estado={"contexto": []}, objetivo="{}", problemas=None,
        personajes=["per-marta"], ids_de_hechos=["hec-llave"])
    assert "acciones" in texto, "el campo tiene que existir en el contrato"
    minusculas = texto.lower()
    for significado in ("pasa a conocer", "sirviendose"):
        assert significado in minusculas, (
            "falta el significado de un campo: dar la forma sin el significado "
            "es lo que produjo F-31")


def test_el_prompt_dice_que_pov_se_planifico():
    """`SPEC-18` C-2, y la causa directa de `F-34`: no se lo deciamos, asi que
    el modelo eligio -y eligio mal-. Regla 4: exigir en el contrato lo que el
    prompt no pide es pedir lo imposible."""
    texto = prompt.construir(
        parametros={"escena": "e1", "longitud_objetivo": [300, 900],
                    "pov": "per-marta"},
        estado={"contexto": []}, objetivo="{}", problemas=None,
        personajes=["per-marta", "per-ana"], ids_de_hechos=[])
    assert "per-marta" in texto
    assert "pov_usado" in texto, "y hay que pedir que lo declare de vuelta"


def test_el_prompt_dice_que_hechos_tiene_que_establecer_esta_escena():
    """`SPEC-19` P-5, y la Regla 4 **por tercera vez**: `F-21` con los
    identificadores, `F-34` con el POV, y ahora los hechos a establecer.
    Exigir en el contrato lo que el prompt no pide produce un rechazo merecido
    e inutil, y el sistema se para por una causa que nadie nombro."""
    texto = prompt.construir(
        parametros={"escena": "e2", "longitud_objetivo": [300, 900],
                    "pov": "per-marta"},
        estado={"contexto": []}, objetivo="{}", problemas=None,
        personajes=["per-marta"], ids_de_hechos=["hec-sotano", "hec-llave"],
        establece=["hec-sotano"])
    assert "hec-sotano" in texto
    minusculas = texto.lower()
    assert "establec" in minusculas, "tiene que decir que hay que establecerlos"


def test_sin_hechos_que_establecer_el_prompt_no_lo_pide():
    """`establece[]` es opcional: la mayoria de escenas no prometen nada."""
    texto = prompt.construir(
        parametros={"escena": "e2", "pov": "per-marta"},
        estado={"contexto": []}, objetivo="{}", problemas=None,
        personajes=["per-marta"], ids_de_hechos=["hec-sotano"])
    assert "ESTA ESCENA TIENE QUE ESTABLECER" not in texto


def test_la_extension_va_dicha_en_palabras_y_no_solo_en_los_parametros():
    """`F-209`: con el rango solo dentro del JSON de parametros, el Escritor real se quedo
    corto en todas las escenas (970-1067 palabras contra 1150-1350) y `INV-17` rindio el
    capitulo. Se le dice el rango y a cuanto apuntar, que es por arriba del minimo."""
    texto = _p(parametros={"pov": "per-a", "longitud_objetivo": [1150, 1350]})
    assert "entre 1150 y 1350 palabras" in texto
    assert "unas 1300" in texto


def test_sin_rango_no_inventa_una_extension():
    assert "palabras; apunta" not in _p()


def test_pov_usado_se_pide_como_obligatorio_en_el_formato():
    """`F-210`: el Escritor real devolvio texto y delta sin `pov_usado` y el contrato lo
    rechazo. El formato decia «dos claves» y enumeraba tres."""
    texto = _p(parametros={"pov": "per-a"})
    assert "dos claves" not in texto
    assert "tres claves, las tres obligatorias" in texto


def test_la_definicion_del_escritor_no_contradice_el_formato_del_prompt():
    """`F-210`, la causa: `.claude/agents/escritor.md` pedia «dos claves y nada mas» sin
    `pov_usado`, y el system prompt ganaba al mensaje. Las dos piden las mismas tres."""
    import pathlib
    agente = (pathlib.Path(__file__).resolve().parents[5] / ".claude" / "agents"
              / "escritor.md").read_text(encoding="utf-8")
    assert "dos claves" not in agente
    assert '"pov_usado"' in agente


def test_las_palabras_clave_se_piden_en_su_forma_exacta():
    """`F-211`: el Escritor conto el rasgo con «bajaba a mirar» y `INV-23` buscaba «baja a
    mirar»: cuatro intentos, el capitulo rendido. Se le dice que la forma no se conjuga."""
    texto = _p(imprescindibles=[{"elemento": "siempre baja a mirar",
                                 "palabras_clave": ["baja a mirar"]}])
    assert "en esa forma exacta" in texto
    assert "tiempo del verbo" in texto


def test_la_extension_se_traduce_a_parrafos():
    """`F-209`, segunda vuelta: con la cifra sola el Escritor siguio entre 883 y 991."""
    texto = _p(parametros={"longitud_objetivo": [1150, 1350]})
    assert "unos 13 parrafos" in texto
