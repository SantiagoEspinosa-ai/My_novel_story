"""C4 — Las puertas, con el caso negativo de cada invariante que ejecutan.

"Una invariante que nunca ha fallado en las pruebas no esta verificada, solo
declarada." Esta feature ejecuta seis, y aqui esta el fragmento que viola cada
una a proposito.
"""

import pytest

from app.commons.dominio.enumeraciones import EstadoDeHallazgo, Severidad
from app.features.verificacion import puertas


def _mundo():
    return {
        "entidades_vivas": {"marta": "vivo", "ana": "muerto"},
        "ubicaciones": {"marta": "salon", "ana": "sotano"},
        "accesos": {"salon": ["cocina"], "sotano": []},
        "conocimiento": {("marta", "hec-1"): {"desde": 1, "grado": "sabe"}},
    }


def test_inv01_una_escena_sin_cambio_de_valor():
    h = puertas.verificar({"id": "e1", "cambio_de_valor": None}, {}, _mundo())
    assert any(x.invariante == "INV-01" and x.severidad is Severidad.BLOQUEANTE for x in h)


def test_inv02_un_personaje_muerto_presente():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "personajes_presentes": ["ana"], "lugar": "salon"}
    h = puertas.verificar(esc, {}, _mundo())
    assert any(x.invariante == "INV-02" for x in h)


def test_inv02_un_personaje_en_un_lugar_inaccesible():
    """La mitad que obligo a partir `Lugar`: la accesibilidad."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "sotano"}
    h = puertas.verificar(esc, {}, _mundo())
    assert any(x.invariante == "INV-02" for x in h)


def test_inv03_actuar_sobre_un_hecho_que_no_se_conoce():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "conocimiento", "signo": "positivo"},
           "personajes_presentes": ["marta"], "lugar": "salon", "t_fabula": 5}
    delta = {"revelaciones": [{"sujeto": "ana", "hecho": "hec-9"}]}
    h = puertas.verificar(esc, delta, _mundo())
    assert any(x.invariante == "INV-03" and x.severidad is Severidad.BLOQUEANTE for x in h)


def test_inv04_el_pov_cambia_dentro_de_la_escena():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "control", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "salon",
           "pov": "marta", "pov_usado": "ana"}
    h = puertas.verificar(esc, {}, _mundo())
    assert any(x.invariante == "INV-04" for x in h)


def test_inv17_una_escena_de_944_palabras_con_minimo_de_1200():
    """El caso de `main`, ahora cazado por una regla y no por un juez."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "salon",
           "longitud_objetivo": (1200, 2200), "palabras": 944}
    h = puertas.verificar(esc, {}, _mundo())
    inv17 = [x for x in h if x.invariante == "INV-17"]
    assert inv17 and inv17[0].severidad is Severidad.MAYOR


def test_un_verificador_mudo_produce_sin_veredicto_y_no_un_pase():
    """`SPEC-10` C-2: quien no se dejo auditar no gana por defecto."""
    h = puertas.veredicto_ilegible("INV-10", "e1", salida="{{roto")
    assert h.estado is EstadoDeHallazgo.SIN_VEREDICTO
    assert h.descripcion, "se rellena con que se intento comprobar y donde"


def test_una_escena_limpia_no_produce_hallazgos():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "salon",
           "pov": "marta", "pov_usado": "marta",
           "longitud_objetivo": (500, 2200), "palabras": 900}
    assert puertas.verificar(esc, {}, _mundo()) == []
