"""Las palabras vetadas en tres niveles (`SPEC-25`).

`franja` y `obra` son cadena vacia y no `NULL` cuando no aplican: en SQLite dos
`NULL` nunca son iguales, asi que `UNIQUE (forma, nivel, franja, obra)` dejaria
entrar la misma palabra global cada vez que se cargara la lista, y la carga
dejaria de ser idempotente sin que nada fallara.
"""

import sqlite3
from dataclasses import dataclass

from app.commons.dominio.enumeraciones import NivelDeVeto as NV
from app.commons.politica import auditoria
from app.commons.politica.vetadas import formas_de_nombre

SQL = """
CREATE TABLE IF NOT EXISTS palabra_vetada (
    forma  TEXT NOT NULL,
    nivel  TEXT NOT NULL,
    franja TEXT NOT NULL DEFAULT '',
    obra   TEXT NOT NULL DEFAULT '',
    UNIQUE (forma, nivel, franja, obra)
);
"""


@dataclass(frozen=True)
class Vetada:
    forma: str
    nivel: NV
    # `SPEC-29` `RF-06`: el `rowid`. Una vetada que no es global sube a Langfuse por
    # este id y su nivel, nunca por su forma: puede ser el nombre de una persona.
    id: int | None = None


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)
    auditoria.asegurar_tabla(con)


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


def vetar_en_novela(con, obra, palabras=(), nombres=()):
    """El nivel por novela.

    Las palabras y expresiones se vetan tal cual; los nombres propios, ademas,
    por su nombre de pila (`RF-15`). Van separados porque partir una expresion
    como si fuera un nombre vetaria su primera palabra: «tema de familia»
    acabaria vetando «tema» en toda la novela.
    """
    with con:
        for palabra in palabras:
            _insertar(con, palabra, NV.NOVELA, obra=obra)
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
        "SELECT forma, nivel, rowid FROM palabra_vetada "
        "WHERE nivel = ? OR (nivel = ? AND franja = ?) OR (nivel = ? AND obra = ?) "
        "ORDER BY rowid",
        (str(NV.GLOBAL), str(NV.FRANJA_DE_EDAD), franja or "", str(NV.NOVELA),
         obra)).fetchall()
    return [Vetada(f[0], NV(f[1]), f[2]) for f in filas]

