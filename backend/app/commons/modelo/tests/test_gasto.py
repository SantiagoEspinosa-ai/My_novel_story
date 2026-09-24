"""`SPEC-33` `RF-18`, `RF-19`, `PLAN-33` E4: `GastoDeDelegacion` en la base.

Vive en `commons/` porque lo escriben la entrevista y la orquestacion, y una feature no
importa de otra (`docs/architecture.md`). Un coste que no se midio se guarda `NULL`:
un cero se leeria como un dato y un hueco no.
"""

import sqlite3

from app.commons.db import migraciones
from app.commons.modelo import gasto


def _base():
    con = sqlite3.connect(":memory:")
    migraciones.migrar(con)
    return con


def test_el_anotador_guarda_una_fila_por_delegacion():
    con = _base()
    anotar = gasto.anotador(con, obra="obra-a", generacion="gen-1")
    anotar("escritor", 0.25)
    anotar("editor", 0.5)
    filas = con.execute("SELECT obra, agente, generacion, coste_usd FROM gasto_de_delegacion "
                        "ORDER BY id").fetchall()
    assert filas == [("obra-a", "escritor", "gen-1", 0.25), ("obra-a", "editor", "gen-1", 0.5)]


def test_un_coste_ausente_se_guarda_nulo_y_no_cero():
    con = _base()
    gasto.anotador(con, obra="obra-a")("entrevistador", None)
    assert con.execute("SELECT coste_usd, generacion FROM gasto_de_delegacion").fetchone() == \
        (None, None)


def test_cada_fila_dice_cuando():
    con = _base()
    gasto.anotador(con, obra="obra-a")("escritor", 0.1)
    assert con.execute("SELECT cuando FROM gasto_de_delegacion").fetchone()[0]


def test_la_tabla_nace_en_una_migracion():
    """`VER-21`: `esquema_version` tiene que decir cuando aparecio."""
    con = _base()
    assert migraciones.tiene_tabla(con, "gasto_de_delegacion")
