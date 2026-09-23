"""`SPEC-25` `RF-17`: normalizar antes de comparar, y comparar palabras enteras.

Una prueba por regla. El caso de «ventana» es el que importa mas: un detector
que compara subcadenas veta media novela por un nombre de tres letras, y lo
hace sin fallar, solo devolviendo capitulos a reescribir una y otra vez.
"""

from app.commons.politica.vetadas import coincidencias, formas_de_nombre


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


# --- `F-59`: «coño» se normalizaba en «con» -------------------------------------

from app.commons.configuracion import carga

# Las palabras mas frecuentes del español escrito, en sus formas mas comunes.
# Una vetada que coincida con alguna de estas deja la novela sin poder escribirse.
COMUNES = """de la que el en y a los se del las un por con no una su para es al lo
como mas o pero sus le ha me si sin sobre este ya entre cuando todo esta ser son
dos tambien fue habia era muy anos hasta desde esta mi porque que solo han yo
hay vez puede todos asi nos ni parte tiene el uno donde bien tiempo mismo ese
ahora cada e vida otro despues te otros aunque esa eso hace otra gobierno tan
durante siempre dia tanto ella tres si dijo sido gran pais segun menos mundo
casa cosa caso mano noche agua ojos luz tarde parque amigo amiga novio novia
padre madre hijo hija perro perra nino nina cama mesa puerta calle ciudad
camino cielo mar sol voz vino con cono canto conto contra""".split()


def test_la_ene_no_se_pierde():
    """`F-59`: sin la ñ, «coño» quedaba en «con» y vetaba la preposicion."""
    assert _encontradas("Vino con ella.", ["coño"]) == []
    assert _encontradas("¡Coño!", ["coño"]) == ["coño"]
    assert _encontradas("Soltó dos coños.", ["coño"]) == ["coño"]


def test_ninguna_vetada_de_la_lista_real_veta_una_palabra_comun():
    """El barrido que habria cazado `F-59` antes de gastar una ejecucion real:
    cada palabra de `config/vetadas.json` contra las palabras mas comunes."""
    listas = carga.cargar_vetadas()
    vetadas = list(listas.global_) + [v for vs in listas.franjas.values() for v in vs]
    texto = " ".join(COMUNES)
    choques = [(c.vetada, c.fragmento) for c in coincidencias(texto, vetadas)]
    assert choques == []
