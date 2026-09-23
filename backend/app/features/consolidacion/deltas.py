"""Guardar el delta de cada escena, que hasta ahora se aplicaba y se tiraba.

`SPEC-01` §3.2.2 declara la tabla `delta_de_escena` y la llama **fuente de
verdad del estado**. No existia: lo que quedaba tras consolidar era el
**efecto** del delta -donde esta cada quien, quien sabe que-, y el efecto no
deja reconstruir su causa. En particular se perdia entero `acciones`, que dice
que personaje obro sirviendose de que hecho y es lo mas cercano que el dominio
tiene a "esta escena depende de este hecho".

POR QUE SE GUARDA EL DELTA ENTERO Y EN JSON
--------------------------------------------
El delta es un diff heterogeneo de ocho listas que el dominio define como una
sola cosa. Descomponerlo en ocho tablas obligaria a reunirlo en cada lectura y,
peor, a decidir por adelantado que partes importan; guardarlo entero conserva
**lo que el Escritor devolvio**, que es lo que luego se quiere poder comparar.
Lo derivado -que hechos usa una escena, por ejemplo- se indexa aparte a partir
de aqui, y esta tabla sigue siendo la fuente.

La escena ya guarda asi `cambio_de_valor`, `beats` y `longitud_objetivo`: no se
inaugura una costumbre.

POR QUE POR ESCENA Y VERSION, Y NO SOLO POR ESCENA
---------------------------------------------------
El texto y el delta vienen en la misma respuesta (`RF-09`), asi que son dos
mitades del mismo intento y se versionan igual que el `Borrador`. Una clave
por escena sola machacaria el delta viejo con el nuevo en cuanto se regenerara
algo, y el delta viejo es justo lo que hace falta para saber si la
regeneracion movio el estado del mundo o solo cambio la prosa (`SPEC-23`).

La version puede no constar, porque hoy no todos los caminos que consolidan la
conocen. Entonces se guarda **ausente**: `NULL`, nunca `0`. Un cero se leeria
como "la version cero" y un hueco se lee como lo que es (`RF-25`).
"""

import json
import sqlite3

SQL = """
CREATE TABLE IF NOT EXISTS delta_de_escena (
    orden     INTEGER PRIMARY KEY AUTOINCREMENT,
    escena    TEXT    NOT NULL,
    version   INTEGER,
    contenido TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS delta_por_escena ON delta_de_escena (escena, orden);
"""


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar(con, escena, delta, version=None):
    """Escribe el delta tal cual vino.

    No abre transaccion propia a proposito: cuando lo llama la consolidacion,
    tiene que ir **dentro** de la suya. Fuera de ella quedaria guardado el
    delta de una escena que no llego a consolidarse.
    """
    con.execute(
        "INSERT INTO delta_de_escena (escena, version, contenido) VALUES (?, ?, ?)",
        (escena, version, json.dumps(delta, ensure_ascii=False)),
    )


def leer(con, escena):
    """Todos los deltas de la escena, del mas viejo al mas nuevo.

    Devuelve lista y no un solo delta porque una escena regenerada tiene mas de
    uno, y quedarse con el ultimo es perder la comparacion.
    """
    filas = con.execute(
        "SELECT version, contenido FROM delta_de_escena WHERE escena = ? ORDER BY orden",
        (escena,),
    )
    return [{"version": f[0], "delta": json.loads(f[1])} for f in filas]


def ultimo(con, escena):
    """El delta vigente de una escena, o `None` si no hay ninguno.

    `None` significa que no consta, y quien lo reciba tiene que distinguirlo de
    un delta vacio: un delta vacio es una escena que no cambio nada, y eso ya
    seria un hallazgo de `INV-01`.
    """
    guardados = leer(con, escena)
    return guardados[-1] if guardados else None
