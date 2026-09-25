"""`PLAN-41` R1 (`SPEC-41` `RF-01`, `RF-02`): retirar una novela de la estanteria con su motivo.
`PLAN-42` P1 (`SPEC-42`): la administracion ensena la estanteria, las mismas y en el mismo
orden; la retirada sigue guardada en la base. Datos inventados."""

from app.features.regalo import repository as repo
from app.features.regalo.tests.conftest import OBRA, OTRA


def _ids(cliente):
    return [o["id"] for o in cliente.get("/obras").json()["obras"]]


def _ids_admin(cliente):
    return [o["id"] for o in cliente.get("/admin/obras").json()["obras"]]


def test_una_obra_retirada_no_sale_ni_en_la_estanteria_ni_en_admin(cliente, con):
    r = cliente.post("/admin/obras/{0}/retirada".format(OBRA),
                     json={"motivo": "datos de la semilla, sin texto: no se puede terminar"})
    assert r.status_code == 200, r.text
    assert OBRA not in _ids(cliente) and OTRA in _ids(cliente)
    assert OBRA not in _ids_admin(cliente)
    # `SPEC-42` `RF-02`: no se borra nada; el motivo sigue en la base.
    retirada = repo.retiradas(con)[OBRA]
    assert retirada["motivo"].startswith("datos de la semilla") and retirada["quien"] == "sistema"


def test_la_administracion_ensena_la_estanteria_en_su_orden_y_sin_retiradas(cliente):
    cliente.post("/admin/obras/{0}/retirada".format(OBRA), json={"motivo": "prueba"})
    assert _ids_admin(cliente) == _ids(cliente)
    assert all("retirada" not in o for o in cliente.get("/admin/obras").json()["obras"])


def test_devolver_una_retirada_la_devuelve_a_la_administracion(cliente):
    cliente.post("/admin/obras/{0}/retirada".format(OBRA), json={"motivo": "prueba"})
    cliente.delete("/admin/obras/{0}/retirada".format(OBRA))
    assert OBRA in _ids_admin(cliente) and _ids_admin(cliente) == _ids(cliente)


def test_retirar_exige_motivo(cliente):
    assert cliente.post("/admin/obras/{0}/retirada".format(OBRA), json={"motivo": ""}).status_code == 422
    assert cliente.post("/admin/obras/no-existe/retirada", json={"motivo": "x"}).status_code == 404


def test_retirar_se_deshace(cliente):
    cliente.post("/admin/obras/{0}/retirada".format(OBRA), json={"motivo": "prueba"})
    assert cliente.delete("/admin/obras/{0}/retirada".format(OBRA)).status_code == 200
    assert OBRA in _ids(cliente)
