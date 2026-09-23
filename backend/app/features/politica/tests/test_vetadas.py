"""`SPEC-25` `RF-17`: normalizar antes de comparar, y comparar palabras enteras.

Una prueba por regla. El caso de «ventana» es el que importa mas: un detector
que compara subcadenas veta media novela por un nombre de tres letras, y lo
hace sin fallar, solo devolviendo capitulos a reescribir una y otra vez.
"""

from app.features.politica.vetadas import coincidencias, formas_de_nombre


def _encontradas(texto, vetadas):
    return [c.vetada for c in coincidencias(texto, vetadas)]


def test_los_acentos_y_las_mayusculas_no_importan():
    assert _encontradas("Subió al Árbol.", ["arbol"]) == ["arbol"]


def test_el_plural_coincide_con_el_singular():
    assert _encontradas("Tenia dos perros.", ["perro"]) == ["perro"]


def test_el_plural_en_es_coincide():
    assert _encontradas("Vio los cadáveres.", ["cadaver"]) == ["cadaver"]


def test_el_genero_gramatical_coincide():
    assert _encontradas("Era su amiga.", ["amigo"]) == ["amigo"]


def test_compara_palabras_enteras_no_subcadenas():
    assert _encontradas("Abrio la ventana.", ["ana"]) == []


def test_una_expresion_de_varias_palabras_coincide_aunque_cambie_de_linea():
    assert _encontradas("Era un tema\nde familia.", ["tema de familia"]) == [
        "tema de familia"]


def test_una_expresion_no_coincide_con_sus_palabras_sueltas():
    assert _encontradas("Un tema. Mas tarde, familia.", ["tema de familia"]) == []


def test_la_coincidencia_devuelve_el_fragmento_original():
    """El audit log y el Escritor necesitan lo que se escribio, no la raiz."""
    [c] = coincidencias("Vio los Cadáveres.", ["cadaver"])
    assert c.fragmento == "Cadáveres"


def test_un_nombre_se_veta_completo_y_por_su_nombre_de_pila():
    assert formas_de_nombre("Luis Pérez") == ["Luis Pérez", "Luis"]
    formas = formas_de_nombre("Luis Pérez")
    assert _encontradas("Llamo Luis.", formas) == ["Luis"]


def test_un_nombre_de_una_sola_palabra_tiene_una_sola_forma():
    assert formas_de_nombre("Nala") == ["Nala"]


def test_sin_vetadas_no_hay_coincidencias():
    assert coincidencias("Cualquier cosa.", []) == []
