"""`PLAN-30` E8: evaluar la puerta de publicacion una vez, con Lean automatico.

La novela se escribe con dobles (`_escrita`, de `test_novela.py`) y Lean es un doble
que cuenta cuantas veces se le llama: estas pruebas miran lo que compone la puerta,
no lo que dice Lean de verdad (eso es `auditoria/tests/test_lean_real.py`).
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.features.auditoria import repository as veredictos
from app.features.auditoria.publicacion import ResultadoLean
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import publicacion
from app.features.orquestacion.tests.test_novela import BIEN, JuezDeObra, _escrita
from app.features.planificacion.tests.conftest import ficha

ABRUPTO = {"arco_cerrado": True, "final_abrupto": True, "justificacion": "acaba de golpe"}


class LeanFijo:
    def __init__(self, codigo=0, violaciones=()):
        self.resultado = ResultadoLean(codigo, list(violaciones))
        self.llamadas = 0

    def verificar(self, con, obra):
        self.llamadas += 1
        return self.resultado


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _evaluar(con, lean, juez):
    return publicacion.evaluar(con, "obra-x", ficha(), lean, juez)


def _abiertos(con, invariante):
    return [h for e in escaleta.escenas_de(con, "obra-x")
            for h in escaleta.hallazgos_abiertos(con, e["id"])
            if h["invariante"] == invariante]


def test_lean_se_ejecuta_sin_que_nadie_lo_pida(con):
    """`RF-02`: una llamada a Lean por ronda, sin que el llamante lo pida."""
    _escrita(con)
    lean = LeanFijo()
    _evaluar(con, lean, JuezDeObra(BIEN))
    assert lean.llamadas == 1


def test_todo_limpio_guarda_el_veredicto_publicado(con):
    _escrita(con)
    e = _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert e.decision.publica and e.ronda == 1
    v = veredictos.ultimo(con, "obra-x")
    assert v["publica"] and v["ronda"] == 1 and v["codigo_lean"] == 0
    assert [n["invariante"] for n in v["no_ejecutadas"]] == ["INV-06"]


def test_con_inv24_fallando_lean_se_ejecuta_igual(con):
    """`RF-04` informa de todas las condiciones, asi que Lean corre aunque ya se
    sepa que la version no se publica."""
    _escrita(con, usados=("imp-01", "imp-02"))
    lean = LeanFijo()
    e = _evaluar(con, lean, JuezDeObra(BIEN))
    assert lean.llamadas == 1
    assert "INV-24" in [c.invariante for c in e.decision.condiciones]


def test_un_capitulo_rendido_no_publica(con):
    _escrita(con)
    with con:
        con.execute("UPDATE escena SET estado='aceptada_por_rendicion' "
                    "WHERE id='obra-x-cap-03-e1' OR id='cap-03-e1'")
    e = _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert [(c.invariante, c.capitulo) for c in e.decision.condiciones] == [("INV-29", "cap-03")]


def test_un_fallo_de_lean_deja_hallazgo_inv28_con_sus_eventos(con):
    _escrita(con)
    e = _evaluar(con, LeanFijo(1, [{"invariante": "L-1", "eventos": ["ev-1", "ev-2"],
                                    "detalle": "ev-2 va antes"}]), JuezDeObra(BIEN))
    assert not e.decision.publica
    assert "L-1" in _abiertos(con, "INV-28")[0]["descripcion"]


def test_un_inv27_que_la_ronda_nueva_no_ve_se_cierra_con_motivo(con):
    _escrita(con)
    _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    [viejo] = _abiertos(con, "INV-27")
    e = _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert e.decision.publica and e.ronda == 2
    assert _abiertos(con, "INV-27") == []
    fila = con.execute("SELECT estado, motivo_de_cierre FROM hallazgo WHERE id = ?",
                       (viejo["id"],)).fetchone()
    assert fila[0] == EH.RESUELTO.value and "ronda 2" in fila[1]


def test_un_inv27_que_sigue_no_se_cierra_ni_se_duplica(con):
    """Si sigue, queda el mismo hallazgo: ni se marca resuelto lo que no se arreglo,
    ni se abre otro igual encima (el recuento por invariante es lo que dice si una
    regla sirve)."""
    _escrita(con)
    _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    [viejo] = _abiertos(con, "INV-27")
    e = _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    assert not e.decision.publica
    assert [h["id"] for h in _abiertos(con, "INV-27")] == [viejo["id"]]
