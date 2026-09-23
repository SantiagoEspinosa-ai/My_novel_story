"""Aplicar el delta al estado del mundo, entero o nada.

POR QUE LA ATOMICIDAD ES ARQUITECTURA Y NO DETALLE
---------------------------------------------------
`INV-05` exige que el delta este aplicado antes de generar la escena
siguiente, y **un delta a medias es un estado que la invariante no sabe
clasificar**: lo dara por aplicado o por no aplicado segun que parte se mire.
La puerta que corta la propagacion del error dejaria de cortarla justo en el
caso en que mas falta hace.

Es ademas la unica categoria de fallo de la que no se sale reintentando. Los
otros tres de `SPEC-07` detienen el trabajo y dejan el estado intacto; este lo
corrompe, y a partir de ahi todo lo que se genere encima hereda la corrupcion
sin que nada avise.
"""

import sqlite3

from app.features.consolidacion import mundo as modulo_mundo

SQL = """
CREATE TABLE IF NOT EXISTS entidad (
    id       TEXT PRIMARY KEY,
    vital    TEXT NOT NULL,
    lugar    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS escena_consolidada (
    escena TEXT PRIMARY KEY
);
"""


class DeltaIncompatible(Exception):
    """`RF-20`: no se aplica, produce hallazgo y la escena no se consolida."""


class YaConsolidada(Exception):
    pass


def asegurar_tablas(con):
    with con:
        con.executescript(SQL)
    modulo_mundo.asegurar_tablas(con)


def sembrar(con, entidades):
    with con:
        for id_e, (vital, lugar) in entidades.items():
            con.execute("INSERT OR REPLACE INTO entidad VALUES (?, ?, ?)",
                        (id_e, vital, lugar))


def estado(con):
    return {r[0]: (r[1], r[2]) for r in con.execute("SELECT id, vital, lugar FROM entidad")}


def puede_generarse_la_siguiente(con, escena):
    fila = con.execute("SELECT 1 FROM escena_consolidada WHERE escena = ?",
                       (escena,)).fetchone()
    return fila is not None


def consolidar(con, escena, delta):
    """Todo en una transaccion. Si algo falla, no queda nada escrito."""
    if puede_generarse_la_siguiente(con, escena):
        raise YaConsolidada(
            "la escena {0} ya esta consolidada; aplicar su delta dos veces "
            "duplicaria los cambios".format(escena)
        )
    try:
        with con:
            for m in delta.get("movimientos", []):
                cur = con.execute("UPDATE entidad SET lugar = ? WHERE id = ?",
                                  (m["a"], m["personaje"]))
                if cur.rowcount == 0:
                    raise DeltaIncompatible(
                        "el delta mueve a {0}, que no existe en el estado en "
                        "t".format(m["personaje"]))
            for c in delta.get("cambios_de_estado_vital", []):
                cur = con.execute("UPDATE entidad SET vital = ? WHERE id = ? AND vital = ?",
                                  (c["a"], c["personaje"], c["de"]))
                if cur.rowcount == 0:
                    raise DeltaIncompatible(
                        "el delta lleva a {0} de {1} a {2}, y su estado en t no "
                        "es {1}".format(c["personaje"], c["de"], c["a"]))
            # El conocimiento se escribe **dentro** de la misma transaccion.
            # Fuera de ella, un delta que falle a mitad dejaria al personaje
            # sabiendo algo que nunca llego a pasar: el estado a medias que
            # `INV-05` no sabe clasificar, por otra puerta.
            modulo_mundo.aplicar_conocimiento(con, escena, delta)
            con.execute("INSERT INTO escena_consolidada VALUES (?)", (escena,))
    except DeltaIncompatible:
        raise
    return True
