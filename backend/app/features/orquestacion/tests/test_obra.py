"""F6 — El bucle de escenas, contra dobles.

Lo que se comprueba aqui es el **encadenado**: que el material de la escena N
incluya lo que dejo la N-1, que el contexto crezca, y que una `bloqueante`
detenga la obra en vez de saltarsela.
"""

import sqlite3

import pytest

from app.commons.modelo.doble import DobleDelModelo
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import obra


class Devuelve:
    def __init__(self, respuesta, nombre="doble"):
        self.nombre, self._r = nombre, respuesta

    def llamar(self, prompt):
        return dict(self._r, medidas={"modelos": ["doble-1"], "tokens_entrada": 5,
                                      "tokens_salida": 5})


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": ["lug-sotano"], "lug-sotano": ["lug-salon"]})
    repo.guardar_escaleta(c, "cap-1", [
        {"id": "e{0}".format(i), "orden": i,
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
         "beats": ["b"], "longitud_objetivo": [10, 5000]} for i in (1, 2, 3)])
    return c


def _agentes():
    return (DobleDelModelo(),
            Devuelve({"veredicto": "PASA", "problemas": []}),
            Devuelve({"texto": "Resumen de la escena. " * 10,
                      "hechos_clave": ["hec-llave"]}))


def test_genera_las_tres_escenas_en_orden(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1", "e2", "e3"]
    assert g.llego_al_final


def test_el_material_de_la_escena_2_incluye_lo_que_dejo_la_1(con):
    """El encadenado: sin esto la 2 genera contra el mundo de la 1."""
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    material = obra.reunir_material(con, repo.escena(con, "e2"))
    assert material["resumenes"], "el resumen de la 1 esta disponible en la 2"
    assert material["escena_anterior"], "y el texto de la 1 tambien"


def test_el_contexto_crece_escena_a_escena(con):
    """El criterio de terminacion de la Fase F, y el unico que importa."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    totales = [m["total"] for m in g.medidas]
    assert totales == sorted(totales), "no decrece: {0}".format(totales)
    assert totales[-1] > totales[0], "tiene que crecer solo: {0}".format(totales)


def test_una_bloqueante_detiene_la_obra_y_deja_el_dato(con):
    """No se rinde y no se salta. Y la parada **es la medida** (`VER-64`)."""
    with con:
        con.execute("UPDATE escena SET cambio_de_valor='null' WHERE id='e2'")
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1"]
    assert g.parada["escena"] == "e2"
    assert any(inv == "INV-01" for inv, _ in g.parada["hallazgos"])
    assert "INV-01" in obra.informe(g)


def test_rf26_detiene_la_obra_sin_llamar_al_modelo(con):
    """Con un techo imposible no se genera: se falla antes."""
    escritor = DobleDelModelo()
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1)
    assert g.parada["motivo"] == "no_cabe"
    assert escritor.llamadas == []


def test_el_informe_dice_si_el_contexto_crece(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert "CRECE" in obra.informe(g)
