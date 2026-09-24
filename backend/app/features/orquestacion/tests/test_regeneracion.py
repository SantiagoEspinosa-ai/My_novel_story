"""`PLAN-23`: la regeneracion en una obra acumulativa, contra bases en memoria.

Ningun paso llama al modelo. Los datos son inventados.
"""

import pytest

from app.features.consolidacion import mundo
from app.features.orquestacion import regeneracion
from app.features.orquestacion.tests import obra_regenerable as o
from app.features.planificacion import repository as planes
from app.features.planificacion.tests.conftest import plan


@pytest.fixture
def con():
    c = o.conexion()
    planes.asegurar_tablas(c)
    return c


# --- A2 · la semilla ------------------------------------------------------------

def test_sin_plan_aprobado_no_hay_semilla_y_se_dice(con):
    o.obra(con)
    planes.guardar(con, "obra-a", 1, plan(), False, "revisor", ["no"])
    with pytest.raises(regeneracion.SinSemilla, match="plan aprobado"):
        regeneracion.semilla_de(con, "obra-a")


def test_la_semilla_sale_del_plan_y_del_conocimiento_anterior_al_relato(con):
    o.obra(con)
    planes.guardar(con, "obra-a", 1, plan(), True, "revisor", [])
    mundo.sembrar_conocimiento(con, [{"sujeto": "per-irene", "hecho": "imp-01"}])
    o.escribir(con, "obra-a-c1-e1", "texto", {
        "movimientos": [], "revelaciones": [{"sujeto": "per-brisa", "hecho": "h-x"}]})
    s = regeneracion.semilla_de(con, "obra-a")
    assert s["entidades_vivas"] == {"per-irene": "vivo", "per-brisa": "vivo"}
    assert s["ubicaciones"] == {"per-irene": "lug-casa", "per-brisa": "lug-casa"}
    assert s["accesos"] == {"lug-casa": []}
    # Lo revelado por una escena no es semilla: es de su delta.
    assert s["conocimiento"] == {("per-irene", "imp-01"): {"desde": None, "grado": "sabe"}}
