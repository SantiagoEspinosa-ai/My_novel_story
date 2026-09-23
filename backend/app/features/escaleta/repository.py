"""Persistencia de la escaleta, los borradores y los hallazgos.

`Borrador.version` crece **por escena y no globalmente**: la version 3 de la
escena 7 no tiene nada que ver con la version 3 de la escena 2, y numerarlas en
comun haria imposible leer "esta escena necesito cuatro intentos", que es una
de las señales que la otra rama identifico como mas utiles al interpretar un
informe.

`Escena.intentos` no se guarda aparte: es el numero de borradores. Un contador
que se lleva al lado de lo que cuenta se desincroniza en cuanto un camino de
codigo olvida incrementarlo.
"""

import json
import sqlite3

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH

SQL = """
CREATE TABLE IF NOT EXISTS escena (
    id                 TEXT PRIMARY KEY,
    obra               TEXT NOT NULL,
    orden              INTEGER NOT NULL,
    estado             TEXT NOT NULL,
    cambio_de_valor    TEXT NOT NULL,
    beats              TEXT NOT NULL,
    longitud_objetivo  TEXT,
    borrador_aceptado  INTEGER
);
CREATE TABLE IF NOT EXISTS borrador (
    escena      TEXT NOT NULL,
    version     INTEGER NOT NULL,
    texto       TEXT NOT NULL,
    modelo      TEXT,
    prompt_hash TEXT,
    PRIMARY KEY (escena, version)
);
CREATE TABLE IF NOT EXISTS hallazgo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invariante  TEXT NOT NULL,
    verificador TEXT NOT NULL,
    escena      TEXT NOT NULL,
    severidad   TEXT NOT NULL,
    estado      TEXT NOT NULL,
    descripcion TEXT NOT NULL
);
"""

CUENTAN_COMO_ABIERTOS = (EH.ABIERTO.value, EH.SIN_VEREDICTO.value)


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar_escaleta(con, obra, escenas):
    asegurar_tablas(con)
    with con:
        for e in escenas:
            con.execute(
                "INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, "
                "beats, longitud_objetivo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (e["id"], obra, e["orden"], EE.PLANIFICADA.value,
                 json.dumps(e["cambio_de_valor"]), json.dumps(e["beats"]),
                 json.dumps(e.get("longitud_objetivo"))),
            )


def escenas_de(con, obra):
    filas = con.execute(
        "SELECT id, orden, estado, cambio_de_valor, beats, longitud_objetivo, "
        "borrador_aceptado FROM escena WHERE obra = ? ORDER BY orden", (obra,))
    return [{"id": f[0], "orden": f[1], "estado": f[2],
             "cambio_de_valor": json.loads(f[3]), "beats": json.loads(f[4]),
             "longitud_objetivo": json.loads(f[5]) if f[5] else None,
             "borrador_aceptado": f[6]} for f in filas]


def escena(con, id_escena):
    for e in con.execute(
            "SELECT id, orden, estado, cambio_de_valor, beats, longitud_objetivo, "
            "borrador_aceptado FROM escena WHERE id = ?", (id_escena,)):
        return {"id": e[0], "orden": e[1], "estado": e[2],
                "cambio_de_valor": json.loads(e[3]), "beats": json.loads(e[4]),
                "longitud_objetivo": json.loads(e[5]) if e[5] else None,
                "borrador_aceptado": e[6]}
    return None


def guardar_borrador(con, escena, texto, modelo, prompt_hash):
    """Devuelve la version, que crece por escena."""
    with con:
        fila = con.execute("SELECT MAX(version) FROM borrador WHERE escena = ?",
                           (escena,)).fetchone()
        version = (fila[0] or 0) + 1
        con.execute("INSERT INTO borrador VALUES (?, ?, ?, ?, ?)",
                    (escena, version, texto, modelo, prompt_hash))
        con.execute("UPDATE escena SET estado = ? WHERE id = ?",
                    (EE.GENERADA.value, escena))
    return version


def intentos_de(con, escena):
    """No hay contador aparte: es cuantos borradores hay."""
    return con.execute("SELECT COUNT(*) FROM borrador WHERE escena = ?",
                       (escena,)).fetchone()[0]


def guardar_hallazgo(con, invariante, verificador, escena, severidad, estado, descripcion):
    with con:
        con.execute(
            "INSERT INTO hallazgo (invariante, verificador, escena, severidad, "
            "estado, descripcion) VALUES (?, ?, ?, ?, ?, ?)",
            (invariante, verificador, escena, str(severidad), str(estado), descripcion))


def hallazgos_abiertos(con, escena):
    filas = con.execute(
        "SELECT invariante, verificador, severidad, estado, descripcion FROM hallazgo "
        "WHERE escena = ? AND estado IN (?, ?)",
        (escena, CUENTAN_COMO_ABIERTOS[0], CUENTAN_COMO_ABIERTOS[1]))
    return [{"invariante": f[0], "verificador": f[1], "severidad": f[2],
             "estado": f[3], "descripcion": f[4]} for f in filas]


def aceptar_borrador(con, escena, version, rindiendose):
    estado = EE.ACEPTADA_POR_RENDICION if rindiendose else EE.ACEPTADA
    with con:
        con.execute("UPDATE escena SET estado = ?, borrador_aceptado = ? WHERE id = ?",
                    (estado.value, version, escena))
