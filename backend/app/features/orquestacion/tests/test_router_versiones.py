"""`PLAN-23` A5: que cambio, y los dos endpoints de lectura de versiones.

«Cambio» lo decide el backend **por identidad**, no comparando textos (`CE-5`,
`RF-52`). Sin contrato congelado en esta rama: la forma de la respuesta la fijan
estas pruebas (nota «Sin contrato congelado» de `PLAN-23`).
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.features.brief import repository as brief
from app.features.consolidacion import mundo
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import regeneracion
from app.features.orquestacion.tests import obra_regenerable as o
from app.features.planificacion import repository as planes
from app.features.planificacion.tests.conftest import plan
from app.main import app, preparar_base


def _dos_versiones(con, texto_nuevo="texto de c2"):
    for m in (o.escaleta, o.aplicar, o.deltas, o.cronologia, o.memoria, o.mundo, planes):
        m.asegurar_tablas(con)
    ids = o.obra(con)
    planes.guardar(con, "obra-a", 1, plan(), True, "revisor", [])
    mundo.rebobinar(con, regeneracion.semilla_de(con, "obra-a"))
    for c in ids:
        o.escribir(con, o.escena_de(c), "texto de {0}".format(c))
    nuevo = "obra-a-c2-v2"
    brief.crear_version(con, "obra-a", [ids[0], nuevo, ids[2]], anterior=1, commit="def5678")
    escaleta.guardar_escaleta(con, "obra-a", [{
        "id": o.escena_de(nuevo), "orden": 1, "capitulo": nuevo,
        "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"}, "beats": [],
        "pov": "per-ana", "lugar": "lug-casa", "t_discurso": 2}])
    o.escribir(con, o.escena_de(nuevo), texto_nuevo)
    return ids, nuevo


def test_cambio_es_por_capitulo_y_lo_dice_el_backend_sin_comparar_textos():
    con = o.conexion()
    ids, nuevo = _dos_versiones(con)
    assert regeneracion.comparar(con, "obra-a", 1, 2) == [
        {"orden": 1, "capitulo": ids[0], "compartido": True},
        {"orden": 2, "capitulo": nuevo, "compartido": False},
        {"orden": 3, "capitulo": ids[2], "compartido": True},
    ]


def test_un_capitulo_nuevo_con_el_mismo_texto_sigue_contando_como_cambiado():
    con = o.conexion()
    ids, nuevo = _dos_versiones(con, texto_nuevo="texto de obra-a-c2")
    assert [c["compartido"] for c in regeneracion.comparar(con, "obra-a", 1, 2)] == [
        True, False, True]


@pytest.fixture
def cliente(tmp_path):
    # Se monta en memoria y se copia: en disco, cada `with con` es un `fsync`.
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta).close()
    con = o.conexion()
    _dos_versiones(con)
    regeneracion.reverificar(con, "obra-a", 2)
    destino = sqlite3.connect(ruta)
    con.backup(destino)
    destino.close()
    con.close()
    app.state.ruta_db = ruta
    yield TestClient(app), ruta


def test_get_versiones_lista_la_1_y_la_2_con_su_numero_y_su_commit(cliente):
    c, _ = cliente
    r = c.get("/obras/obra-a/versiones")
    assert r.status_code == 200
    vs = r.json()["versiones"]
    assert [v["numero"] for v in vs] == [1, 2]
    assert vs[1]["commit"] == "def5678" and vs[1]["anterior"] == 1
    assert vs[0]["commit"] and vs[0]["creada_en"] and vs[0]["anterior"] is None
    assert c.get("/obras/obra-nadie/versiones").status_code == 404


def test_get_version_da_por_escena_su_estado_y_su_estado_de_verificacion(cliente):
    c, _ = cliente
    r = c.get("/obras/obra-a/versiones/2")
    assert r.status_code == 200
    v = r.json()
    assert v["numero"] == 2 and v["anterior"] == 1
    caps = v["capitulos"]
    assert [x["compartido"] for x in caps] == [True, False, True]
    assert all(x["estado"] == "abierto" for x in caps)
    escenas = [e for x in caps for e in x["escenas"]]
    assert {e["estado"] for e in escenas} == {"consolidada"}
    assert {e["estado_de_verificacion"] for e in escenas} == {EV.VERIFICADA.value}
    # La 1 no se ha reverificado: su verde no consta, y se dice.
    v1 = c.get("/obras/obra-a/versiones/1").json()
    assert {e["estado_de_verificacion"] for x in v1["capitulos"] for e in x["escenas"]} \
        == {EV.SIN_REVERIFICAR.value}
    assert [x["compartido"] for x in v1["capitulos"]] == [None, None, None]
    assert c.get("/obras/obra-a/versiones/9").status_code == 404


def test_ningun_campo_expone_la_configuracion_del_sistema(cliente):
    """`RF-57`: ni modelos, ni topes, ni la ruta de la base."""
    c, ruta = cliente
    for url in ("/obras/obra-a/versiones", "/obras/obra-a/versiones/2"):
        cuerpo = c.get(url).text
        assert ruta not in cuerpo and "obra.db" not in cuerpo
        for prohibida in ("modelo", "tope", "ruta", "techo", "presupuesto"):
            assert prohibida not in cuerpo


def test_get_versiones_dice_cual_es_la_vigente_y_no_es_la_ultima_de_la_lista(cliente):
    """`F-150`: la web deducia la vigente como la ultima de la lista, y mientras la cascada
    escribia una version nueva la marcaba como vigente. El backend la dice (`F-121`: la
    ultima **publicada**), y la web no la calcula (`CLAUDE.md`)."""
    from app.features.auditoria import repository as veredictos
    from app.features.auditoria.publicacion import Decision
    c, ruta = cliente
    vs = c.get("/obras/obra-a/versiones").json()
    assert [v["numero"] for v in vs["versiones"]] == [1, 2]
    assert vs["vigente"] == 1, "la 2 existe pero no esta publicada"
    con = sqlite3.connect(ruta)
    veredictos.guardar(con, "obra-a", Decision(True, [], []), 0, version=2)
    con.close()
    assert c.get("/obras/obra-a/versiones").json()["vigente"] == 2
