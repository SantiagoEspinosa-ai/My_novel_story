"""E3 — La delegacion, probada sin arrancar ningun proceso.

El ejecutor se inyecta, asi que **ninguna prueba sale de la maquina** ni gasta
nada. Lo que se prueba es lo que la rama `main` pago descubriendo:

    - el prompt va por stdin y no como argumento;
    - las vallas de bloque de codigo las anade la sesion intermedia;
    - una respuesta ilegible es fallo de contrato, no de transporte.
"""

import pytest

from app.commons.modelo import proveedor
from app.commons.modelo.doble import DobleDelModelo

RESPUESTA_OK = '{"texto": "La puerta estaba abierta.", "delta": {"cambio_de_valor": {}}}'


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv(proveedor.VARIABLES["modelo_escritor"], "modelo-de-prueba")
    monkeypatch.setenv(proveedor.VARIABLES["ejecutable"], "claude-de-mentira")


def test_sin_la_variable_del_modelo_falla_al_construir(monkeypatch):
    monkeypatch.delenv(proveedor.VARIABLES["modelo_escritor"], raising=False)
    with pytest.raises(proveedor.FaltaEntorno) as e:
        proveedor.SesionDelegada()
    assert proveedor.VARIABLES["modelo_escritor"] in str(e.value)


def test_el_prompt_va_por_stdin_y_no_como_argumento(entorno):
    """Hallazgo 14. `cmd.exe` termina el comando en el primer salto de linea."""
    visto = {}

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None):
        visto["orden_entera"] = (ejecutable, modelo, agente)
        visto["prompt"] = prompt
        return RESPUESTA_OK

    c = proveedor.SesionDelegada(ejecutar=ejecutar)
    prompt = "primera linea\nsegunda linea que cmd.exe se comeria"
    c.llamar(prompt)
    assert visto["prompt"] == prompt, "el prompt entero, por stdin"
    assert "segunda linea" not in str(visto["orden_entera"])


def test_las_vallas_de_bloque_de_codigo_no_pierden_la_escena(entorno):
    """Hallazgo 7: las anade la sesion intermedia, no el modelo."""
    con_vallas = "```json\n" + RESPUESTA_OK + "\n```"
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: con_vallas)
    assert c.llamar("x")["texto"].startswith("La puerta")


def test_se_rescata_el_primer_objeto_equilibrado_con_preambulo(entorno):
    """Un modelo que saluda antes del JSON no cuesta una escena entera."""
    ruidosa = "Claro, aqui tienes la escena:\n" + RESPUESTA_OK + "\nEspero que te sirva."
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: ruidosa)
    assert c.llamar("x")["delta"] == {"cambio_de_valor": {}}


def test_las_llaves_anidadas_no_cortan_en_la_primera_de_cierre(entorno):
    anidado = '{"texto": "x", "delta": {"cambio_de_valor": {"eje": "vida"}}}'
    assert proveedor.primer_objeto_equilibrado("ruido " + anidado + " mas ruido") == anidado


def test_una_respuesta_ilegible_es_fallo_de_contrato_no_de_transporte(entorno):
    """Por `O-3` no se reintenta: repetirlo repite el error."""
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: "lo siento, no puedo ayudarte")
    with pytest.raises(proveedor.RespuestaIlegible):
        c.llamar("x")


def test_un_proceso_que_no_arranca_es_fallo_de_transporte(entorno):
    def revienta(*a, **k):
        raise OSError("WinError 2")
    c = proveedor.SesionDelegada(ejecutar=revienta)
    with pytest.raises(proveedor.FalloDeTransporte):
        c.llamar("x")


def test_no_hay_usage_y_el_campo_no_se_rellena_con_cero(entorno):
    """`SPEC-14` C-3: los tokens los reporta la sesion, no vienen aqui."""
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: RESPUESTA_OK)
    assert "usage" not in c.llamar("x")


def test_la_firma_es_la_misma_que_la_del_doble(entorno):
    """Lo que hace que el bucle probado en E2 sea el mismo que correra en E5."""
    real = proveedor.SesionDelegada(ejecutar=lambda *a, **k: RESPUESTA_OK)
    for atributo in ("nombre", "llamar"):
        assert hasattr(real, atributo) and hasattr(DobleDelModelo(), atributo)


