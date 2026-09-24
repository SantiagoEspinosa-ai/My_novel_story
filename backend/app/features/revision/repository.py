"""Persistencia de la peticion de cambio del lector (`SPEC-23`, `PLAN-23` A7, `C-4`).

Es el unico fichero de la feature que ve SQL (`A-01`). Una peticion **no edita
nada**: el enunciado nuevo de un hecho o el nombre nuevo de un personaje viven aqui,
y valen en la version que la peticion produce. `HechoCanonico` no se toca.
"""

import json
import sqlite3

from app.commons.db.migraciones import PETICION_SQL
from app.commons.dominio.enumeraciones import ClaseDePeticion, SalidaDeRegeneracion

_COLUMNAS = ("id, obra, version_de_partida, clase, hecho, enunciado_nuevo, personaje, "
             "nombre_nuevo, texto, salida, capitulos_propuestos, creada_en")


def asegurar_tablas(con):
    with con:
        con.executescript(PETICION_SQL)


def guardar(con, obra, peticion):
    """Devuelve el identificador. Las enumeraciones entran validadas o no entran."""
    asegurar_tablas(con)
    salida = peticion.get("salida")
    with con:
        cur = con.execute(
            "INSERT INTO peticion_de_cambio (obra, version_de_partida, clase, hecho, "
            "enunciado_nuevo, personaje, nombre_nuevo, texto, salida, capitulos_propuestos) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (obra, peticion["version_de_partida"], ClaseDePeticion(peticion["clase"]).value,
             peticion.get("hecho"), peticion.get("enunciado_nuevo"),
             peticion.get("personaje"), peticion.get("nombre_nuevo"), peticion["texto"],
             SalidaDeRegeneracion(salida).value if salida else None,
             json.dumps(list(peticion.get("capitulos_propuestos") or []),
                        ensure_ascii=False)))
    return cur.lastrowid


def leer(con, id_peticion):
    """La peticion, o `None`. No crea la tabla: se lee tambien en solo lectura."""
    try:
        f = con.execute("SELECT {0} FROM peticion_de_cambio WHERE id = ?".format(_COLUMNAS),
                        (id_peticion,)).fetchone()
    except sqlite3.OperationalError:
        return None
    if f is None:
        return None
    return {"id": f[0], "obra": f[1], "version_de_partida": f[2],
            "clase": ClaseDePeticion(f[3]), "hecho": f[4], "enunciado_nuevo": f[5],
            "personaje": f[6], "nombre_nuevo": f[7], "texto": f[8],
            "salida": SalidaDeRegeneracion(f[9]) if f[9] else None,
            "capitulos_propuestos": json.loads(f[10]), "creada_en": f[11]}
