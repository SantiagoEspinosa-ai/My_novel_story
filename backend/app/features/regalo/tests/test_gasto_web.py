"""`SPEC-33` `RF-12`, `RF-19` y cuestion 1, `PLAN-33` E10: lo que la confirmacion ensena.

Tres cifras, cada una con su procedencia: lo gastado en la base frente al techo, la ultima
generacion medida y la referencia de la novela de ejemplo. Lo gastado es siempre un
**suelo**: lo anterior a la migracion 17 no tiene coste guardado, y sumar como si lo
tuviera seria el sesgo hacia lo barato (decision del autor).
"""

from app.commons.modelo import gasto
from app.features.regalo import router
from app.features.regalo.tests.conftest import OBRA, OTRA


def _leer(cliente):
    r = cliente.get("/generaciones/gasto")
    assert r.status_code == 200, r.text
    return r.json()


def test_lo_gastado_es_suelo_y_lo_dice(cliente, con):
    gasto.anotador(con, OBRA, "gen-1")("escritor", 2.0)
    gasto.anotador(con, OTRA)("entrevistador", 0.5)
    g = _leer(cliente)["gastado"]
    assert (g["usd"], g["delegaciones"], g["es_suelo"]) == (2.5, 2, True)
    assert "migracion 17" in g["por_que_es_suelo"]


def test_sin_generaciones_la_ultima_viene_ausente_y_no_a_cero(cliente):
    c = _leer(cliente)
    assert c["ultima"] is None
    assert c["gastado"]["usd"] is None and c["gastado"]["delegaciones"] == 0


def test_la_ultima_es_la_ultima_generacion_de_la_base(cliente, con):
    gasto.anotador(con, OBRA, "gen-1")("escritor", 9.0)
    a = gasto.anotador(con, OTRA, "gen-2")
    a("escritor", 1.0)
    a("editor", None)
    u = _leer(cliente)["ultima"]
    assert (u["generacion"], u["usd"], u["es_suelo"]) == ("gen-2", 1.0, True)


def test_la_referencia_viaja_con_su_fuente(cliente):
    r = _leer(cliente)["referencia"]
    assert (r["usd"], r["delegaciones"]) == (16.8905, 36)
    assert "harness/evals/medidas.md" in r["fuente"] and "R1" in r["fuente"]


def test_el_techo_viene_de_la_configuracion(cliente, con, monkeypatch):
    real = router._sistema()
    monkeypatch.setattr(router, "_sistema", lambda: real.model_copy(update={
        "generacion_web": real.generacion_web.model_copy(update={"techo_de_gasto_usd": 3.0})}))
    gasto.anotador(con, OBRA, "gen-1")("escritor", 2.0)
    c = _leer(cliente)
    assert (c["techo_usd"], c["alcanzado"]) == (3.0, False)
    gasto.anotador(con, OBRA, "gen-1")("editor", 1.0)
    assert _leer(cliente)["alcanzado"] is True, "llegar al techo es alcanzarlo"