def test_el_cwd_viaja_al_ejecutor_porque_es_lo_que_aisla(entorno):
    """`omitClaudeMd` se ignora en silencio en 2.1.274; lo que aisla es el cwd.

    Comprobado con un control: con la opcion a `false` y a `true` el agente
    enumero los seis niveles del presupuesto; desde un directorio vacio
    respondio NO LO SE. El cuerpo del agente si se aplica, asi que la
    definicion se carga y **la opcion se ignora**.
    """
    visto = {}

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None):
        visto["cwd"] = cwd
        return RESPUESTA_OK

    proveedor.SesionDelegada(ejecutar=ejecutar, cwd="/un/directorio/vacio").llamar("x")
    assert visto["cwd"] == "/un/directorio/vacio"


def test_sin_cwd_la_delegacion_arranca_en_la_raiz_del_repositorio(entorno):
    """`F-61`: Claude Code solo carga los hooks de `.claude/settings.json` si la
    sesion arranca en la carpeta que lo contiene. Heredando el directorio del
    proceso -`backend/` en los guiones- los hooks no se cargaban nunca."""
    import pathlib
    visto = {}

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None):
        visto["cwd"] = cwd
        return RESPUESTA_OK

    proveedor.SesionDelegada(ejecutar=ejecutar).llamar("x")
    raiz = pathlib.Path(visto["cwd"])
    assert (raiz / ".claude" / "settings.json").exists()
    assert (raiz / "backend").is_dir()


# --- `PLAN-28` E6: la delegacion ofrece las tools --------------------------------

import json as _json  # noqa: E402
import subprocess as _subprocess  # noqa: E402

SOBRE = _json.dumps({"type": "result", "result": RESPUESTA_OK, "total_cost_usd": 0.01,
                     "usage": {"input_tokens": 5, "output_tokens": 5}})


def _orden_de(monkeypatch, **kw):
    visto = {}

    def run(orden, **opciones):
        visto["orden"] = orden
        if "--mcp-config" in orden:
            with open(orden[orden.index("--mcp-config") + 1], encoding="utf-8") as f:
                visto["config"] = _json.load(f)
        return _subprocess.CompletedProcess(orden, 0, stdout=SOBRE, stderr="")

    monkeypatch.setattr(proveedor.subprocess, "run", run)
    proveedor._ejecutar_proceso("claude", "modelo", kw.pop("agente", "escritor"), "p", **kw)
    return visto


def test_con_herramientas_la_orden_lleva_mcp_estricto_y_solo_las_permitidas(monkeypatch):
    v = _orden_de(monkeypatch, herramientas={"db": "obra.db", "obra": "obra-a",
                                             "delegacion": "d1"})
    orden = v["orden"]
    assert "--strict-mcp-config" in orden
    permitidas = orden[orden.index("--allowedTools") + 1].split(",")
    assert permitidas == ["mcp__story_bible__hechos", "mcp__story_bible__ficha",
                          "mcp__story_bible__cronologia"]


def test_la_configuracion_mcp_va_en_un_fichero_con_obra_base_agente_y_delegacion(monkeypatch):
    """En un fichero y no como cadena: la orden pasa por un `.CMD`, y un JSON con
    comillas como argumento corre el riesgo de pasar por `cmd.exe` (hallazgo 3)."""
    import os
    v = _orden_de(monkeypatch, herramientas={"db": "obra.db", "obra": "obra-a",
                                             "delegacion": "d1"})
    servidor = v["config"]["mcpServers"]["story_bible"]
    assert os.path.isabs(servidor["args"][0]) and servidor["args"][0].endswith("story_bible.py")
    assert servidor["env"]["HARNESS_OBRA"] == "obra-a"
    assert servidor["env"]["HARNESS_AGENTE"] == "escritor"
    assert servidor["env"]["HARNESS_DELEGACION"] == "d1"
    assert os.path.isabs(servidor["env"]["HARNESS_DB"])


def test_sin_herramientas_la_orden_no_lleva_mcp(monkeypatch):
    orden = _orden_de(monkeypatch)["orden"]
    assert "--mcp-config" not in orden and "--allowedTools" not in orden


def test_cada_delegacion_del_pipeline_apaga_las_herramientas_integradas(monkeypatch):
    """`D-2`: `--tools \"\"` en todos los agentes, no solo en los que tienen tools."""
    for agente in ("escritor", "planificador", "resumidor"):
        orden = _orden_de(monkeypatch, agente=agente)["orden"]
        assert orden[orden.index("--tools") + 1] == ""


