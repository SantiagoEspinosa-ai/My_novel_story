"""`PLAN-36` G1 (`SPEC-36` `RF-02`, `RF-03`): el titulo en la generacion y la administracion.
Todo por SQL y resuelto aqui: la web lo pinta. Datos inventados."""

from app.commons.modelo import gasto
from app.features.regalo.tests.conftest import OBRA, OTRA, fijar_fase, id_escena


def _hallazgo(con, escena, severidad, estado="abierto"):
    with con:
        con.execute("INSERT INTO hallazgo (invariante, verificador, escena, severidad, estado, "
                    "descripcion) VALUES ('INV-17', 'v', ?, ?, ?, 'inventado')",
                    (escena, severidad, estado))


def _veredicto(con, obra, ronda, codigo):
    from app.commons.db.migraciones import VEREDICTO_SQL
    with con:
        con.executescript(VEREDICTO_SQL)
        con.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
                    "condiciones, codigo_lean, no_ejecutadas) VALUES (?, 1, ?, ?, '[]', ?, '[]')",
                    (obra, ronda, int(codigo == 0), codigo))


def test_la_generacion_trae_el_titulo_de_la_obra(cliente):
    assert cliente.get("/obras/{0}/generacion".format(OBRA)).json()["titulo"] == "El mapa de Irene"


def test_sin_montar_el_titulo_es_nulo(cliente, con):
    fijar_fase(con, "obra-sin-montar", "planificando", total=None)
    assert cliente.get("/obras/obra-sin-montar/generacion").json()["titulo"] is None


def test_la_administracion_trae_cada_obra_con_su_coste_y_hallazgos(cliente, con):
    fijar_fase(con, OBRA, "publicada")
    anotar = gasto.anotador(con, OBRA, "gen-1")
    anotar("escritor", 1.5)
    anotar("editor", None)
    _hallazgo(con, id_escena(OBRA, 1), "mayor")
    _hallazgo(con, id_escena(OBRA, 2), "menor")
    _hallazgo(con, id_escena(OBRA, 3), "mayor", estado="resuelto")
    r = cliente.get("/admin/obras")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["techo_usd"] > 0 and d["gastado"]["usd"] == 1.5
    obras = {o["id"]: o for o in d["obras"]}
    a = obras[OBRA]
    assert a["titulo"] == "El mapa de Irene" and a["fase"] == "publicada"
    assert a["coste"]["usd"] == 1.5 and a["coste"]["delegaciones"] == 2
    assert a["coste"]["es_suelo"] is True
    assert a["hallazgos"] == {"bloqueante": 0, "mayor": 1, "menor": 1}
    b = obras[OTRA]
    assert b["coste"] is None and b["fase"] is None and b["codigo_lean"] is None


def test_el_codigo_de_lean_es_el_del_ultimo_veredicto(cliente, con):
    _veredicto(con, OBRA, 1, 2)
    _veredicto(con, OBRA, 2, 0)
    obras = {o["id"]: o for o in cliente.get("/admin/obras").json()["obras"]}
    assert obras[OBRA]["codigo_lean"] == 0
