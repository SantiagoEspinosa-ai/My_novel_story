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
    return {"titulo": "El mapa de Irene", "premisa": "Irene sigue un mapa antiguo.",
            "plan": dict(plan_dict(), **cambios)}


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


def test_un_plan_que_no_cumple_el_esquema_se_repite_y_se_dice(con):
    malo = {"titulo": "t", "premisa": "p", "plan": {"capitulos": []}}
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


def test_la_premisa_y_el_titulo_vienen_de_la_ficha(con):
    """`SPEC-25` v3: los propone el entrevistador. El planificador los recibe en
    el prompt y no puede cambiarlos aunque devuelva otros."""
    planificador = Agente([dict(_plan(), titulo="Otro titulo", premisa="Otra premisa")])
    r = service.planificar(con, "obra-x", ficha(), planificador, Agente([APROBADO]))
    assert r.titulo == "El mapa de Irene"
    assert r.premisa == "Un mapa heredado lleva a Irene de vuelta a Lisboa."
    assert "Un mapa heredado lleva a Irene de vuelta a Lisboa." in planificador.llamadas[0]


def test_un_plan_sin_titulo_propio_ya_no_gasta_una_ronda(con):
    r = service.planificar(con, "obra-x", ficha(), Agente([{"plan": plan_dict()}]),
                           Agente([APROBADO]))
    assert r.version == 1


def test_el_prompt_dice_que_no_hay_campos_extra_y_que_los_accesos_son_ids(con):
    """`F-62`, Regla 4: en la ejecucion real el Planificador invento un campo y
    escribio los accesos como texto. El esquema los rechaza; el prompt tiene que
    haberlo pedido antes."""
    planificador = Agente([_plan()])
    service.planificar(con, "obra-x", ficha(), planificador, Agente([APROBADO]))
    prompt = planificador.llamadas[0]
    assert "campo" in prompt and "rechaza" in prompt
    assert "accesos" in prompt and "identificadores" in prompt


def test_el_prompt_del_planificador_lleva_la_longitud_elegida(con):
    """`SPEC-32` `RF-09`: el Planificador escribe para la extension de la ficha."""
    planificador = Agente([_plan()])
    service.planificar(con, "obra-x", ficha(extension="larga"), planificador,
                       Agente([{"aprobado": True, "objeciones": []}]))
    assert "1350" in planificador.llamadas[0] and "1500" in planificador.llamadas[0]
    assert "1000" not in planificador.llamadas[0]


# --- Reanudar sin volver a planificar -------------------------------------------

def test_con_un_plan_aprobado_se_reutiliza_sin_llamar_a_nadie(con):
    """Relanzar tras una caida volvia a pagar al Planificador y al Revisor, y el
    plan nuevo podia no cuadrar con la obra ya montada: el checkpoint que pide el
    enunciado tiene que reanudar, no rehacer."""
    primero = service.reanudar_o_planificar(con, "obra-x", ficha(), Agente([_plan()]),
                                            Agente([APROBADO]))
    planificador, revisor = Agente([_plan()]), Agente([APROBADO])
    segundo = service.reanudar_o_planificar(con, "obra-x", ficha(), planificador, revisor)
    assert planificador.llamadas == [] and revisor.llamadas == []
    assert segundo.reutilizado and not primero.reutilizado
    assert segundo.version == primero.version
    assert segundo.plan == primero.plan
    assert segundo.titulo == "El mapa de Irene"


def test_sin_plan_aprobado_se_planifica(con):
    r = service.reanudar_o_planificar(con, "obra-x", ficha(), Agente([_plan()]),
                                      Agente([APROBADO]))
    assert r.version == 1 and not r.reutilizado


def test_un_plan_fuera_de_esquema_no_gasta_ronda_de_revision(con):
    """`F-68`: en la segunda ejecucion real dos de las tres rondas se fueron en errores
    de formato y el Revisor solo vio un plan. Con una sola ronda, dos planes fuera de
    esquema no la gastan: el Revisor ve el tercero."""
    malo = {"titulo": "t", "premisa": "p", "plan": {"capitulos": []}}
    revisor = Agente([APROBADO])
    r = service.planificar(con, "obra-x", ficha(), Agente([malo, malo, _plan()]), revisor,
                           tope=1)
    assert r.version == 3 and len(revisor.llamadas) == 1
    assert [v["origen"] for v in repo.versiones(con, "obra-x")] == ["esquema", "esquema",
                                                                     "revisor"]


def test_los_planes_fuera_de_esquema_tienen_su_propio_tope(con):
    """Y ese reintento tiene limite: sin el, un Planificador que nunca cumple el esquema
    no terminaria. Tras `tope_de_formato` reintentos, la generacion no empieza."""
    malo = {"titulo": "t", "premisa": "p", "plan": {"capitulos": []}}
    planificador, revisor = Agente([malo]), Agente([APROBADO])
    with pytest.raises(service.PlanNoAprobado) as e:
        service.planificar(con, "obra-x", ficha(), planificador, revisor,
                           tope=3, tope_de_formato=2)
    assert len(planificador.llamadas) == 3 and revisor.llamadas == []
    assert "esquema" in str(e.value)


# --- `PLAN-27` E3: quien esta en cada escena -----------------------------------------

def test_una_escena_del_plan_con_un_presente_no_declarado_no_valida():
    from pydantic import ValidationError
    from app.commons.configuracion.esquemas import PlanDeLaObra
    d = plan_dict()
    d["capitulos"][0]["escenas"][0]["personajes_presentes"] = ["per-irene", "per-nadie"]
    with pytest.raises(ValidationError) as e:
        PlanDeLaObra.model_validate(d)
    # Por el presente y no por un campo de mas: antes de existir el campo, el plan ya no
    # validaba, y la prueba habria pasado por el motivo equivocado.
    assert "per-nadie" in str(e.value) and "no es un personaje declarado" in str(e.value)


def test_los_presentes_se_acotan_a_la_obra_como_el_pov():
    """`F-64`: los identificadores del plan son de su obra, tambien los presentes."""
    from app.commons.configuracion.esquemas import PlanDeLaObra
    from app.features.planificacion.ids import acotar_a_la_obra
    d = plan_dict()
    d["capitulos"][0]["escenas"][0]["personajes_presentes"] = ["per-irene", "per-brisa"]
    p = acotar_a_la_obra(PlanDeLaObra.model_validate(d), "obra-x")
    assert p.capitulos[0].escenas[0].personajes_presentes == ["obra-x-per-irene",
                                                              "obra-x-per-brisa"]


def test_el_prompt_del_planificador_pide_los_personajes_presentes(con):
    planificador = Agente([_plan()])
    service.planificar(con, "obra-x", ficha(), planificador, Agente([APROBADO]))
    assert "personajes_presentes" in planificador.llamadas[0]


def test_relanzar_la_planificacion_no_pisa_las_versiones_anteriores(con):
    """`F-111`, TLC `CE-8` (`RondasDePlanConservadas`): `planificar` volvia a numerar desde
    la version 1 y, con `INSERT OR REPLACE`, pisaba las rondas de la ejecucion anterior."""
    with pytest.raises(service.PlanNoAprobado):
        service.planificar(con, "obra-x", ficha(), Agente([_plan()]),
                           Agente([_rechazo("no tiene arco")]))
    r = service.planificar(con, "obra-x", ficha(), Agente([_plan()]), Agente([APROBADO]))
    versiones = repo.versiones(con, "obra-x")
    assert [v["version"] for v in versiones] == [1, 2, 3, 4]
    assert [v["aprobado"] for v in versiones] == [False, False, False, True]
    assert r.version == 4