def test_toda_delegacion_con_agente_lleva_strict_mcp_config_aunque_no_tenga_herramientas(monkeypatch):
    """`PLAN-22` DP-6: con un `.mcp.json` en la raiz, una delegacion sin tools que no
    lleve `--strict-mcp-config` cargaria el browser MCP. El hook negaria la llamada, pero
    el servidor arrancaria igual (hallazgo 11)."""
    for agente in ("planificador", "revisor_plan", "resumidor", "juez", "escritor"):
        orden = _orden_de(monkeypatch, agente=agente)["orden"]
        assert "--strict-mcp-config" in orden, agente
        assert "--mcp-config" not in orden, "sin tools no se le da ningun servidor"


def test_la_delegacion_devuelve_su_identificador_en_las_medidas(entorno):
    visto = {}

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None, herramientas=None):
        visto["herramientas"] = herramientas
        return SOBRE

    s = proveedor.SesionDelegada(agente="escritor", ejecutar=ejecutar)
    s.herramientas = {"db": "obra.db", "obra": "obra-a"}
    r = s.llamar("x")
    assert r["medidas"]["delegacion"] == visto["herramientas"]["delegacion"]
    assert s.llamar("y")["medidas"]["delegacion"] != r["medidas"]["delegacion"], \
        "una delegacion nueva en cada llamada"


# --- `PLAN-29` E1: el coste de lo ilegible y un entorno limpio ---------------------

def _entorno_de(monkeypatch, **kw):
    visto = {}

    def run(orden, **opciones):
        visto["env"] = opciones["env"]
        return _subprocess.CompletedProcess(orden, 0, stdout=SOBRE, stderr="")

    monkeypatch.setattr(proveedor.subprocess, "run", run)
    proveedor._ejecutar_proceso("claude", "modelo", "escritor", "p", **kw)
    return visto["env"]


def test_una_respuesta_ilegible_conserva_las_medidas_del_sobre(entorno):
    """El sobre se pago aunque el modelo devolviera algo que no parsea: su coste no se pierde."""
    sobre = _json.dumps({"type": "result", "result": "no es json", "total_cost_usd": 0.07,
                         "usage": {"input_tokens": 11, "output_tokens": 13}})
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: sobre)
    with pytest.raises(proveedor.RespuestaIlegible) as e:
        c.llamar("x")
    assert e.value.medidas["coste_usd"] == 0.07
    assert e.value.medidas["tokens_entrada"] == 11


def test_un_sobre_ilegible_no_inventa_medidas(entorno):
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: "basura sin llaves")
    with pytest.raises(proveedor.RespuestaIlegible) as e:
        c.llamar("x")
    assert e.value.medidas is None


def test_la_delegacion_no_hereda_las_claves_de_langfuse(monkeypatch):
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-dummy-de-prueba")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-dummy-de-prueba")
    env = _entorno_de(monkeypatch, entorno={"LANGFUSE_BASE_URL": "https://ejemplo.invalid"})
    assert not [k for k in env if k.startswith("LANGFUSE_")]


def test_la_telemetria_de_claude_code_queda_apagada_en_la_delegacion(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_ENABLE_TELEMETRY", "1")
    env = _entorno_de(monkeypatch)
    assert "CLAUDE_CODE_ENABLE_TELEMETRY" not in env


def test_limpiar_el_entorno_deja_pasar_lo_que_leen_los_hooks(monkeypatch):
    """Los hooks dependen de las `HARNESS_*` (`F-61`, `1ad5691`)."""
    monkeypatch.setenv("HARNESS_REGISTRO_HOOKS", "registro.jsonl")
    env = _entorno_de(monkeypatch, reglas="reglas.json", entorno={"HARNESS_DB": "obra.db"})
    assert env["HARNESS_AGENTE"] == "escritor" and env["HARNESS_REGLAS"] == "reglas.json"
    assert env["HARNESS_DB"] == "obra.db" and env["HARNESS_REGISTRO_HOOKS"] == "registro.jsonl"


def test_settings_no_enciende_la_telemetria():
    """`SPEC-29` `RF-11`: la exportacion OTEL propia de Claude Code queda apagada."""
    ajustes = _json.loads((proveedor.RAIZ_DEL_REPOSITORIO / ".claude" / "settings.json")
                          .read_text(encoding="utf-8"))
    variables = ajustes.get("env") or {}
    assert "CLAUDE_CODE_ENABLE_TELEMETRY" not in variables
    assert not [k for k in variables if k.startswith("OTEL_")]
