"""`SPEC-26` `RF-02`..`RF-07`: planificar con revision (`PLAN-26` E5)."""

import json
import sqlite3

import pytest

from app.features.planificacion import repository as repo
from app.features.planificacion import service
from app.features.planificacion.tests.conftest import ficha, plan_dict


class Agente:
    def __init__(self, respuestas, nombre="doble"):
        self.respuestas, self.llamadas, self.nombre = list(respuestas), [], nombre

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return self.respuestas[min(len(self.llamadas) - 1, len(self.respuestas) - 1)]


def _plan(**cambios):
    return {"plan": dict(plan_dict(), **cambios)}


APROBADO = {"aprobado": True, "objeciones": []}


def _rechazo(texto):
    return {"aprobado": False, "objeciones": [texto]}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    return c


def test_aprobado_a_la_primera(con):
    r = service.planificar(con, "obra-x", ficha(), Agente([_plan()]), Agente([APROBADO]))
    assert r.version == 1 and len(r.plan.capitulos) == 10


def test_las_objeciones_de_una_ronda_entran_en_la_siguiente(con):
    planificador = Agente([_plan()])
    revisor = Agente([_rechazo("el tono no es divertido"),
                      _rechazo("falta el cumpleaños"), APROBADO])
    r = service.planificar(con, "obra-x", ficha(), planificador, revisor)
    assert r.version == 3
    assert "falta el cumpleaños" in planificador.llamadas[2]
    assert "el tono no es divertido" not in planificador.llamadas[2], \
        "solo las objeciones de la ronda anterior"


def test_tres_rechazos_y_la_generacion_no_empieza(con):
    with pytest.raises(service.PlanNoAprobado) as e:
        service.planificar(con, "obra-x", ficha(), Agente([_plan()]),
                           Agente([_rechazo("no tiene arco")]))
    assert "no tiene arco" in str(e.value)
    assert [v["aprobado"] for v in repo.versiones(con, "obra-x")] == [False] * 3


def test_un_plan_con_huecos_no_llega_al_revisor(con):
    revisor = Agente([APROBADO])
    corto = _plan(capitulos=plan_dict()["capitulos"][:9])
    r = service.planificar(con, "obra-x", ficha(), Agente([corto, _plan()]), revisor)
    assert r.version == 2 and len(revisor.llamadas) == 1
    [v1, v2] = repo.versiones(con, "obra-x")
    assert v1["origen"] == "codigo" and "10 capitulos" in v1["objeciones"][0]


def test_un_plan_que_no_cumple_el_esquema_gasta_una_ronda_y_se_dice(con):
    malo = {"plan": {"capitulos": []}}
    r = service.planificar(con, "obra-x", ficha(), Agente([malo, _plan()]),
                           Agente([APROBADO]))
    assert r.version == 2
    assert repo.versiones(con, "obra-x")[0]["origen"] == "esquema"


def test_un_revisor_ilegible_no_aprueba(con):
    with pytest.raises(service.PlanNoAprobado):
        service.planificar(con, "obra-x", ficha(), Agente([_plan()]),
                           Agente([{"sin": "veredicto"}]))


def test_el_revisor_recibe_la_ficha_y_el_plan(con):
    revisor = Agente([APROBADO])
    service.planificar(con, "obra-x", ficha(), Agente([_plan()]), revisor)
    assert "Irene Valdés" in revisor.llamadas[0]
    assert "cap-10" in revisor.llamadas[0]


def test_el_plan_aprobado_se_guarda_y_se_puede_leer(con):
    service.planificar(con, "obra-x", ficha(), Agente([_plan()]), Agente([APROBADO]))
    assert len(repo.aprobado(con, "obra-x").capitulos) == 10
