"""Con que codigo se escribio esta base.

EL CASO QUE LO ABRIO, MEDIDO
------------------------------
Una obra de diez capitulos llevaba una hora corriendo cuando `uso_de_hecho`
entro en la rama. Su proceso habia importado los modulos al lanzarse, asi que
siguio escribiendo con **codigo anterior al del arbol**: la tabla ni siquiera
existe en esa base.

Preguntarle despues *"que escenas leyeron este hecho"* habria devuelto una
lista vacia indistinguible de **ninguna**, y ese cero no se habria enseñado:
**se habria medido**, dando un arrastre pequeño y perfectamente creible.

Lo que faltaba no era una comprobacion mas. Era que **la base no guarda con que
codigo se escribio**: la traza guarda el modelo y `VER-62` vigila que sea
estable entre delegaciones, y del harness no habia nada. Una medida sobre una
base vieja contesta en silencio sobre otro codigo.

POR QUE SE GUARDA LA VERSION DE **CREACION** Y NO LA ULTIMA
-------------------------------------------------------------
Porque la pregunta util es *"con que codigo se escribio lo que hay aqui"*, y
sobrescribir contestaria *"cual fue el ultimo proceso que la abrio"*, que no
dice nada sobre las filas que ya estaban. Por eso `registrar` **no pisa**.

LO QUE NO SE PUEDE DETERMINAR SE DICE
---------------------------------------
Si no hay repositorio a mano, la version queda como `sin_determinar` y no como
un valor plausible. Un dato inventado que queda escrito deja de distinguirse
de uno medido, que es la regla que gobierna todos los numeros del proyecto.
"""

import subprocess
import sqlite3

SIN_DETERMINAR = "sin_determinar"

SQL = """
CREATE TABLE IF NOT EXISTS procedencia (
    clave  TEXT PRIMARY KEY,
    valor  TEXT NOT NULL,
    cuando TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def version_del_arbol(cwd=None) -> str:
    """El commit con el que corre este proceso, o `SIN_DETERMINAR`.

    No se inventa nada: fuera de un repositorio, o sin `git` en el camino, la
    respuesta es que no consta.
    """
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, cwd=cwd, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return SIN_DETERMINAR
    salida = (r.stdout or "").strip()
    return salida if r.returncode == 0 and salida else SIN_DETERMINAR


def registrar(con: sqlite3.Connection, version="__del_arbol__", cwd=None):
    """Deja constancia de con que codigo se creo esta base. **No pisa.**"""
    if version == "__del_arbol__":
        version = version_del_arbol(cwd)
    with con:
        con.executescript(SQL)
        con.execute("INSERT OR IGNORE INTO procedencia (clave, valor) "
                    "VALUES ('version_del_harness', ?)",
                    (version or SIN_DETERMINAR,))


def leer(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)
    fila = con.execute("SELECT valor, cuando FROM procedencia "
                       "WHERE clave = 'version_del_harness'").fetchone()
    if fila is None:
        return {"version": None, "creada_en": None}
    return {"version": fila[0], "creada_en": fila[1]}


def comprobar(con: sqlite3.Connection, version="__del_arbol__", cwd=None):
    """Devuelve el aviso si la base se escribio con otro codigo, o `None`.

    **Una base sin procedencia no es una base conforme** (Regla 8): las
    anteriores a esto no tienen fila, y leer esa ausencia como "coincide"
    seria exactamente el silencio que esto viene a quitar.
    """
    if version == "__del_arbol__":
        version = version_del_arbol(cwd)
    guardada = leer(con)["version"]
    if guardada is None:
        return ("esta base no dice con que codigo se escribio, y el proceso "
                "actual corre con {0}. **No consta** que coincidan: las bases "
                "anteriores a `procedencia` no llevan la marca, asi que "
                "cualquier medida sobre ella puede estar contestando sobre "
                "otro codigo".format(version))
    if guardada != version:
        return ("esta base se escribio con {0} y el proceso actual corre con "
                "{1}. Una medida sobre ella contesta sobre el codigo de "
                "entonces, no sobre el de ahora".format(guardada, version))
    return None
