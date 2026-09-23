"""Los dos hooks de Claude Code (`SPEC-26` `RF-17`..`RF-19`, `PLAN-26` E10).

Se ejecutan como proceso, con su entrada JSON por stdin, igual que los lanza
Claude Code. **Lo que no prueban**: que Claude Code les entregue en una
delegacion real estas variables y este formato. Eso lo comprueba E13.
"""

import json
import os
import pathlib
import sqlite3
import subprocess
import sys

import pytest

from app.commons.modelo import proveedor
from app.commons.politica import auditoria
from app.features.orquestacion import ciclo

BACKEND = pathlib.Path(__file__).resolve().parents[4]
HOOKS = BACKEND / "hooks"
RAIZ = BACKEND.parent


def _lanzar(script, entrada, **entorno):
    env = {k: v for k, v in os.environ.items() if not k.startswith("HARNESS_")}
    env.update(entorno)
    r = subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(entrada),
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, r.stderr


def _reglas(tmp_path, **cambios):
    datos = dict({"vetadas": ["zoquete"], "nombres": ["Irene Valdés"],
                  "longitud": [10, 50]}, **cambios)
    p = tmp_path / "reglas.json"
    p.write_text(json.dumps(datos), encoding="utf-8")
    return str(p)


def _respuesta(texto):
    return {"last_assistant_message": json.dumps({"texto": texto, "delta": {}})}


BIEN = " ".join(["palabra"] * 20) + " Irene."


def test_sin_harness_agente_los_dos_salen_con_cero_sin_mirar(tmp_path):
    """`RF-19`: una sesion interactiva en el mismo proyecto no se toca."""
    assert _lanzar("validar_capitulo.py", _respuesta("corto"))[0] == 0
    assert _lanzar("policy.py", {"tool_name": "Bash", "tool_input": {}})[0] == 0


def test_un_texto_corto_vuelve_al_escritor_con_el_motivo(tmp_path):
    codigo, err = _lanzar("validar_capitulo.py", _respuesta("tres palabras solo"),
                          HARNESS_AGENTE="escritor", HARNESS_REGLAS=_reglas(tmp_path))
    assert codigo == 2 and "palabras" in err


def test_una_vetada_vuelve_al_escritor(tmp_path):
    codigo, err = _lanzar("validar_capitulo.py", _respuesta(BIEN + " zoquete"),
                          HARNESS_AGENTE="escritor", HARNESS_REGLAS=_reglas(tmp_path))
    assert codigo == 2 and "zoquete" in err


def test_un_nombre_mal_escrito_vuelve_al_escritor(tmp_path):
    codigo, err = _lanzar("validar_capitulo.py", _respuesta(BIEN + " Irena"),
                          HARNESS_AGENTE="escritor", HARNESS_REGLAS=_reglas(tmp_path))
    assert codigo == 2 and "Irene" in err


def test_un_texto_correcto_pasa(tmp_path):
    assert _lanzar("validar_capitulo.py", _respuesta(BIEN), HARNESS_AGENTE="escritor",
                   HARNESS_REGLAS=_reglas(tmp_path))[0] == 0


def test_solo_una_correccion_dentro_de_la_sesion(tmp_path):
    """Con `stop_hook_active` ya se corrigio una vez: se deja terminar y lo que
    quede lo cazan las puertas del codigo. Sin esto, un bucle sin tope."""
    entrada = dict(_respuesta("corto"), stop_hook_active=True)
    assert _lanzar("validar_capitulo.py", entrada, HARNESS_AGENTE="escritor",
                   HARNESS_REGLAS=_reglas(tmp_path))[0] == 0


def test_la_ultima_respuesta_se_lee_de_la_transcripcion(tmp_path):
    t = tmp_path / "t.jsonl"
    t.write_text("\n".join(json.dumps(x) for x in [
        {"type": "user", "message": {"content": "hola"}},
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": json.dumps({"texto": "muy corto"})}]}}]),
        encoding="utf-8")
    codigo, err = _lanzar("validar_capitulo.py", {"transcript_path": str(t)},
                          HARNESS_AGENTE="escritor", HARNESS_REGLAS=_reglas(tmp_path))
    assert codigo == 2 and "palabras" in err


def test_otro_agente_del_pipeline_no_se_valida_como_capitulo(tmp_path):
    assert _lanzar("validar_capitulo.py", _respuesta("corto"), HARNESS_AGENTE="editor",
                   HARNESS_REGLAS=_reglas(tmp_path))[0] == 0


def test_policy_niega_la_herramienta_y_lo_deja_en_el_audit_log(tmp_path):
    db = tmp_path / "obra.db"
    codigo, err = _lanzar("policy.py", {"tool_name": "Read", "tool_input": {"file_path": "x"}},
                          HARNESS_AGENTE="escritor", HARNESS_DB=str(db),
                          HARNESS_OBRA="obra-x")
    assert codigo == 2 and "Read" in err
    [d] = auditoria.decisiones(sqlite3.connect(db), "obra-x")
    assert d["tipo"].value == "herramienta_denegada"
    assert d["detalle"] == {"agente": "escritor", "herramienta": "Read"}


def test_la_sesion_delegada_pone_las_variables(monkeypatch):
    visto = {}

    def run(orden, **kw):
        visto.update(kw.get("env") or {})
        return subprocess.CompletedProcess(orden, 0, stdout="{}", stderr="")

    monkeypatch.setattr(proveedor.subprocess, "run", run)
    proveedor._ejecutar_proceso("claude", "m", "escritor", "p", reglas="/tmp/r.json")
    assert visto["HARNESS_AGENTE"] == "escritor"
    assert visto["HARNESS_REGLAS"] == "/tmp/r.json"


def test_el_proyecto_declara_los_dos_hooks():
    ajustes = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert "validar_capitulo.py" in json.dumps(ajustes["hooks"]["Stop"])
    assert "policy.py" in json.dumps(ajustes["hooks"]["PreToolUse"])


def test_el_directorio_aislado_lleva_el_hook_de_policy(tmp_path):
    """El Editor y el Juez se lanzan fuera del proyecto: sin esto, `RF-18`
    ("cualquier agente del pipeline") no los cubriria."""
    definicion = RAIZ / ".claude" / "agents" / "editor.md"
    base = pathlib.Path(ciclo.preparar_directorio_aislado(definicion, nombre="editor"))
    ajustes = json.loads((base / ".claude" / "settings.json").read_text(encoding="utf-8"))
    comando = ajustes["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
    assert str(HOOKS / "policy.py") in comando
    assert "Stop" not in ajustes["hooks"]
