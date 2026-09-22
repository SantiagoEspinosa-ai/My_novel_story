"""Acceso a datos del alta de obra. Es el unico que ve SQL.

`A-01`: cada feature tiene los mismos ficheros y `repository.py` es el unico
que habla con la base. El servicio no sabe que hay SQLite debajo, y por eso se
puede probar sin base.
"""

import json
import sqlite3
import uuid

MIGRACION_SQL = """
CREATE TABLE IF NOT EXISTS obra (
    id                 TEXT PRIMARY KEY,
    titulo             TEXT NOT NULL,
    premisa            TEXT NOT NULL,
    genero             TEXT,
    subgenero          TEXT,
    extension_objetivo INTEGER,
    guia_de_estilo     TEXT
);
CREATE TABLE IF NOT EXISTS capitulo (
    id     TEXT PRIMARY KEY,
    obra   TEXT NOT NULL REFERENCES obra(id),
    orden  INTEGER NOT NULL,
    estado TEXT NOT NULL DEFAULT 'abierto',
    UNIQUE (obra, orden)
);
"""


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(MIGRACION_SQL)


def crear(con, datos: dict) -> str:
    asegurar_tablas(con)
    id_obra = str(uuid.uuid4())
    guia = {k: datos.get(k) for k in ("persona", "tiempo_verbal")}
    with con:
        con.execute(
            "INSERT INTO obra (id, titulo, premisa, genero, subgenero, "
            "extension_objetivo, guia_de_estilo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_obra, datos["titulo"], datos["premisa"], datos.get("genero"),
             datos.get("subgenero"), datos.get("extension_objetivo"),
             json.dumps(guia)),
        )
    return id_obra


def leer(con, id_obra: str):
    asegurar_tablas(con)
    fila = con.execute(
        "SELECT id, titulo, premisa, genero FROM obra WHERE id = ?", (id_obra,)
    ).fetchone()
    if fila is None:
        return None
    capitulos = [r[0] for r in con.execute(
        "SELECT id FROM capitulo WHERE obra = ? ORDER BY orden", (id_obra,)
    )]
    return {"id": fila[0], "titulo": fila[1], "premisa": fila[2],
            "genero": fila[3], "capitulos": capitulos}
