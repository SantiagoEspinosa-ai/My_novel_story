"""Que tool puede llamar cada agente del pipeline (`SPEC-28` `RF-03`, `RF-07`).

Vive en `commons/` porque la leen tres sitios: el hook de policy, `proveedor` al armar la
orden y `orquestacion` al dar las tools. Solo el Escritor y el Editor tienen tools, y solo
las tres de lectura de la story bible; cualquier otra, de este servidor o de otro, se
niega. Una prueba comprueba que esta lista y el catalogo del servidor son la misma.
"""

SERVIDOR = "story_bible"

TOOLS_DE_LA_STORY_BIBLE = ("hechos", "ficha", "cronologia")

_DE_LA_STORY_BIBLE = tuple("mcp__{0}__{1}".format(SERVIDOR, t) for t in TOOLS_DE_LA_STORY_BIBLE)

# `PLAN-22` E13b: el `inspector_visual` tiene las del browser (Playwright MCP) y nada
# mas; ningun otro agente las tiene. Sin `browser_evaluate`: no ejecuta codigo en la pagina.
BROWSER = "playwright"
TOOLS_DEL_BROWSER = ("browser_navigate", "browser_navigate_back", "browser_snapshot",
                     "browser_click", "browser_take_screenshot", "browser_wait_for",
                     "browser_console_messages", "browser_resize")
_DEL_BROWSER = tuple("mcp__{0}__{1}".format(BROWSER, t) for t in TOOLS_DEL_BROWSER)

PERMITIDAS = {"escritor": _DE_LA_STORY_BIBLE, "editor": _DE_LA_STORY_BIBLE,
              "inspector_visual": _DEL_BROWSER}


def permitida(agente, herramienta) -> bool:
    return herramienta in PERMITIDAS.get(agente, ())
