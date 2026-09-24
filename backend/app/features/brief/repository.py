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
    guia_de_estilo     TEXT,
    dedicatoria        TEXT
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


class CapituloDeOtraObra(Exception):
    """`F-64`: un capitulo con el identificador de otro de otra obra.

    `capitulo` tiene clave global, y antes se escribia con `INSERT OR REPLACE`: la
    segunda obra se quedaba los capitulos de la primera y no fallaba nada. Ahora
    falla antes de escribir. El camino normal no llega aqui, porque el plan acota
    sus identificadores a la obra (`planificacion.ids`); esto es para el que entra
    por otro sitio.
    """


def alta_de_obra(con, id_obra, datos, capitulos):
    """Da de alta una obra **con sus capitulos y su orden**, en un solo sitio.

    POR QUE ESTO NO PUEDE ESTAR EN DOS SITIOS
    -------------------------------------------
    La forma de la obra vive en el brief, y darla de alta desde dos sitios -el
    guion con sus `INSERT` a mano por un lado, el alta de la API por otro- es
    exactamente como vuelven a divergir: el dia que una de las dos aprenda algo,
    la otra no. Es la misma leccion de `F-56`, donde la forma de la obra vivia
    dentro del guion y por eso nadie pudo discutirla en diez capitulos.

    `crear()` sigue existiendo para el alta por API, que genera identificador y
    todavia no recibe capitulos. Esta recibe el identificador ya decidido,
    porque quien repite una tanda necesita que la obra se llame igual que la vez
    anterior para poder comparar las dos.

    **El orden de los capitulos no es decorativo**: es lo que
    `escaleta.asignar_t_discurso` necesita para numerar el orden de lectura de la
    obra entera. Sin el, sus escenas se quedan sin situar y lo dice.

    Es idempotente: el guion la llama en cada arranque, y repetir un arranque no
    puede dejar la obra con el doble de capitulos.
    """
    asegurar_tablas(con)
    ajenos = [(c, f[0]) for c in capitulos for f in con.execute(
        "SELECT obra FROM capitulo WHERE id = ? AND obra <> ?", (c, id_obra))]
    if ajenos:
        raise CapituloDeOtraObra(
            "estos capitulos ya son de otra obra y no se pisan: {0}".format(
                ", ".join("{0} (de {1})".format(c, o) for c, o in ajenos)))
    guia = {k: datos.get(k) for k in ("persona", "tiempo_verbal")}
    with con:
        con.execute(
            "INSERT OR REPLACE INTO obra (id, titulo, premisa, genero, "
            "subgenero, extension_objetivo, guia_de_estilo, dedicatoria) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (id_obra, datos["titulo"], datos["premisa"], datos.get("genero"),
             datos.get("subgenero"), datos.get("extension_objetivo"),
             json.dumps(guia), datos.get("dedicatoria")))
        for posicion, id_capitulo in enumerate(capitulos, start=1):
            con.execute(
                "INSERT OR REPLACE INTO capitulo (id, obra, orden, estado) "
                "VALUES (?, ?, ?, 'abierto')", (id_capitulo, id_obra, posicion))
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
