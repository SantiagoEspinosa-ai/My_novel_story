"""`PLAN-37` H1 (`SPEC-37`): la historia de una novela, resuelta en el backend. Datos
inventados, sembrados por SQL con horas fijas: la atribucion del coste depende de ellas."""

import json

import pytest

from app.commons.db.migraciones import PETICION_SQL, VEREDICTO_SQL, VERSIONES_SQL
from app.features.regalo.tests.conftest import CRITERIOS, OBRA, id_capitulo, id_escena

PLAN_SQL = """CREATE TABLE IF NOT EXISTS plan_de_obra (obra TEXT, version INTEGER, plan TEXT,
aprobado INTEGER, origen TEXT, objeciones TEXT)"""


def _fase(con, fase, desde, capitulo=None, motivo=None):
    con.execute("INSERT INTO progreso_de_generacion (obra, fase, capitulo, total_de_capitulos, "
                "motivo, desde) VALUES (?, ?, ?, 10, ?, ?)", (OBRA, fase, capitulo, motivo, desde))


def _gasto(con, agente, usd, cuando):
    con.execute("INSERT INTO gasto_de_delegacion (obra, agente, generacion, coste_usd, cuando) "
                "VALUES (?, ?, 'gen-1', ?, ?)", (OBRA, agente, usd, cuando))


@pytest.fixture
def historia(con):
    with con:
        con.executescript(PLAN_SQL + ";" + VERSIONES_SQL + PETICION_SQL + VEREDICTO_SQL)
        con.execute("INSERT INTO plan_de_obra VALUES (?, 1, NULL, 0, 'revisor', ?)",
                    (OBRA, json.dumps(["falta el recuerdo de Lisboa"])))
        con.execute("INSERT INTO plan_de_obra VALUES (?, 2, '{}', 1, 'revisor', '[]')", (OBRA,))
        _gasto(con, "entrevistador", 0.05, "2026-09-24 09:00:00")
        _fase(con, "planificando", "2026-09-24 10:00:00")
        _gasto(con, "planificador", 1.0, "2026-09-24 10:01:00")
        _gasto(con, "revisor_plan", 0.5, "2026-09-24 10:02:00")
        _fase(con, "escribiendo", "2026-09-24 10:10:00", 1)
        _gasto(con, "escritor", 0.8, "2026-09-24 10:11:00")
        _fase(con, "editando", "2026-09-24 10:12:00", 1)
        _gasto(con, "editor", 0.4, "2026-09-24 10:13:00")
        _gasto(con, "editor", None, "2026-09-24 10:14:00")
        _fase(con, "escribiendo", "2026-09-24 10:20:00", 3)
        _gasto(con, "escritor", 1.2, "2026-09-24 10:21:00")
        _fase(con, "parada", "2026-09-24 10:30:00", 3, "bloqueante")
        _fase(con, "en_la_puerta", "2026-09-24 11:00:00")
        _gasto(con, "editor", 0.3, "2026-09-24 11:01:00")
        # El capitulo 1, aceptado en su segundo intento, con sus seis notas.
        e1, e3 = id_escena(OBRA, 1), id_escena(OBRA, 3)
        for v in (1, 2):
            con.execute("INSERT INTO borrador (escena, version, texto) VALUES (?, ?, 't')", (e1, v))
        for v in (1, 2, 3):
            con.execute("INSERT INTO borrador (escena, version, texto) VALUES (?, ?, 't')", (e3, v))
        con.execute("UPDATE escena SET estado = 'consolidada', borrador_aceptado = 2 WHERE id = ?",
                    (e1,))
        for c, n in zip(CRITERIOS, (4, 5, 3, 4, 2, 5)):
            con.execute("INSERT INTO valoracion_del_editor (escena, version, criterio, nota, "
                        "justificacion, instruccion) VALUES (?, 2, ?, ?, 'porque', '')", (e1, c, n))
        con.execute("INSERT INTO hallazgo (invariante, verificador, escena, severidad, estado, "
                    "descripcion) VALUES ('INV-26', 'editor', ?, 'mayor', 'abierto', 'ritmo bajo')",
                    (e1,))
        # Dos versiones: la 2 nacio de una peticion y cambia el capitulo 3.
        caps = [id_capitulo(OBRA, n) for n in range(1, 11)]
        con.execute("INSERT INTO version_de_obra (obra, numero, anterior, peticion, \"commit\", "
                    "creada_en) VALUES (?, 1, NULL, NULL, 'c', '2026-09-24 09:59:00')", (OBRA,))
        con.execute("INSERT INTO peticion_de_cambio (id, obra, version_de_partida, clase, texto) "
                    "VALUES (7, ?, 1, 'hecho', 'el perro se llama Nala')", (OBRA,))
        con.execute("INSERT INTO version_de_obra (obra, numero, anterior, peticion, \"commit\", "
                    "creada_en) VALUES (?, 2, 1, 7, 'c', '2026-09-25 09:00:00')", (OBRA,))
        for n, cap in enumerate(caps, 1):
            con.execute("INSERT INTO capitulo_de_version VALUES (?, 1, ?, ?)", (OBRA, n, cap))
            con.execute("INSERT INTO capitulo_de_version VALUES (?, 2, ?, ?)",
                        (OBRA, n, cap + "-v2" if n == 3 else cap))
        con.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
                    "condiciones, codigo_lean, no_ejecutadas, cuando) VALUES (?, 1, 1, 0, ?, 2, "
                    "'[]', '2026-09-24 11:02:00')", (OBRA, json.dumps(
                        [{"invariante": "INV-28", "capitulo": None, "detalle": "sin veredicto"}])))
        con.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
                    "condiciones, codigo_lean, no_ejecutadas, cuando) VALUES (?, 1, 2, 1, '[]', 0, "
                    "'[]', '2026-09-24 11:10:00')", (OBRA,))


