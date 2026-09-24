"""Acceso a datos del alta de obra. Es el unico que ve SQL.

`A-01`: cada feature tiene los mismos ficheros y `repository.py` es el unico
que habla con la base. El servicio no sabe que hay SQLite debajo, y por eso se
puede probar sin base.
"""

import functools
import json
import sqlite3
import uuid

from app.commons.db import procedencia
from app.commons.db.migraciones import VERSIONES_SQL
from app.commons.obra import vigente as obra_vigente

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
    estado TEXT NOT NULL DEFAULT 'abierto'
);
"""
# Sin `UNIQUE (obra, orden)` (`PLAN-23` hallazgo 4): el orden de un capitulo en una
# version lo dice `capitulo_de_version`, y un capitulo nuevo en la posicion 3 de la
# version 2 no puede borrar al capitulo 3 de la version 1 (Regla 7).


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(MIGRACION_SQL)
        con.executescript(VERSIONES_SQL)


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
        # `PLAN-23` A3: la obra nace con su version 1. Relanzar el alta no crea otra.
        if not _hay_version(con, id_obra):
            _insertar_version(con, id_obra, 1, capitulos, None, None, _commit_del_proceso())
    return id_obra


# --- Versiones de la obra (`SPEC-23` `D-2`, `PLAN-23` A3) ------------------------

@functools.lru_cache(maxsize=1)
def _commit_del_proceso():
    """El commit con el que corre este proceso. Una vez: el codigo que se cargo al
    arrancar no cambia aunque el arbol si, y es el que escribe (`MF-27`)."""
    return procedencia.version_del_arbol()


def _hay_version(con, obra):
    return con.execute("SELECT 1 FROM version_de_obra WHERE obra = ?",
                       (obra,)).fetchone() is not None


def _insertar_version(con, obra, numero, capitulos, anterior, peticion, commit):
    con.execute('INSERT INTO version_de_obra (obra, numero, anterior, peticion, "commit") '
                "VALUES (?, ?, ?, ?, ?)", (obra, numero, anterior, peticion, commit))
    for orden, capitulo in enumerate(capitulos, start=1):
        con.execute("INSERT INTO capitulo_de_version (obra, numero, orden, capitulo) "
                    "VALUES (?, ?, ?, ?)", (obra, numero, orden, capitulo))


def crear_version(con, obra, capitulos, anterior=None, peticion=None, commit=None):
    """Una version nueva con `capitulos` en orden. Devuelve su numero.

    Un capitulo que ya existe **se comparte por referencia**: es la misma fila. Uno
    que no existe se crea, con su posicion como `orden` y `abierto`. Nada de la
    version anterior se toca, y la base lo hace cumplir con sus disparadores.
    """
    asegurar_tablas(con)
    ajenos = [(c, f[0]) for c in capitulos for f in con.execute(
        "SELECT obra FROM capitulo WHERE id = ? AND obra <> ?", (c, obra))]
    if ajenos:
        raise CapituloDeOtraObra(
            "estos capitulos ya son de otra obra y no se comparten: {0}".format(
                ", ".join("{0} (de {1})".format(c, o) for c, o in ajenos)))
    with con:
        fila = con.execute("SELECT MAX(numero) FROM version_de_obra WHERE obra = ?",
                           (obra,)).fetchone()
        numero = (fila[0] or 0) + 1
        for posicion, capitulo in enumerate(capitulos, start=1):
            con.execute("INSERT OR IGNORE INTO capitulo (id, obra, orden, estado) "
                        "VALUES (?, ?, ?, 'abierto')", (capitulo, obra, posicion))
        _insertar_version(con, obra, numero, capitulos, anterior, peticion,
                          commit or _commit_del_proceso())
    return numero


def _leer(con, sql, args):
    """Leer no crea tablas: las lecturas de versiones tienen que valer en una conexion
    de solo lectura (la de la story bible, `SPEC-28` `RF-04`). Sin tabla, no hay filas."""
    try:
        return con.execute(sql, args).fetchall()
    except sqlite3.OperationalError:
        return []


def versiones_de(con, obra):
    return [{"numero": f[0], "anterior": f[1], "peticion": f[2], "commit": f[3],
             "creada_en": f[4]}
            for f in _leer(con, 'SELECT numero, anterior, peticion, "commit", creada_en '
                                "FROM version_de_obra WHERE obra = ? ORDER BY numero",
                           (obra,))]


def capitulos_de_version(con, obra, numero):
    return [f[0] for f in _leer(
        con, "SELECT capitulo FROM capitulo_de_version WHERE obra = ? AND numero = ? "
             "ORDER BY orden", (obra, numero))]


def version_vigente(con, obra):
    """La ultima **publicada**; si no hay ninguna, la 1. `None` si la obra no tiene
    versiones. No es la ultima creada: la cascada crea la version antes de escribirla, y
    el lector la veria a medias (`F-121`, TLC `CE-14`). La regla, en `commons/obra/`."""
    return obra_vigente.version_vigente(con, obra)


def leer(con, id_obra: str):
    asegurar_tablas(con)
    fila = con.execute(
        "SELECT id, titulo, premisa, genero FROM obra WHERE id = ?", (id_obra,)
    ).fetchone()
    if fila is None:
        return None
    # `PLAN-23` A6: los de la version vigente. Sin version -una obra de antes-, los de
    # la obra por su orden, como siempre.
    vigente = version_vigente(con, id_obra)
    capitulos = (capitulos_de_version(con, id_obra, vigente) if vigente is not None
                 else [r[0] for r in con.execute(
                     "SELECT id FROM capitulo WHERE obra = ? ORDER BY orden", (id_obra,))])
    return {"id": fila[0], "titulo": fila[1], "premisa": fila[2],
            "genero": fila[3], "capitulos": capitulos}


def estado_de_capitulo(con, capitulo):
    """El `estado_de_capitulo` de un capitulo, o `None` si no existe."""
    fila = con.execute("SELECT estado FROM capitulo WHERE id = ?", (capitulo,)).fetchone()
    return fila[0] if fila else None
