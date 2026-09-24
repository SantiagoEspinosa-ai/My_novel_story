"""`PLAN-22` E12 (`VER-108`): un solo browser MCP en la configuracion del repositorio, y
ninguna delegacion del pipeline lo usa.

`.mcp.json` es para la sesion de Claude Code que inspecciona la web (E13), no para los
agentes. Toda delegacion lleva `--strict-mcp-config` (DP-6) y el hook de policy niega las
tools del browser a cualquier agente del pipeline.
"""

import json
import pathlib

from app.commons.politica.herramientas import permitida

RAIZ = pathlib.Path(__file__).resolve().parents[5]
AGENTES = sorted(p.stem for p in (RAIZ / ".claude" / "agents").glob("*.md"))
DEL_BROWSER = ("mcp__playwright__browser_navigate", "mcp__playwright__browser_snapshot",
               "mcp__playwright__browser_click", "mcp__playwright__browser_take_screenshot")


def test_el_mcp_json_declara_un_solo_servidor_y_es_el_del_browser():
    datos = json.loads((RAIZ / ".mcp.json").read_text(encoding="utf-8"))
    servidores = datos["mcpServers"]
    assert list(servidores) == ["playwright"]
    orden = " ".join([servidores["playwright"]["command"]] + servidores["playwright"]["args"])
    assert "@playwright/mcp@" in orden, "la version va fijada, no la ultima"


def test_policy_niega_a_cualquier_agente_una_tool_del_browser():
    """A cualquiera **del pipeline**: desde `PLAN-22` E13b el `inspector_visual` es el
    unico que las tiene, y es un validador, no un agente que escriba."""
    assert AGENTES, "no se encontraron agentes en .claude/agents"
    for agente in (a for a in AGENTES if a != "inspector_visual"):
        for tool in DEL_BROWSER:
            assert not permitida(agente, tool), (agente, tool)


def test_el_inspector_solo_tiene_las_tools_del_browser():
    from app.commons.politica.herramientas import PERMITIDAS, TOOLS_DEL_BROWSER
    esperadas = tuple("mcp__playwright__{0}".format(t) for t in TOOLS_DEL_BROWSER)
    assert PERMITIDAS["inspector_visual"] == esperadas
    assert not permitida("inspector_visual", "mcp__story_bible__hechos")
    assert not permitida("inspector_visual", "Bash")
    # El frontmatter del agente declara exactamente esas.
    cabecera = (RAIZ / ".claude" / "agents" / "inspector_visual.md").read_text(
        encoding="utf-8").split("---")[1]
    linea = [x for x in cabecera.splitlines() if x.startswith("tools:")][0]
    assert tuple(x.strip() for x in linea[len("tools:"):].split(",")) == esperadas


def test_la_delegacion_del_inspector_carga_el_mcp_json_con_mcp_estricto(monkeypatch):
    import subprocess
    from app.commons.modelo import proveedor
    visto = {}

    def run(orden, **_):
        visto["orden"] = orden
        return subprocess.CompletedProcess(orden, 0, stdout="{}", stderr="")

    monkeypatch.setattr(proveedor.subprocess, "run", run)
    proveedor._ejecutar_proceso("claude", "m", "inspector_visual", "p",
                                mcp_fijo=str(RAIZ / ".mcp.json"))
    orden = visto["orden"]
    assert orden[orden.index("--mcp-config") + 1].endswith(".mcp.json")
    assert "--strict-mcp-config" in orden
    permitidas = orden[orden.index("--allowedTools") + 1].split(",")
    assert permitidas and all(x.startswith("mcp__playwright__") for x in permitidas)
