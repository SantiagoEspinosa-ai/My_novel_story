"""`PLAN-31` E5: el `Contador`, que sale de `novela_regalo.py` y gana prueba.

Suma lo que costo un agente que no pasa por las trazas del ciclo: el Planificador, el
Revisor, el juicio de obra, el Entrevistador. **Lo que no trae coste no suma cero**: se
cuenta aparte, porque un cero se lee como un dato y un hueco no.
"""

import pytest

from app.commons.modelo import proveedor
from app.commons.modelo.contador import Contador


class _Sesion:
    nombre = "doble"

    def __init__(self, respuestas):
        self.respuestas, self.entorno, self.herramientas = list(respuestas), {}, None

    def llamar(self, prompt):
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_una_delegacion_sin_coste_cuenta_como_sin_medir_no_como_cero():
    c = Contador(_Sesion([{"x": 1}, {"x": 2, "medidas": {"coste_usd": 0.25}}]))
    c.llamar("a")
    assert c.delegaciones == 1 and c.sin_coste == 1
    assert c.medido is None, "sin ninguna delegacion con coste, el total no es 0: no se sabe"
    c.llamar("b")
    assert c.delegaciones == 2 and c.sin_coste == 1 and c.usd == 0.25
    assert c.medido == 0.25


def test_una_respuesta_ilegible_se_paga_igual_y_se_cuenta():
    """`PLAN-29` E1: lo ilegible conserva su coste."""
    c = Contador(_Sesion([proveedor.RespuestaIlegible("no es json",
                                                       medidas={"coste_usd": 0.5})]))
    with pytest.raises(proveedor.RespuestaIlegible):
        c.llamar("a")
    assert c.delegaciones == 1 and c.usd == 0.5 and c.sin_coste == 0


def test_un_fallo_de_transporte_cuenta_como_delegacion_sin_coste():
    c = Contador(_Sesion([proveedor.FalloDeTransporte("TimeoutExpired")]))
    with pytest.raises(proveedor.FalloDeTransporte):
        c.llamar("a")
    assert c.delegaciones == 1 and c.sin_coste == 1


def test_lo_que_se_configura_sobre_el_contador_es_de_la_sesion():
    """Las tools y el entorno los lee la sesion de dentro, no el envoltorio."""
    s = _Sesion([])
    c = Contador(s)
    c.herramientas = {"db": "x.db", "obra": "o"}
    assert s.herramientas == {"db": "x.db", "obra": "o"}
    assert c.entorno is s.entorno and c.nombre == "doble" and c.sesion is s
