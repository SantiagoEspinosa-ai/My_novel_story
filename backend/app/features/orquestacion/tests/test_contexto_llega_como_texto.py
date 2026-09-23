"""`F-58`: el Escritor recibia los **tamaños** de los bloques de contexto, no su
texto, en todas las escenas. Que la escena anterior este vacia en la primera es
correcto; que el bloque inmutable sea un numero no lo es nunca.

Estas pruebas miran el **contenido** del prompt, que es lo que ninguna miraba:
todas comprobaban que el recorte cuadrara y ninguna que el texto llegara.
"""

import re
import sqlite3

import pytest

from app.commons.modelo.doble import DobleDelModelo
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import obra

PREMISA = "Un faro abandonado guarda las cartas que nadie envio."


class Devuelve:
    nombre = "doble"

    def __init__(self, r):
        self.r = r

    def llamar(self, prompt):
        return dict(self.r)


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": []})
    repo.guardar_escaleta(c, "obra-f", [
        {"id": "e{0}".format(i), "orden": i, "capitulo": "cap-1",
         "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
         "pov": "per-marta", "lugar": "lug-salon",
         "beats": [{"id": "b{0}".format(i), "texto": "Marta encuentra la carta {0}.".format(i),
                    "establece": []}],
         "longitud_objetivo": [10, 5000]} for i in (1, 2, 3)])
    return c


def _generar(con, **kw):
    escritor = DobleDelModelo()
    obra.generar_obra(con, "obra-f", escritor,
                      Devuelve({"veredicto": "PASA", "problemas": []}),
                      Devuelve({"texto": "Resumen: Marta abre el faro.",
                                "hechos_clave": []}),
                      inmutable=PREMISA, techo=kw.pop("techo", 1_000_000), **kw)
    return escritor.llamadas


def test_la_premisa_llega_como_texto_en_todas_las_escenas(con):
    for prompt in _generar(con):
        assert PREMISA in prompt


def test_ningun_bloque_llega_como_un_numero(con):
    for prompt in _generar(con):
        assert not re.search(r'\["inmutable", \d+\]', prompt)
        assert not re.search(r'\["escena_anterior", \d+\]', prompt)


def test_la_escena_anterior_y_los_resumenes_llegan_desde_la_segunda(con):
    llamadas = _generar(con)
    assert "Resumen: Marta abre el faro." not in llamadas[0], "en la primera no hay"
    assert "Resumen: Marta abre el faro." in llamadas[2]
    assert "palabra palabra" in llamadas[1], "el texto de la escena anterior"


def test_la_sinopsis_del_beat_llega_como_lo_que_la_escena_tiene_que_hacer(con):
    llamadas = _generar(con)
    assert "Marta encuentra la carta 1." in llamadas[0]
    assert "Marta encuentra la carta 3." in llamadas[2]


def test_un_bloque_eliminado_por_el_recorte_no_llega(con, monkeypatch):
    """El recorte se aplica al **texto**, no solo se planifica: `aplicar_recorte`
    existia y nadie la llamaba fuera de sus pruebas."""
    from app.features.contexto import recorte
    from app.features.contexto.bloques import Clase

    monkeypatch.setattr(recorte, "planificar", lambda tamanos, techo: [
        recorte.Paso("condensaciones", Clase.ELIMINACION)])
    llamadas = _generar(con)
    assert "Resumen: Marta abre el faro." not in llamadas[2]
    assert PREMISA in llamadas[2], "lo que no se recorta sigue llegando"
