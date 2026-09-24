"""`PLAN-23` A1: la medida del arrastre de `SPEC-23` v2, antes que nada.

La media, entre los hechos de la obra con al menos un uso (`C-1`), del numero de
capitulos distintos que lo usan segun `menciona`. **≤ 3 → `S-1`; > 3 → `S-2`.**
Todo con datos inventados: la medida se ejecuta de verdad en B1.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.commons.dominio.enumeraciones import OrigenDeUso as O
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import arrastre
from app.features.orquestacion.tests import obra_regenerable as o


def _completa(con, capitulos=5, **kw):
    ids = o.obra(con, capitulos=capitulos, **kw)
    for c in ids:
        o.escribir(con, o.escena_de(c), "texto de {0}".format(c))
    return ids


@pytest.fixture
def con():
    return o.conexion()


def test_la_media_cuenta_capitulos_distintos_por_mencion(con):
    ids = _completa(con, hechos=[("h-1", "uno"), ("h-2", "dos")])
    for c in ids[:4]:
        o.usar(con, "h-1", c)
    o.usar(con, "h-2", ids[0])
    o.usar(con, "h-2", ids[1])
    r = arrastre.medir(con, "obra-a")
    assert r["medido"] is True
    assert (r["numerador"], r["denominador"]) == (6, 2)
    assert r["arrastre_medio"] == 3.0
    assert {d["hecho"]: d["capitulos_por_mencion"] for d in r["detalle"]} == {"h-1": 4, "h-2": 2}


def test_dos_menciones_en_el_mismo_capitulo_cuentan_uno(con):
    ids = o.obra(con, capitulos=2, hechos=[("h-1", "uno")])
    escaleta.guardar_escaleta(con, "obra-a", [{
        "id": "obra-a-c1-e2", "orden": 2, "capitulo": ids[0],
        "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"}, "beats": [],
        "pov": "per-ana", "lugar": "lug-casa", "t_discurso": 3}])
    for e in ("obra-a-c1-e1", "obra-a-c1-e2", "obra-a-c2-e1"):
        o.escribir(con, e, "texto")
    o.usar(con, "h-1", ids[0], escena="obra-a-c1-e1")
    o.usar(con, "h-1", ids[0], escena="obra-a-c1-e2")
    r = arrastre.medir(con, "obra-a")
    assert r["numerador"] == 1 and r["denominador"] == 1


def test_con_exactamente_3_sale_s1_y_con_algo_mas_sale_s2(con):
    ids = _completa(con, hechos=[("h-1", "uno"), ("h-2", "dos")])
    for c in ids[:3]:
        o.usar(con, "h-1", c)
    for c in ids[:3]:
        o.usar(con, "h-2", c)
    assert arrastre.medir(con, "obra-a")["salida"] == "cascada"
    o.usar(con, "h-2", ids[3])
    r = arrastre.medir(con, "obra-a")
    assert r["arrastre_medio"] == 3.5 and r["salida"] == "selectiva"
    assert arrastre.salida_para(3) == "cascada" and arrastre.salida_para(3.01) == "selectiva"


def test_una_obra_incompleta_no_se_mide_y_dice_que_falta(con):
    ids = o.obra(con, capitulos=3, hechos=[("h-1", "uno")])
    o.escribir(con, o.escena_de(ids[0]), "texto")
    o.usar(con, "h-1", ids[0])
    with con:
        con.execute("DELETE FROM escena WHERE id = ?", (o.escena_de(ids[2]),))
    r = arrastre.medir(con, "obra-a")
    assert r["medido"] is False
    assert "obra-a-c2-e1" in r["faltan"]["escenas_sin_hacer"]
    assert r["faltan"]["capitulos_sin_escena"] == ["obra-a-c3"]
    assert "salida" not in r


def test_sin_ningun_hecho_con_usos_no_se_mide(con):
    _completa(con, hechos=[("h-1", "uno")])
    r = arrastre.medir(con, "obra-a")
    assert r["medido"] is False and "ningun hecho" in r["motivo"]


def test_los_usos_de_otra_obra_con_el_mismo_id_de_hecho_no_cuentan(con):
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno")])
    o.usar(con, "h-1", ids[0])
    otra = o.obra(con, id_obra="obra-b", capitulos=3, hechos=[("h-1", "otro")], commit=None)
    for c in otra:
        o.usar(con, "h-1", c)
    r = arrastre.medir(con, "obra-a")
    assert (r["numerador"], r["denominador"]) == (1, 1)


def test_sin_procedencia_no_se_mide(con):
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno")], commit=None)
    o.usar(con, "h-1", ids[0])
    r = arrastre.medir(con, "obra-a")
    assert r["medido"] is False and "MF-27" in r["motivo"]
    o.procedencia.registrar(con, version="sin_determinar")
    assert arrastre.medir(con, "obra-a")["medido"] is False


def test_el_resultado_lleva_la_direccion_del_sesgo(con):
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno"), ("imp-01", "el perro")])
    o.usar(con, "h-1", ids[0])
    o.usar(con, "imp-01", ids[1])
    o.usar(con, "h-1", ids[1], tipo=U.DEPENDE, origen=O.DELTA)
    r = arrastre.medir(con, "obra-a")
    assert r["sesgo"] == "a la baja, hacia S-1"
    assert r["commit"] == o.COMMIT and r["obra"] == "obra-a"
    assert {d["hecho"]: d["origen"] for d in r["detalle"]} == {
        "h-1": "plan", "imp-01": "imprescindible"}


def test_un_hecho_que_solo_se_usa_por_depende_entra_con_cero(con):
    """`C-1`, la lectura literal: entra en el denominador y aporta 0."""
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno"), ("h-2", "dos")])
    o.usar(con, "h-1", ids[0])
    o.usar(con, "h-2", ids[1], tipo=U.DEPENDE, origen=O.DELTA)
    r = arrastre.medir(con, "obra-a")
    assert (r["numerador"], r["denominador"]) == (1, 2)


def test_un_uso_sin_capitulo_se_cuenta_aparte(con):
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno")])
    o.usar(con, "h-1", ids[0])
    o.cronologia.registrar_usos(con, [{"hecho": "h-1", "escena": o.escena_de(ids[1]),
                                       "capitulo": None, "tipo": U.MENCIONA,
                                       "origen": O.REGLA}])
    r = arrastre.medir(con, "obra-a")
    assert r["detalle"][0]["capitulos_por_mencion"] == 1
    assert r["detalle"][0]["usos_sin_capitulo"] == 1


def test_un_capitulo_reescrito_tras_consolidar_se_informa_aparte(con):
    """Hallazgo 9: la reescritura a delta fijo cambia el texto aceptado y no el acta."""
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno")])
    o.usar(con, "h-1", ids[0])
    e = o.escena_de(ids[1])
    v = escaleta.guardar_borrador(con, e, "texto reescrito", "doble", "hash")
    escaleta.aceptar_reescritura(con, e, v)
    r = arrastre.medir(con, "obra-a")
    assert r["reescritas_tras_consolidar"] == [e]
    assert r["medido"] is True


def test_medir_no_escribe_en_la_base(con):
    ids = _completa(con, capitulos=2, hechos=[("h-1", "uno")])
    o.usar(con, "h-1", ids[0])
    antes = list(con.iterdump())
    cambios = con.total_changes
    arrastre.medir(con, "obra-a")
    assert con.total_changes == cambios
    assert list(con.iterdump()) == antes


def test_el_guion_imprime_json_y_sale_con_1_si_se_niega(tmp_path):
    import sqlite3
    ruta = tmp_path / "base.db"
    con = sqlite3.connect(ruta)
    from app.commons.db import migraciones
    migraciones.migrar(con)
    for m in (o.escaleta, o.aplicar, o.deltas, o.cronologia, o.memoria, o.mundo, o.brief):
        m.asegurar_tablas(con)
    ids = o.obra(con, capitulos=2, hechos=[("h-1", "uno")])
    for c in ids:
        o.escribir(con, o.escena_de(c), "texto")
    con.close()
    guion = Path(__file__).resolve().parents[4] / "medir_arrastre.py"
    r = subprocess.run([sys.executable, "-X", "utf8", str(guion), "--base", str(ruta),
                        "--obra", "obra-a"], capture_output=True, text=True,
                       cwd=guion.parent)
    assert r.returncode == 1, r.stderr
    assert json.loads(r.stdout)["medido"] is False
    con = sqlite3.connect(ruta)
    o.usar(con, "h-1", ids[0])
    con.close()
    r = subprocess.run([sys.executable, "-X", "utf8", str(guion), "--base", str(ruta),
                        "--obra", "obra-a"], capture_output=True, text=True,
                       cwd=guion.parent)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["salida"] == "cascada"
