"""Que tool puede llamar cada agente del pipeline (`SPEC-28` `RF-03`, `RF-07`).

Vive en `commons/` porque la leen tres sitios: el hook de policy, `proveedor` al armar la
orden y `orquestacion` al dar las tools. Solo el Escritor y el Editor tienen tools, y solo
las tres de lectura de la story bible; cualquier otra, de este servidor o de otro, se
niega. Una prueba comprueba que esta lista y el catalogo del servidor son la misma.
"""

SERVIDOR = "story_bible"

TOOLS_DE_LA_STORY_BIBLE = ("hechos", "ficha", "cronologia")

_DE_LA_STORY_BIBLE = tuple("mcp__{0}__{1}".format(SERVIDOR, t) for t in TOOLS_DE_LA_STORY_BIBLE)

PERMITIDAS = {"escritor": _DE_LA_STORY_BIBLE, "editor": _DE_LA_STORY_BIBLE}


def permitida(agente, herramienta) -> bool:
    return herramienta in PERMITIDAS.get(agente, ())
