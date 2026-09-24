"""Persistencia de la reverificacion (`SPEC-23` `D-1`, `PLAN-23` A4).

Es el unico fichero de la feature que ve SQL (`A-01`). Guarda las puertas vueltas a
pasar **en una version** y contra que estado (`huella_del_estado`). No escribe en
`hallazgo`: los hallazgos de una version viajan con su fila.
"""

import json

from app.commons.db.migraciones import REVERIFICACION_SQL
from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV


def asegurar_tablas(con):
    with con:
        con.executescript(REVERIFICACION_SQL)


def guardar(con, obra, version, escena, huella, estado, hallazgos):
    with con:
        con.execute("INSERT OR REPLACE INTO reverificacion (obra, version, escena, "
                    "huella_del_estado, estado, hallazgos) VALUES (?, ?, ?, ?, ?, ?)",
                    (obra, version, escena, huella, EV(estado).value,
                     json.dumps(hallazgos, ensure_ascii=False)))


def leer(con, obra, version, escena, huella):
    """La fila con **esa** huella, o `None`. Una fila con otra huella no se devuelve:
    es un verde de otro estado."""
    f = con.execute("SELECT estado, hallazgos FROM reverificacion WHERE obra = ? AND "
                    "version = ? AND escena = ? AND huella_del_estado = ?",
                    (obra, version, escena, huella)).fetchone()
    if f is None:
        return None
    return {"estado": EV(f[0]), "hallazgos": json.loads(f[1])}
