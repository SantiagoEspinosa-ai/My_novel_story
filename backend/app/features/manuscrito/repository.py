"""El SQL del manuscrito que no es el texto (`PLAN-27` E6). Como `exportar.py`, lee
tablas y no importa ninguna feature."""

import json
import sqlite3

from app.commons.obra import vigente as obra_vigente


def ultimo_veredicto(con, obra):
    """El ultimo veredicto de la puerta de publicacion (`SPEC-30`) **de la version que se
    exporta**, que es la vigente (`PLAN-23` `F-121`), o `None` si la puerta no ha corrido
    nunca sobre ella. Las rondas son por version (`F-122`): mezclarlas compararia la ronda
    1 de una con la 3 de otra."""
    numero = obra_vigente.version_vigente(con, obra)
    filtro, args = ("AND version = ?", (obra, numero)) if numero is not None else ("", (obra,))
    try:
        f = con.execute("SELECT ronda, publica, condiciones, codigo_lean "
                        "FROM veredicto_de_publicacion WHERE obra = ? {0} "
                        "ORDER BY version DESC, ronda DESC LIMIT 1".format(filtro),
                        args).fetchone()
    except sqlite3.OperationalError:
        return None
    if f is None:
        return None
    return {"ronda": f[0], "publica": bool(f[1]), "condiciones": json.loads(f[2]),
            "codigo_lean": f[3]}
