"""Las entrevistas y sus turnos en SQLite (`SPEC-25`).

Esto es lo que se borra al entregar (`RF-21`): la conversacion y la ficha. Las
vetadas de la novela y los hechos de la story bible viven en otras tablas y se
quedan.

`juicios`, `avisos_confirmados` y `vistas` son estado de la conversacion, no de
la ficha: la ficha es lo que se acuerda con el comprador, y esto es como se
llego. Por eso no estan en `FichaDeEntrevista` ni en `Docs/definitions.md`.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field

from app.commons.dominio.destinatario import FichaDeEntrevista

SQL = """
CREATE TABLE IF NOT EXISTS entrevista (
    id                 TEXT PRIMARY KEY,
    obra               TEXT NOT NULL,
    ficha              TEXT NOT NULL,
    cerrada            INTEGER NOT NULL DEFAULT 0,
    juicios            TEXT NOT NULL DEFAULT '[]',
    avisos_confirmados TEXT NOT NULL DEFAULT '[]',
    vistas             TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS turno_de_entrevista (
    entrevista TEXT NOT NULL REFERENCES entrevista(id),
    orden      INTEGER NOT NULL,
    respuesta  TEXT NOT NULL,
    pregunta   TEXT NOT NULL,
    PRIMARY KEY (entrevista, orden)
);
"""


@dataclass
class Entrevista:
    id: str
    obra: str
    ficha: FichaDeEntrevista
    cerrada: bool
    juicios: list = field(default_factory=list)
    avisos_confirmados: list = field(default_factory=list)
    vistas: dict = field(default_factory=dict)


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def crear(con, obra=None) -> Entrevista:
    e = Entrevista(id="ent-" + uuid.uuid4().hex[:10],
                   obra=obra or "obra-" + uuid.uuid4().hex[:10],
                   ficha=FichaDeEntrevista(), cerrada=False)
    with con:
        con.execute("INSERT INTO entrevista (id, obra, ficha) VALUES (?, ?, ?)",
                    (e.id, e.obra, e.ficha.model_dump_json()))
    return e


def leer(con, id_e) -> Entrevista | None:
    f = con.execute("SELECT id, obra, ficha, cerrada, juicios, avisos_confirmados, "
                    "vistas FROM entrevista WHERE id = ?", (id_e,)).fetchone()
    if f is None:
        return None
    return Entrevista(id=f[0], obra=f[1],
                      ficha=FichaDeEntrevista.model_validate_json(f[2]),
                      cerrada=bool(f[3]), juicios=json.loads(f[4]),
                      avisos_confirmados=json.loads(f[5]), vistas=json.loads(f[6]))


def guardar(con, e: Entrevista, respuesta=None, pregunta=None):
    """La entrevista y, si lo hay, su turno, en una sola transaccion: un turno
    guardado sin su ficha, o al reves, dejaria la conversacion diciendo algo
    que la ficha no refleja."""
    with con:
        con.execute("UPDATE entrevista SET ficha = ?, cerrada = ?, juicios = ?, "
                    "avisos_confirmados = ?, vistas = ? WHERE id = ?",
                    (e.ficha.model_dump_json(), int(e.cerrada),
                     json.dumps(e.juicios, ensure_ascii=False),
                     json.dumps(e.avisos_confirmados, ensure_ascii=False),
                     json.dumps(e.vistas, ensure_ascii=False), e.id))
        if respuesta is not None:
            orden = con.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM "
                                "turno_de_entrevista WHERE entrevista = ?",
                                (e.id,)).fetchone()[0]
            con.execute("INSERT INTO turno_de_entrevista (entrevista, orden, "
                        "respuesta, pregunta) VALUES (?, ?, ?, ?)",
                        (e.id, orden, respuesta, pregunta or ""))


def turnos(con, id_e) -> list:
    filas = con.execute("SELECT orden, respuesta, pregunta FROM turno_de_entrevista "
                        "WHERE entrevista = ? ORDER BY orden", (id_e,)).fetchall()
    return [{"orden": f[0], "respuesta": f[1], "pregunta": f[2]} for f in filas]


def de_la_obra(con, obra) -> list:
    return [f[0] for f in con.execute("SELECT id FROM entrevista WHERE obra = ?",
                                      (obra,)).fetchall()]


def borrar_de_la_obra(con, obra) -> dict:
    """`RF-21`: la conversacion, el texto libre y la ficha. Devuelve cuantas
    filas se borraron de cada tabla, nunca que contenian."""
    ids = de_la_obra(con, obra)
    with con:
        turnos_borrados = sum(
            con.execute("DELETE FROM turno_de_entrevista WHERE entrevista = ?",
                        (i,)).rowcount for i in ids)
        entrevistas = con.execute("DELETE FROM entrevista WHERE obra = ?",
                                  (obra,)).rowcount
    return {"entrevistas": entrevistas, "turnos": turnos_borrados}
