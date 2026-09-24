"""`backend/pedir_cambio.py`: un cambio real sin la web (`PLAN-23` B-S1.1), con dobles.

El guion llama al mismo servicio que la API -`proponer`, `pedir` y la rama de la salida-
con los agentes de `novela_regalo.agentes`. Aqui esos agentes son dobles y Lean es fijo:
**ninguna prueba gasta**. Datos inventados.
"""

import importlib.util
import pathlib
import sqlite3

from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.features.brief import repository as brief
from app.features.orquestacion.tests.test_cascada import (
    CAPS, OBRA, _EscritorDeLaVersion, _agentes, _base)
from app.features.orquestacion.tests.test_novela import _LeanFijo, _con_coste
from app.features.planificacion.tests.conftest import ficha


def _guion():
    ruta = pathlib.Path(__file__).resolve().parents[4] / "pedir_cambio.py"
    spec = importlib.util.spec_from_file_location("pedir_cambio", ruta)
    guion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guion)
    return guion


def _en_fichero(tmp_path, **kw):
    ruta = str(tmp_path / "obra.db")
    mem = _base(**kw)
    destino = sqlite3.connect(ruta)
    mem.backup(destino)
    destino.close()
    return ruta


class _NoLlamar:
    """Si alguien lo llama, la prueba falla: sin `--confirmo-el-gasto` no se delega."""

    def __call__(self, *a, **kw):
        raise AssertionError("sin confirmar el gasto no se crean agentes")


def _preparado(monkeypatch, agentes=None):
    guion = _guion()
    monkeypatch.setattr(guion, "agentes", agentes or _NoLlamar())
    monkeypatch.setattr(guion, "crear_exportador", lambda: ExportadorEnMemoria())
    monkeypatch.setattr(guion, "crear_lean", lambda sistema: _LeanFijo())
    return guion


HECHO = ["--hecho", "imp-02", "--enunciado", "el viaje en tren nocturno a Lisboa",
         "--texto", "que el tren sea de noche"]


def _cuantos(ruta, tabla):
    con = sqlite3.connect(ruta)
    try:
        return con.execute("SELECT COUNT(*) FROM {0}".format(tabla)).fetchone()[0]
    except sqlite3.OperationalError:
        return 0
    finally:
        con.close()


def test_sin_confirmar_el_gasto_imprime_la_propuesta_y_sale_con_2(tmp_path, monkeypatch,
                                                                 capsys):
    ruta = _en_fichero(tmp_path)
    guion = _preparado(monkeypatch)
    codigo = guion.main(["--base", ruta, "--obra", OBRA] + HECHO)
    salida = capsys.readouterr().out
    assert codigo == 2, salida
    assert "salida: cascada" in salida
    assert ", ".join(CAPS[2:]) in salida
    assert "reescribimos lo que dependía de esto: el capítulo 3 y todos los siguientes" \
        in salida
    assert "si la prosa contradice sin que el delta lo declare, no se toca" in salida
    assert "--confirmo-el-gasto" in salida
    assert _cuantos(ruta, "peticion_de_cambio") == 0 and _cuantos(ruta, "trabajo") == 0
    con = sqlite3.connect(ruta)
    assert [v["numero"] for v in brief.versiones_de(con, OBRA)] == [1]
    con.close()


def test_con_el_gasto_confirmado_regenera_y_dice_capitulos_coste_y_veredicto(
        tmp_path, monkeypatch, capsys):
    ruta = _en_fichero(tmp_path)
    medidos = _con_coste(_agentes(_EscritorDeLaVersion()), coste=0.01)
    guion = _preparado(monkeypatch, agentes=lambda sistema, entorno: medidos)
    codigo = guion.main(["--base", ruta, "--obra", OBRA, "--confirmo-el-gasto"] + HECHO)
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    assert "version 2" in salida
    assert "capitulos cambiados: " + ", ".join(
        "{0}-v2".format(c) for c in CAPS[2:]) in salida
    assert "capitulos compartidos: " + ", ".join(CAPS[:2]) in salida
    # 8 capitulos x (Escritor, Editor, Resumidor) + el juicio de obra de la puerta.
    assert "delegaciones: 25 | sin coste medido: 0" in salida, salida
    assert "coste leido: 0.2500 USD" in salida
    assert "publicada" in salida and "NO se publica" not in salida
    assert "=== LANGFUSE ===" in salida
    con = sqlite3.connect(ruta)
    assert [v["numero"] for v in brief.versiones_de(con, OBRA)] == [1, 2]
    assert brief.version_vigente(con, OBRA) == 2
    con.close()


def test_un_renombrado_por_la_terminal_empieza_donde_sale_el_nombre(tmp_path, monkeypatch,
                                                                    capsys):
    ruta = _en_fichero(tmp_path)
    guion = _preparado(monkeypatch)
    codigo = guion.main(["--base", ruta, "--obra", OBRA, "--personaje", "obra-x-per-brisa",
                         "--nombre", "Nala", "--texto", "el perro se llama Nala"])
    salida = capsys.readouterr().out
    assert codigo == 2
    assert "el capítulo 1 y todos los siguientes" in salida


def test_una_peticion_no_admitida_sale_con_1_y_dice_por_que(tmp_path, monkeypatch, capsys):
    ruta = _en_fichero(tmp_path)
    guion = _preparado(monkeypatch)
    codigo = guion.main(["--base", ruta, "--obra", OBRA, "--hecho", "h-que-no-existe",
                         "--enunciado", "x", "--texto", "y", "--confirmo-el-gasto"])
    salida = capsys.readouterr().out
    assert codigo == 1 and "no es un hecho de esta obra" in salida
    assert _cuantos(ruta, "peticion_de_cambio") == 0


def test_sin_ficha_en_la_base_lo_dice_y_no_escribe_nada(tmp_path, monkeypatch, capsys):
    """`F-91`: la ficha se borra al entregar. Sin ella el guion se para antes de crear la
    version, y dice que se puede dar con `--ficha`."""
    ruta = _en_fichero(tmp_path, con_ficha=False)
    guion = _preparado(monkeypatch, agentes=lambda s, e: _agentes(_EscritorDeLaVersion()))
    codigo = guion.main(["--base", ruta, "--obra", OBRA, "--confirmo-el-gasto"] + HECHO)
    salida = capsys.readouterr().out
    assert codigo == 1 and "F-91" in salida and "--ficha" in salida
    con = sqlite3.connect(ruta)
    assert [v["numero"] for v in brief.versiones_de(con, OBRA)] == [1]
    con.close()


def test_con_la_ficha_en_un_fichero_regenera_aunque_la_base_no_la_tenga(
        tmp_path, monkeypatch, capsys):
    ruta = _en_fichero(tmp_path, con_ficha=False)
    ruta_ficha = tmp_path / "ficha.json"
    ruta_ficha.write_text(ficha().model_dump_json(), encoding="utf-8")
    guion = _preparado(monkeypatch, agentes=lambda s, e: _agentes(_EscritorDeLaVersion()))
    codigo = guion.main(["--base", ruta, "--obra", OBRA, "--ficha", str(ruta_ficha),
                         "--confirmo-el-gasto"] + HECHO)
    salida = capsys.readouterr().out
    assert codigo == 0, salida


def test_una_base_que_no_existe_no_se_crea(tmp_path, monkeypatch, capsys):
    guion = _preparado(monkeypatch)
    ruta = tmp_path / "no-esta.db"
    codigo = guion.main(["--base", str(ruta), "--obra", OBRA] + HECHO)
    assert codigo == 1 and not ruta.exists()
    assert "no existe" in capsys.readouterr().out
