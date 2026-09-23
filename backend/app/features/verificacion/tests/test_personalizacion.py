"""`SPEC-26` `RF-13`, `RF-14` y `RF-16`: validadores deterministas de la
personalizacion (`PLAN-25` E2). Funciones puras sobre texto.

Los nombres de prueba son inventados y distintos entre si, salvo donde la
prueba necesita a proposito dos nombres parecidos (Luis y Luisa).
"""

from app.features.verificacion import personalizacion as p


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
