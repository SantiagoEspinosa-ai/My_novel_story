"""`PLAN-28` E4: el servidor de la story bible como proceso, igual que lo lanzara
Claude Code con `--mcp-config`."""

import json
import os
import pathlib
import sqlite3
import subprocess
import sys

import pytest

from app.commons.db import migraciones
from app.features.observabilidad import repository as obs
from app.features.orquestacion.tests.test_story_bible import _montar

SCRIPT = pathlib.Path(__file__).resolve().parents[4] / "herramientas" / "story_bible.py"


@pytest.fixture
def base(tmp_path):
    ruta = tmp_path / "obra.db"
    con = sqlite3.connect(str(ruta))
    con.row_factory = sqlite3.Row
    migraciones.migrar(con)
    _montar(con, "obra-a")
    con.close()
    return str(ruta)


def _lanzar(mensajes, **entorno):
    env = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")}
    env.update(entorno)
    r = subprocess.run([sys.executable, str(SCRIPT)], env=env, capture_output=True,
                       input="".join(json.dumps(m) + "\n" for m in mensajes),
                       text=True, encoding="utf-8", timeout=60)
    return r.returncode, [json.loads(l) for l in r.stdout.splitlines() if l.strip()], r.stderr


def _llamar(nombre, argumentos, id_=1):
    return {"jsonrpc": "2.0", "id": id_, "method": "tools/call",
            "params": {"name": nombre, "arguments": argumentos}}


def _entorno(base):
    return {"HARNESS_DB": base, "HARNESS_OBRA": "obra-a", "HARNESS_AGENTE": "escritor",
            "HARNESS_DELEGACION": "del-7"}


def test_el_servidor_como_proceso_atiende_las_tres_tools(base):
    codigo, respuestas, _ = _lanzar(
        [{"jsonrpc": "2.0", "id": 0, "method": "tools/list"},
         _llamar("hechos", {}, 1), _llamar("ficha", {"id": "obra-a-per-irene"}, 2),
         _llamar("cronologia", {}, 3)], **_entorno(base))
    assert codigo == 0
    assert {t["name"] for t in respuestas[0]["result"]["tools"]} == {"hechos", "ficha", "cronologia"}
    assert all(not r["result"]["isError"] for r in respuestas[1:])
    assert "Irene Valdés" in respuestas[2]["result"]["content"][0]["text"]


def test_sin_harness_obra_el_servidor_no_arranca(base):
    codigo, respuestas, error = _lanzar([_llamar("hechos", {})], HARNESS_DB=base)
    assert codigo != 0 and respuestas == [] and "HARNESS_OBRA" in error


def test_el_servidor_no_puede_escribir_en_la_story_bible(base):
    """`RF-04` hecho cumplir por SQLite, no por disciplina: la conexion con la que el
    servidor lee la story bible es de solo lectura, y la de las trazas es otra."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("servidor_story_bible", SCRIPT)
    servidor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(servidor)
    lectura, traza = servidor.abrir_conexiones(base)
    with pytest.raises(sqlite3.OperationalError):
        lectura.execute("UPDATE entidad SET vital = 'muerto'")
    traza.execute("SELECT 1")


def test_cada_llamada_deja_su_fila_con_la_delegacion(base):
    _lanzar([_llamar("hechos", {}, 1), _llamar("ficha", {"id": "nadie"}, 2)], **_entorno(base))
    con = sqlite3.connect(base)
    assert [l["validacion"] for l in obs.llamadas_de(con, "del-7")] == ["ok", "no_existe"]


def test_harness_version_llega_como_numero_y_sin_ella_es_la_vigente():
    """`PLAN-23` B-S1.1: el servidor lee la version que se escribe de `HARNESS_VERSION`."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("servidor_story_bible", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    assert modulo.version_del_entorno({"HARNESS_VERSION": "2"}) == 2
    assert modulo.version_del_entorno({}) is None
