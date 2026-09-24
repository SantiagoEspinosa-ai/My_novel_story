"""`SPEC-26` `RF-13`, `RF-14` y `RF-16`: validadores deterministas de la
personalizacion (`PLAN-25` E2). Funciones puras sobre texto.

Los nombres de prueba son inventados y distintos entre si, salvo donde la
prueba necesita a proposito dos nombres parecidos (Luis y Luisa).
"""

from app.commons.politica import personalizacion as p


def test_un_nombre_con_una_letra_cambiada_se_detecta():
    [m] = p.nombres_mal_escritos("Irena abrio la puerta.", ["Irene Valdés"])
    assert m.escrito == "Irena" and m.correcto == "Irene"


def test_el_nombre_bien_escrito_no_se_detecta():
    assert p.nombres_mal_escritos("Irene abrio la puerta. Valdés sonrio.",
                                  ["Irene Valdés"]) == []


def test_dos_personajes_parecidos_no_se_confunden():
    assert p.nombres_mal_escritos("Luis y Luisa comieron.", ["Luis", "Luisa"]) == []


def test_un_nombre_largo_admite_distancia_dos():
    [m] = p.nombres_mal_escritos("Llego Bartolomeus.", ["Bartolome"])
    assert m.correcto == "Bartolome"
    assert p.nombres_mal_escritos("Llego Bartola.", ["Bartolome"]) == [], \
        "a distancia 3 ya es otro nombre, no una errata"


def test_una_tilde_que_falta_es_un_nombre_mal_escrito():
    """«Exactamente» incluye los acentos: Valdes no es Valdés."""
    [m] = p.nombres_mal_escritos("La señora Valdes llego.", ["Irene Valdés"])
    assert m.correcto == "Valdés"


def test_las_palabras_en_minuscula_no_cuentan_como_nombres():
    """«irena» en minuscula no es un nombre propio: no se mira."""
    assert p.nombres_mal_escritos("una irena de papel", ["Irene"]) == []


def test_una_palabra_comun_con_mayuscula_no_es_errata_si_el_texto_la_usa_en_minuscula():
    """`F-71`: con «Nala», «Nada» a principio de frase era una errata del nombre. Si el
    propio texto escribe «nada» en minuscula, es una palabra, no un nombre."""
    assert p.nombres_mal_escritos("Nada salio bien, y no quedo nada. Llego Nala.",
                                  ["Nala"]) == []


def test_la_errata_de_verdad_se_sigue_detectando_junto_a_palabras_comunes():
    [m] = p.nombres_mal_escritos("Nada salio bien, y no quedo nada. Llego Nela.",
                                 ["Nala"])
    assert m.escrito == "Nela" and m.correcto == "Nala"


def test_una_clave_con_otro_plural_o_acento_cuenta_como_presente():
    imp = [{"elemento": "viaje", "palabras_clave": ["tren", "Lisboa"]}]
    assert p.claves_ausentes("Los trenes iban a Lisbóa.", imp) == []


def test_una_clave_ausente_se_nombra_con_su_elemento():
    imp = [{"elemento": "viaje", "palabras_clave": ["tren", "Lisboa"]}]
    assert p.claves_ausentes("El tren salio tarde.", imp) == [("viaje", "Lisboa")]


def test_el_umbral_de_repeticion_cambia_el_resultado():
    texto = " ".join(["Irene dijo algo."] * 6)
    assert p.repeticiones(texto, "Irene Valdés", umbral=5) == 6
    assert p.repeticiones(texto, "Irene Valdés", umbral=6) is None


def test_una_frase_larga_repetida_entre_capitulos_se_encuentra():
    frase = "el viento del norte traia olor a sal y a madera"
    textos = {"cap-1": "Al salir, " + frase + ".", "cap-2": "Otra vez " + frase + "."}
    [r] = p.frases_repetidas(textos, longitud=8)
    assert set(r.capitulos) == {"cap-1", "cap-2"}


def test_una_frase_corta_comun_no_cuenta_como_repeticion():
    textos = {"cap-1": "Y entonces se fue.", "cap-2": "Y entonces se fue."}
    assert p.frases_repetidas(textos, longitud=8) == []


def test_una_palabra_comun_de_la_lista_no_es_errata_aunque_solo_abra_frases():
    """`F-71` (a): «Nadie» solo a principio de frase, sin «nadie» en minuscula en el
    texto, era el caso que la regla de la minuscula no cubria (tercer borrador real)."""
    # «Nadia» y no «Nala»: «Nadie» esta a distancia 3 de «Nala» y la prueba pasaria sin
    # ejercer nada (Regla 11). A «Nadia» esta a distancia 1, como en el borrador real.
    assert p.nombres_mal_escritos("Nadie vino. Llego Nadia.", ["Nadia"]) == []
    [m] = p.nombres_mal_escritos("Nadie vino. Llego Nadja.", ["Nadia"])
    assert m.escrito == "Nadja", "una errata real junto a la palabra comun sigue saliendo"


def test_la_lista_de_palabras_comunes_es_cerrada_y_esta_escrita():
    """El punto ciego de (a) es la propia lista: se lee, no se deduce."""
    assert "Nadie" in p.PALABRAS_COMUNES and "Nada" in p.PALABRAS_COMUNES
    assert all(w[0].isupper() for w in p.PALABRAS_COMUNES)


def test_la_frase_repetida_se_cuenta_con_el_texto_y_no_con_sus_raices():
    """`F-141`, visto por `INV-30` en real: el lector leia «gat que ha comid en cuatr cas y»
    en vez de la frase del capitulo. Se compara por raices, pero se cuenta con el texto."""
    frase = "el gato que ha comido en cuatro casas y nadie lo sabe"
    textos = {"cap-1": "Al salir, " + frase + ".", "cap-2": "Dijo que " + frase + "."}
    [r] = p.frases_repetidas(textos, longitud=8)
    assert "gato que ha comido en cuatro casas" in r.frase
    assert "gat " not in r.frase
