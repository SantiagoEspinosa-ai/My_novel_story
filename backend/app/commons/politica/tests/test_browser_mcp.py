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
    assert AGENTES, "no se encontraron agentes en .claude/agents"
    for agente in AGENTES:
        for tool in DEL_BROWSER:
            assert not permitida(agente, tool), (agente, tool)
