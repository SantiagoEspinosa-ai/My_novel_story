"""`PLAN-41` R1 (`SPEC-41` `RF-01`, `RF-02`): retirar una novela de la estanteria con su motivo,
sin perderla de la administracion. Datos inventados."""

from app.features.regalo.tests.conftest import OBRA, OTRA


def _ids(cliente):
    return [o["id"] for o in cliente.get("/obras").json()["obras"]]


def test_una_obra_retirada_no_sale_en_la_estanteria_y_si_en_admin(cliente):
    r = cliente.post("/admin/obras/{0}/retirada".format(OBRA),
                     json={"motivo": "datos de la semilla, sin texto: no se puede terminar"})
    assert r.status_code == 200, r.text
    assert OBRA not in _ids(cliente) and OTRA in _ids(cliente)
    obras = {o["id"]: o for o in cliente.get("/admin/obras").json()["obras"]}
    assert obras[OBRA]["retirada"]["motivo"].startswith("datos de la semilla")
    assert obras[OBRA]["retirada"]["quien"] == "sistema"
    assert obras[OTRA]["retirada"] is None


def test_retirar_exige_motivo(cliente):
    assert cliente.post("/admin/obras/{0}/retirada".format(OBRA), json={"motivo": ""}).status_code == 422
    assert cliente.post("/admin/obras/no-existe/retirada", json={"motivo": "x"}).status_code == 404


def test_retirar_se_deshace(cliente):
    cliente.post("/admin/obras/{0}/retirada".format(OBRA), json={"motivo": "prueba"})
    assert cliente.delete("/admin/obras/{0}/retirada".format(OBRA)).status_code == 200
    assert OBRA in _ids(cliente)
