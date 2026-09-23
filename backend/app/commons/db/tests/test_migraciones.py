"""A3 — Las migraciones se versionan, y eso se comprueba.

`CLAUDE.md` y `D-5` de `SPEC-01`:

    "Las migraciones de esquema se versionan. Un cambio en
     `Docs/definitions.md` que altere un atributo obligatorio necesita su
     migracion en el mismo commit."

La segunda mitad es la que `VER-21` comprueba y la que esta prueba sostiene:
sin version aplicada registrada, una base no sabe en que esquema esta y la
siguiente migracion se aplica sobre un supuesto.
"""

import sqlite3

import pytest

from app.commons.db import migraciones


def test_una_base_nueva_arranca_sin_version():
    con = sqlite3.connect(":memory:")
    assert migraciones.version_aplicada(con) == 0


def test_migrar_deja_la_base_en_la_ultima_version():
    con = sqlite3.connect(":memory:")
    migraciones.migrar(con)
    assert migraciones.version_aplicada(con) == migraciones.ULTIMA_VERSION
    assert migraciones.ULTIMA_VERSION >= 1


def test_migrar_dos_veces_no_hace_nada_la_segunda():
    """Reanudar una base ya migrada no puede romperla."""
    con = sqlite3.connect(":memory:")
    aplicadas = migraciones.migrar(con)
    assert aplicadas == migraciones.ULTIMA_VERSION
    assert migraciones.migrar(con) == 0


def test_las_versiones_son_consecutivas_y_sin_huecos():
    """Un hueco significa que alguien borro una migracion publicada."""
    versiones = sorted(m.version for m in migraciones.TODAS)
    assert versiones == list(range(1, migraciones.ULTIMA_VERSION + 1))


def test_caso_negativo_una_migracion_con_version_repetida():
    """El caso negativo de `VER-21`: dos migraciones no pueden compartir numero."""
    with pytest.raises(ValueError, match="repetida"):
        migraciones.validar_secuencia(
            [
                migraciones.Migracion(1, "crea algo", "SELECT 1"),
                migraciones.Migracion(1, "crea otra cosa", "SELECT 1"),
            ]
        )


def test_caso_negativo_un_hueco_en_la_secuencia():
    with pytest.raises(ValueError, match="hueco"):
        migraciones.validar_secuencia(
            [
                migraciones.Migracion(1, "crea algo", "SELECT 1"),
                migraciones.Migracion(3, "crea otra cosa", "SELECT 1"),
            ]
        )


def test_la_migracion_2_permite_conocimiento_anterior_al_relato():
    """`SPEC-17` C-2: `desde_escena` pierde su `NOT NULL`, porque lo que se sabe
    desde antes de la escena 1 no tiene escena de origen. Es la primera
    migracion del proyecto que no es gratis."""
    con = sqlite3.connect(":memory:")
    migraciones.migrar(con)
    assert migraciones.version_aplicada(con) >= 2
    con.execute("INSERT INTO conocimiento (sujeto, hecho, desde_escena, grado, "
                "fuente) VALUES ('per-ana', 'hec-1', NULL, 'sabe', "
                "'anterior_al_relato')")
    assert con.execute("SELECT desde_escena FROM conocimiento").fetchone()[0] is None
