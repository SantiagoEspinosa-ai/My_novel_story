"""Las palabras vetadas en tres niveles y el audit log (`SPEC-25`).

`franja` y `obra` son cadena vacia y no `NULL` cuando no aplican: en SQLite dos
`NULL` nunca son iguales, asi que `UNIQUE (forma, nivel, franja, obra)` dejaria
entrar la misma palabra global cada vez que se cargara la lista, y la carga
dejaria de ser idempotente sin que nada fallara.
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from app.commons.dominio.enumeraciones import NivelDeVeto as NV
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica
from app.features.politica.vetadas import formas_de_nombre

SQL = """
CREATE TABLE IF NOT EXISTS palabra_vetada (
    forma  TEXT NOT NULL,
    nivel  TEXT NOT NULL,
    franja TEXT NOT NULL DEFAULT '',
    obra   TEXT NOT NULL DEFAULT '',
    UNIQUE (forma, nivel, franja, obra)
);
CREATE TABLE IF NOT EXISTS decision_de_politica (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo    TEXT NOT NULL,
    momento TEXT NOT NULL,
    obra    TEXT,
    detalle TEXT NOT NULL DEFAULT '{}'
);
"""


@dataclass(frozen=True)
class Vetada:
    forma: str
    nivel: NV


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def _insertar(con, forma, nivel, franja="", obra=""):
    con.execute("INSERT OR IGNORE INTO palabra_vetada (forma, nivel, franja, obra) "
                "VALUES (?, ?, ?, ?)", (forma, str(nivel), franja, obra))


def cargar_listas(con, listas):
    """Los niveles global y por franja. Idempotente.

    Acepta el `ListasVetadas` validado o un diccionario con la misma forma.
    """
    if hasattr(listas, "global_"):
        globales, franjas = listas.global_, listas.franjas
    else:
        globales, franjas = listas["global"], listas.get("franjas", {})
    with con:
        for forma in globales:
            _insertar(con, forma, NV.GLOBAL)
        for franja, formas in franjas.items():
            for forma in formas:
                _insertar(con, forma, NV.FRANJA_DE_EDAD, franja=franja)


def vetar_en_novela(con, obra, nombres):
    """El nivel por novela. Cada entrada se veta en todas sus formas (`RF-15`)."""
    with con:
        for nombre in nombres:
            for forma in formas_de_nombre(nombre):
                _insertar(con, forma, NV.NOVELA, obra=obra)


def franja_de(edad, franjas):
    for f in franjas:
        if f.desde <= edad <= f.hasta:
            return f.nombre
    return None


def vetadas_para(con, obra, edad, franjas) -> list:
    """Lo que no puede aparecer en esta obra: global, su franja y la novela."""
    franja = franja_de(edad, franjas) if edad is not None else None
    filas = con.execute(
        "SELECT forma, nivel FROM palabra_vetada "
        "WHERE nivel = ? OR (nivel = ? AND franja = ?) OR (nivel = ? AND obra = ?) "
        "ORDER BY rowid",
        (str(NV.GLOBAL), str(NV.FRANJA_DE_EDAD), franja or "", str(NV.NOVELA),
         obra)).fetchall()
    return [Vetada(f[0], NV(f[1])) for f in filas]


def registrar_decision(con, tipo, obra, detalle=None, dentro_de_transaccion=False):
    """Una fila del audit log (`RF-20`). Nunca se actualiza ni se borra."""
    def _escribir():
        con.execute(
            "INSERT INTO decision_de_politica (tipo, momento, obra, detalle) "
            "VALUES (?, ?, ?, ?)",
            (str(TipoDeDecisionDePolitica(tipo)),
             datetime.now(timezone.utc).isoformat(), obra,
             json.dumps(detalle or {}, ensure_ascii=False)))

    if dentro_de_transaccion:
        _escribir()
    else:
        with con:
            _escribir()


def decisiones(con, obra=None) -> list:
    sql = "SELECT tipo, momento, obra, detalle FROM decision_de_politica"
    args = ()
    if obra is not None:
        sql += " WHERE obra = ?"
        args = (obra,)
    filas = con.execute(sql + " ORDER BY id", args).fetchall()
    return [{"tipo": TipoDeDecisionDePolitica(f[0]), "momento": f[1],
             "obra": f[2], "detalle": json.loads(f[3])} for f in filas]
