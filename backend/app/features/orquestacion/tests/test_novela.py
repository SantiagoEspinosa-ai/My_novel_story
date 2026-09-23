"""`PLAN-26` E6: montar la obra a partir del plan aprobado.

Es lo que hacia `preparar` en el guion de la obra de diez capitulos, llevado a
`app/` para poder probarlo y reutilizarlo.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela
from app.features.planificacion.service import PlanAprobado
from app.features.planificacion.tests.conftest import ficha, plan


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _aprobado():
    return PlanAprobado(plan(), 1, "El mapa de Irene", "Irene sigue un mapa antiguo.")


def test_diez_capitulos_de_una_escena_de_mil_a_mil_quinientas(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    escenas = escaleta.escenas_de(con, "obra-x")
    assert len(escenas) == 10
    assert {e["capitulo"] for e in escenas} == {"cap-{0:02d}".format(n) for n in range(1, 11)}
    assert all(list(e["longitud_objetivo"]) == [1000, 1500] for e in escenas)


def test_cada_imprescindible_es_un_hecho_canonico(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    enunciados = {h["enunciado"] for h in escaleta.hechos_declarados(con, "obra-x")}
    assert {"colecciona mapas antiguos", "el viaje en tren a Lisboa",
            "un galgo muy lento"} <= enunciados


def test_fechas_de_nacimiento_y_momento_de_la_fabula_en_la_base(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    assert con.execute("SELECT fecha_de_nacimiento FROM entidad WHERE id='per-irene'"
                       ).fetchone()[0] == "1992-03-14"
    assert escaleta.escena(con, "cap-04-e1")["t_fabula"] == "2026-06-04"


def test_la_obra_queda_con_su_titulo_y_su_genero(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    fila = con.execute("SELECT titulo, genero FROM obra WHERE id='obra-x'").fetchone()
    assert tuple(fila) == ("El mapa de Irene", "aventura")


def test_montar_dos_veces_no_duplica_ni_reinicia(con):
    """Relanzar tras una caida no puede rehacer lo que ya estaba."""
    novela.montar(con, "obra-x", ficha(), _aprobado())
    with con:
        con.execute("UPDATE escena SET estado='consolidada' WHERE id='cap-01-e1'")
    novela.montar(con, "obra-x", ficha(), _aprobado())
    assert len(escaleta.escenas_de(con, "obra-x")) == 10
    assert escaleta.escena(con, "cap-01-e1")["estado"] == "consolidada"
