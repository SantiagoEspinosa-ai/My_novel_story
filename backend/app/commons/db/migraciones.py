"""Migraciones versionadas de SQLite.

`CLAUDE.md`: "Las migraciones de esquema se versionan. Un cambio en
`Docs/definitions.md` que altere un atributo obligatorio necesita su migracion
en el mismo commit." `VER-21` comprueba la segunda mitad cruzando commits;
este modulo sostiene la primera.

POR QUE UNA TABLA DE VERSION Y NO `PRAGMA user_version`
-------------------------------------------------------
`user_version` es un entero suelto: dice en que version esta la base y no dice
cuando se aplico ninguna. Una tabla cuesta lo mismo y deja rastro, y aqui el
rastro importa: una base que no sabe cuando se migro no se puede reconciliar
con el historial de commits que `VER-21` recorre.

POR QUE LAS VERSIONES NO PUEDEN TENER HUECOS
---------------------------------------------
Un hueco significa que alguien borro una migracion ya publicada. Las bases que
la aplicaron y las que no dejan de ser distinguibles, y a partir de ahi el
numero de version miente. Es la misma regla que gobierna los identificadores
del proyecto: lo que se publica no se borra ni se renumera.
"""

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Migracion:
    version: int
    descripcion: str
    sql: str


# Ninguna clase del dominio tiene todavia tabla: llegan con la feature que las
# usa. Lo que existe desde el primer dia es el registro de versiones, porque
# sin el no se puede aplicar la segunda.
TODAS = [
    Migracion(
        1,
        "registro de versiones de esquema",
        """
        CREATE TABLE IF NOT EXISTS esquema_version (
            version     INTEGER PRIMARY KEY,
            descripcion TEXT    NOT NULL,
            aplicada_en TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        """,
    ),
    Migracion(
        2,
        "el conocimiento anterior al relato no tiene escena de origen",
        # `SPEC-17` C-2. La tabla la crea `features/consolidacion/` con
        # `CREATE TABLE IF NOT EXISTS`, asi que una base nueva ya nace bien;
        # esta migracion existe para las que ya tenian la version con
        # `desde_escena NOT NULL`. SQLite no sabe quitar un `NOT NULL` con
        # `ALTER`, asi que se recrea la tabla y se copia, que es el camino que
        # su propia documentacion recomienda.
        """
        CREATE TABLE IF NOT EXISTS conocimiento (
            sujeto       TEXT NOT NULL,
            hecho        TEXT NOT NULL,
            desde_escena TEXT NOT NULL,
            grado        TEXT NOT NULL DEFAULT 'sabe',
            fuente       TEXT,
            PRIMARY KEY (sujeto, hecho)
        );
        CREATE TABLE conocimiento_nuevo (
            sujeto       TEXT NOT NULL,
            hecho        TEXT NOT NULL,
            desde_escena TEXT,
            grado        TEXT NOT NULL DEFAULT 'sabe',
            fuente       TEXT,
            PRIMARY KEY (sujeto, hecho)
        );
        INSERT INTO conocimiento_nuevo SELECT * FROM conocimiento;
        DROP TABLE conocimiento;
        ALTER TABLE conocimiento_nuevo RENAME TO conocimiento;
        """,
    ),
]


def validar_secuencia(migraciones):
    """Las versiones son consecutivas desde 1 y no se repiten.

    Se comprueba en cada arranque y no solo en las pruebas: una migracion mal
    numerada que llega en un despliegue es peor que una que falla en CI.
    """
    vistas = set()
    for m in migraciones:
        if m.version in vistas:
            raise ValueError(
                "version {0} repetida: dos migraciones no pueden compartir "
                "numero, porque entonces la version aplicada no dice cual se "
                "aplico".format(m.version)
            )
        vistas.add(m.version)
    esperadas = set(range(1, len(migraciones) + 1))
    if vistas != esperadas:
        raise ValueError(
            "hueco en la secuencia de migraciones: se esperaba {0} y hay {1}. "
            "Un hueco significa que se borro una migracion publicada".format(
                sorted(esperadas), sorted(vistas)
            )
        )
    return True


validar_secuencia(TODAS)
ULTIMA_VERSION = max(m.version for m in TODAS)


def version_aplicada(con: sqlite3.Connection) -> int:
    """0 si la base es nueva. No crea nada: preguntar no es migrar."""
    fila = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='esquema_version'"
    ).fetchone()
    if fila is None:
        return 0
    fila = con.execute("SELECT MAX(version) FROM esquema_version").fetchone()
    return fila[0] or 0


def migrar(con: sqlite3.Connection) -> int:
    """Aplica lo que falte y devuelve cuantas migraciones se aplicaron.

    Cada migracion va **en su propia transaccion**: si la tercera falla, la
    primera y la segunda siguen aplicadas y la version lo refleja. Lo contrario
    -una transaccion para todas- dejaria la base en un estado que la version no
    describe, que es el mismo problema del delta a medias de `SPEC-07`.
    """
    validar_secuencia(TODAS)
    desde = version_aplicada(con)
    aplicadas = 0
    for m in sorted(TODAS, key=lambda x: x.version):
        if m.version <= desde:
            continue
        with con:
            con.executescript(m.sql)
            con.execute(
                "INSERT INTO esquema_version (version, descripcion) VALUES (?, ?)",
                (m.version, m.descripcion),
            )
        aplicadas += 1
    return aplicadas
