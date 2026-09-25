"""`PLAN-30` E6: el adaptador de Lean y como se lee lo que devuelve.

Todo con un ejecutor doble: estas pruebas no necesitan `lake`. La que lo ejecuta de
verdad es `test_lean_real.py`.
"""

import hashlib
import sqlite3
import subprocess

import pytest

from app.features.auditoria import lean
from app.features.auditoria.lean import VerificadorLean, interpretar

COBERTURA = "#COBERTURA eventos=5 no_ordenables=0\n"


def test_un_0_con_cobertura_es_limpio():
    assert interpretar(0, 0, COBERTURA).codigo == 0


def test_un_0_sin_linea_de_cobertura_no_es_limpio():
    """Un `0` sin la linea que dice que se miro es un `0` que nadie puede
    distinguir de un programa que no llego a mirar (`F-54`)."""
    assert interpretar(0, 0, "todo bien\n").codigo == 2


def test_el_1_del_generador_no_es_el_1_de_lean():
    """`generar_lean.py` sale con 1 cuando convierte cero eventos. No es una
    violacion: es que no habia nada que comprobar."""
    r = interpretar(1, 0, COBERTURA)
    assert r.codigo == 2 and "cero eventos" in r.detalle


def test_las_violaciones_se_leen_de_las_lineas_de_violacion():
    salida = COBERTURA + ("#VIOLACION L-1 ev-1,ev-2 ev-2 va antes\n"
                          "#VIOLACION L-3 ev-3a,ev-3b per-marta en dos sitios\n")
    r = interpretar(0, 1, salida)
    assert r.codigo == 1
    assert [(v["invariante"], v["eventos"]) for v in r.violaciones] == [
        ("L-1", ["ev-1", "ev-2"]), ("L-3", ["ev-3a", "ev-3b"])]


def test_un_codigo_desconocido_o_un_tiempo_agotado_es_sin_veredicto(tmp_path):
    assert interpretar(0, 7, COBERTURA).codigo == 2

    def se_agota(orden, **kw):
        raise subprocess.TimeoutExpired(orden, 1)

    r = VerificadorLean(lake="lake", ejecutar=se_agota).verificar(_base(tmp_path), "obra-x")
    assert r.codigo == 2 and "tiempo" in r.detalle


def test_sin_lake_es_no_disponible(tmp_path, monkeypatch):
    monkeypatch.setattr(lean.shutil, "which", lambda _: None)
    with pytest.raises(lean.LeanNoDisponible):
        lean.localizar_lake(entorno={}, casa=str(tmp_path))
    monkeypatch.setattr(lean, "localizar_lake", lambda **kw: (_ for _ in ()).throw(
        lean.LeanNoDisponible("no esta")))
    r = VerificadorLean().verificar(_base(tmp_path), "obra-x")
    assert r.codigo is None and "no esta" in r.detalle


def test_verificar_no_escribe_en_el_generado_versionado(tmp_path):
    """Se trabaja en una copia: dos obras a la vez no se pisan y el arbol no se
    ensucia con cada ejecucion de la puerta."""
    generado = lean.LEAN / "Cronologia" / "Generado.lean"
    antes = hashlib.sha256(generado.read_bytes()).hexdigest()
    visto = []

    def ejecutar(orden, cwd=None, **kw):
        visto.append(cwd)
        (lean.pathlib.Path(cwd) / "Cronologia" / "Generado.lean").write_text("pisado")
        salida = COBERTURA.encode() if "exe" in orden else b""
        return subprocess.CompletedProcess(orden, 0, stdout=salida, stderr=b"")

    r = VerificadorLean(lake="lake", ejecutar=ejecutar).verificar(_base(tmp_path), "obra-x")
    assert r.codigo == 0
    assert all(str(lean.LEAN) != str(c) for c in visto)
    assert hashlib.sha256(generado.read_bytes()).hexdigest() == antes


def test_una_base_en_memoria_es_sin_veredicto():
    r = VerificadorLean(lake="lake").verificar(sqlite3.connect(":memory:"), "obra-x")
    assert r.codigo == 2 and "memoria" in r.detalle


def _base(tmp_path):
    con = sqlite3.connect(str(tmp_path / "obra.db"))
    con.execute("CREATE TABLE t (x)")
    return con


def test_verificar_pasa_la_version_al_generador(tmp_path):
    visto = []

    def ejecutar(orden, cwd=None, **kw):
        visto.append(list(orden))
        salida = COBERTURA.encode() if "exe" in orden else b""
        return subprocess.CompletedProcess(orden, 0, stdout=salida, stderr=b"")

    VerificadorLean(lake="lake", ejecutar=ejecutar).verificar(_base(tmp_path), "obra-x",
                                                              version=3)
    generador = [o for o in visto if "generar_lean.py" in o][0]
    assert generador[generador.index("--version") + 1] == "3"


def _generador():
    import importlib.util
    spec = importlib.util.spec_from_file_location("generar_lean",
                                                  lean.LEAN / "generar_lean.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_con_version_el_generador_lee_solo_sus_capitulos_y_en_su_orden(tmp_path):
    """Una version 2 que sustituye el capitulo 2 por `cap-02-v2`. Sin version se leen los
    cuatro, y `cap-02-v2` choca con `cap-02` (los digitos finales dan 2): la obra queda sin
    veredicto. Con version, los tres de la 2, ordenados por la version y no por el id."""
    from app.commons.db import migraciones
    con = sqlite3.connect(str(tmp_path / "obra.db"))
    migraciones.migrar(con)
    con.executescript("""
        CREATE TABLE IF NOT EXISTS evento_cronologico (id TEXT, obra TEXT, t_fabula TEXT,
            duracion_min INTEGER, lugar TEXT, escena TEXT, capitulo TEXT, descripcion TEXT);
        CREATE TABLE IF NOT EXISTS participacion_en_evento (evento TEXT, personaje TEXT,
            presencia TEXT);
        CREATE TABLE IF NOT EXISTS entidad (id TEXT, fecha_de_nacimiento TEXT);
        CREATE TABLE IF NOT EXISTS delta_de_escena (orden INTEGER, escena TEXT,
            version INTEGER, contenido TEXT);
    """)
    for i, cap in enumerate(["cap-01", "cap-02", "cap-03", "cap-02-v2"], start=1):
        con.execute("INSERT INTO evento_cronologico VALUES (?, 'obra-x', ?, 60, 'lug', ?, ?, '')",
                    ("ev-{0}".format(i), "2026-01-0{0}T10:00".format(i), cap + "-e1", cap))
    for numero, caps in ((1, ["cap-01", "cap-02", "cap-03"]),
                         (2, ["cap-01", "cap-02-v2", "cap-03"])):
        for orden, cap in enumerate(caps, start=1):
            con.execute("INSERT INTO capitulo_de_version (obra, numero, orden, capitulo) "
                        "VALUES ('obra-x', ?, ?, ?)", (numero, orden, cap))
    con.commit()
    g = _generador()
    sin = g.generar(g.leer(con, "obra-x"), "obra-x")[1]
    assert sin["capitulos_no_ordenables"], "sin version, cap-02 y cap-02-v2 chocan"
    datos = g.leer(con, "obra-x", version=2)
    assert [e["capitulo"] for e in datos["eventos"]] == ["cap-01", "cap-02-v2", "cap-03"]
    informe = g.generar(datos, "obra-x")[1]
    assert informe["capitulos_no_ordenables"] == [] and informe["eventos_convertidos"] == 3

