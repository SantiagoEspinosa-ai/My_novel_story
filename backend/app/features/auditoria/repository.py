"""`veredicto_de_publicacion`: una fila por ronda de la puerta (`SPEC-30`).

Es lo que lee la exportacion a PDF para saber si una version esta publicada
(`SPEC-27` `RF-01`, `PLAN-27` E6), y lo que cuenta las rondas para que relanzar no
reinicie el tope (la leccion de `CE-4`: un checkpoint guarda la decision, no solo el
contador). Por eso vive en la base y no en la memoria de un proceso.
"""

import json
import sqlite3

from app.commons.db.migraciones import VEREDICTO_SQL

# `PLAN-23` `F-122`: la clave es `(obra, version, ronda)`. Una sola copia, en
# `commons/db/migraciones.py`, porque la migracion 16 la necesita tambien.
MIGRACION_SQL = VEREDICTO_SQL


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(MIGRACION_SQL)


def rondas(con, obra, version=1) -> int:
    """Las rondas que **esta version** ha gastado (`F-122`, TLC `CE-15`): la version 2 no
    hereda las que la 1 gasto para publicarse."""
    asegurar_tablas(con)
    return con.execute("SELECT COUNT(*) FROM veredicto_de_publicacion "
                       "WHERE obra = ? AND version = ?", (obra, version)).fetchone()[0]


def guardar(con, obra, decision, codigo_lean, version=1) -> int:
    """Guarda la ronda siguiente de la version y devuelve su numero."""
    ronda = rondas(con, obra, version) + 1
    with con:
        con.execute(
            "INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
            "condiciones, codigo_lean, no_ejecutadas) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (obra, version, ronda, int(decision.publica),
             json.dumps([c.__dict__ for c in decision.condiciones], ensure_ascii=False),
             codigo_lean,
             json.dumps([n.__dict__ for n in decision.no_ejecutadas], ensure_ascii=False)))
    return ronda


def ultimo(con, obra, version=None):
    """El ultimo veredicto de la version, o de la obra entera -la version mas alta que
    haya pasado por la puerta- si no se dice cual."""
    asegurar_tablas(con)
    filtro, args = ("AND version = ?", (obra, version)) if version is not None else ("", (obra,))
    f = con.execute("SELECT ronda, publica, condiciones, codigo_lean, no_ejecutadas, version "
                    "FROM veredicto_de_publicacion WHERE obra = ? {0} "
                    "ORDER BY version DESC, ronda DESC LIMIT 1".format(filtro), args).fetchone()
    if f is None:
        return None
    return {"ronda": f[0], "publica": bool(f[1]), "condiciones": json.loads(f[2]),
            "codigo_lean": f[3], "no_ejecutadas": json.loads(f[4]), "version": f[5]}
