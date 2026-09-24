"""`veredicto_de_publicacion`: una fila por ronda de la puerta (`SPEC-30`).

Es lo que lee la exportacion a PDF para saber si una version esta publicada
(`SPEC-27` `RF-01`, `PLAN-27` E6), y lo que cuenta las rondas para que relanzar no
reinicie el tope (la leccion de `CE-4`: un checkpoint guarda la decision, no solo el
contador). Por eso vive en la base y no en la memoria de un proceso.
"""

import json
import sqlite3

MIGRACION_SQL = """
CREATE TABLE IF NOT EXISTS veredicto_de_publicacion (
    obra          TEXT NOT NULL,
    ronda         INTEGER NOT NULL,
    publica       INTEGER NOT NULL,
    condiciones   TEXT NOT NULL,
    codigo_lean   INTEGER,
    no_ejecutadas TEXT NOT NULL,
    cuando        TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (obra, ronda)
);
"""


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(MIGRACION_SQL)


def rondas(con, obra) -> int:
    asegurar_tablas(con)
    return con.execute("SELECT COUNT(*) FROM veredicto_de_publicacion WHERE obra = ?",
                       (obra,)).fetchone()[0]


def guardar(con, obra, decision, codigo_lean) -> int:
    """Guarda la ronda siguiente y devuelve su numero."""
    ronda = rondas(con, obra) + 1
    with con:
        con.execute(
            "INSERT INTO veredicto_de_publicacion (obra, ronda, publica, condiciones, "
            "codigo_lean, no_ejecutadas) VALUES (?, ?, ?, ?, ?, ?)",
            (obra, ronda, int(decision.publica),
             json.dumps([c.__dict__ for c in decision.condiciones], ensure_ascii=False),
             codigo_lean,
             json.dumps([n.__dict__ for n in decision.no_ejecutadas], ensure_ascii=False)))
    return ronda


def ultimo(con, obra):
    asegurar_tablas(con)
    f = con.execute("SELECT ronda, publica, condiciones, codigo_lean, no_ejecutadas "
                    "FROM veredicto_de_publicacion WHERE obra = ? ORDER BY ronda DESC "
                    "LIMIT 1", (obra,)).fetchone()
    if f is None:
        return None
    return {"ronda": f[0], "publica": bool(f[1]), "condiciones": json.loads(f[2]),
            "codigo_lean": f[3], "no_ejecutadas": json.loads(f[4])}
