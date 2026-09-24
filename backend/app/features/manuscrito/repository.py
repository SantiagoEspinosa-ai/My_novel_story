"""El SQL del manuscrito que no es el texto (`PLAN-27` E6). Como `exportar.py`, lee
tablas y no importa ninguna feature."""

import json
import sqlite3


def ultimo_veredicto(con, obra):
    """El ultimo veredicto de la puerta de publicacion (`SPEC-30`), o `None` si la puerta
    no ha corrido nunca sobre la obra."""
    try:
        f = con.execute("SELECT ronda, publica, condiciones, codigo_lean "
                        "FROM veredicto_de_publicacion WHERE obra = ? "
                        "ORDER BY ronda DESC LIMIT 1", (obra,)).fetchone()
    except sqlite3.OperationalError:
        return None
    if f is None:
        return None
    return {"ronda": f[0], "publica": bool(f[1]), "condiciones": json.loads(f[2]),
            "codigo_lean": f[3]}