def _leer(cliente):
    r = cliente.get("/admin/obras/{0}/historia".format(OBRA))
    assert r.status_code == 200, r.text
    return r.json()


def _de(h, tipo):
    return [e for e in h["eventos"] if e["tipo"] == tipo]


def test_la_historia_cuenta_los_capitulos_con_sus_notas_y_su_coste(cliente, historia):
    h = _leer(cliente)
    tipos = [e["tipo"] for e in h["eventos"]]
    assert tipos[:3] == ["entrevista", "ronda_del_plan", "ronda_del_plan"]
    [uno] = [e for e in _de(h, "capitulo") if e["capitulo"] == 1]
    assert [n["nota"] for n in uno["notas"]] == [4, 5, 3, 4, 2, 5]
    assert [n["bajo_el_umbral"] for n in uno["notas"]].count(True) == 1
    assert uno["intentos"] == 2 and uno["version"] == 1
    assert uno["coste"]["usd"] == pytest.approx(1.2) and uno["coste"]["es_suelo"] is True
    assert uno["cuando"] == "2026-09-24 10:10:00"
    plan = _de(h, "ronda_del_plan")
    assert plan[0]["aprobado"] is False and plan[0]["objeciones"] == ["falta el recuerdo de Lisboa"]
    assert plan[1]["coste"]["usd"] == pytest.approx(1.5)
    assert _de(h, "entrevista")[0]["coste"]["usd"] == pytest.approx(0.05)


def test_una_parada_trae_su_capitulo_su_motivo_y_sus_intentos(cliente, historia):
    [p] = _de(_leer(cliente), "parada")
    assert (p["capitulo"], p["motivo"], p["intentos"]) == (3, "bloqueante", 3)
    assert p["coste"]["usd"] == pytest.approx(1.2)


def test_las_rondas_de_la_puerta_traen_lean_y_condiciones(cliente, historia):
    r1, r2 = _de(_leer(cliente), "ronda_de_la_puerta")
    assert (r1["ronda"], r1["aprobado"], r1["codigo_lean"]) == (1, False, 2)
    assert r1["condiciones"] == ["INV-28 (obra): sin veredicto"]
    assert (r2["aprobado"], r2["codigo_lean"]) == (True, 0)
    assert r1["coste"]["usd"] == pytest.approx(0.3)


def test_una_version_nueva_trae_su_peticion_y_los_capitulos_que_cambiaron(cliente, historia):
    [v] = _de(_leer(cliente), "version")
    assert (v["version"], v["peticion"], v["capitulos_cambiados"]) == (2, "el perro se llama Nala", [3])


def test_el_coste_por_agente_y_los_abiertos_con_su_invariante(cliente, historia):
    h = _leer(cliente)
    agentes = {a["agente"]: a for a in h["por_agente"]}
    assert agentes["escritor"]["usd"] == pytest.approx(2.0)
    assert agentes["editor"]["sin_coste"] == 1 and agentes["editor"]["es_suelo"] is True
    assert h["abiertos"] == [{"invariante": "INV-26", "severidad": "mayor", "capitulo": 1,
                              "descripcion": "ritmo bajo"}]
    t = h["totales"]
    assert t["paradas"] == 1 and t["version_vigente"] == 1
    assert t["nota_media"] == pytest.approx(23 / 6, abs=0.01)
    assert "progreso" in h["atribucion"]


def test_una_obra_que_no_existe_es_404(cliente):
    assert cliente.get("/admin/obras/no-existe/historia").status_code == 404


def test_un_capitulo_sin_hora_va_antes_de_la_puerta_de_su_version(cliente, con, historia):
    """Un capitulo sin progreso (escrito sin fase apuntada) se escribio despues de crear su
    version y antes de pasar la puerta: se ordena por la fecha de la version."""
    from app.features.regalo.tests.conftest import id_capitulo as idc
    with con:
        con.execute("INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, beats, pov, "
                    "lugar, capitulo, borrador_aceptado) VALUES (?, ?, 1, 'consolidada', '{}', "
                    "'[]', 'p', 'l', ?, 1)", ("esc-v2", OBRA, idc(OBRA, 3) + "-v2"))
        con.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
                    "condiciones, codigo_lean, no_ejecutadas, cuando) VALUES (?, 2, 1, 1, '[]', 0, "
                    "'[]', '2026-09-25 10:00:00')", (OBRA,))
    eventos = [e for e in _leer(cliente)["eventos"] if e["version"] == 2]
    assert [e["tipo"] for e in eventos] == ["version", "capitulo", "ronda_de_la_puerta"]
    assert eventos[1]["cuando"] is None
