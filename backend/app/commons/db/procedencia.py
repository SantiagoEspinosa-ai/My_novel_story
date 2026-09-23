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


def registrar(con: sqlite3.Connection, version="__del_arbol__", cwd=None,
              brief=None, sistema=None):
    """Con que codigo **y con que brief** se creo esta base. **No pisa.**

    Son las dos mitades del mismo par. El commit dice que **codigo** escribio
    las filas; la huella del brief dice que **forma de obra** se le pidio. Con
    una sola, una tanda se puede repetir aproximadamente; con las dos, se puede
    repetir exactamente — y dos tandas con el mismo codigo y distinto brief
    dejan de parecer comparables, porque no lo son: son dos novelas.
    """
    if version == "__del_arbol__":
        version = version_del_arbol(cwd)
    with con:
        con.executescript(SQL)
        con.execute("INSERT OR IGNORE INTO procedencia (clave, valor) "
                    "VALUES ('version_del_harness', ?)",
                    (version or SIN_DETERMINAR,))
        if brief:
            con.execute("INSERT OR IGNORE INTO procedencia (clave, valor) "
                        "VALUES ('huella_del_brief', ?)", (brief,))
        if sistema:
            # `MF-28`: el commit dice con **que codigo**, el brief con **que
            # novela**, y esto con **que maquina** -modelos, topes, techo-. Sin
            # los tres, dos tandas que dieron numeros distintos no se pueden
            # explicar: el modelo cambia el coste y la calidad sin que la
            # novela haya cambiado nada.
            con.execute("INSERT OR IGNORE INTO procedencia (clave, valor) "
                        "VALUES ('huella_del_sistema', ?)", (sistema,))


def leer(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)
    filas = dict((f[0], (f[1], f[2])) for f in con.execute(
        "SELECT clave, valor, cuando FROM procedencia"))
    v = filas.get("version_del_harness")
    b = filas.get("huella_del_brief")
    sis = filas.get("huella_del_sistema")
    return {"version": v[0] if v else None,
            "creada_en": v[1] if v else None,
            "sistema": sis[0] if sis else None,
            # `None` y no una cadena vacia: las bases anteriores a esto no lo
            # llevan, y hay que poder distinguir "no consta" de "sin brief".
            "brief": b[0] if b else None}


def comprobar(con: sqlite3.Connection, version="__del_arbol__", cwd=None,
              brief=None, sistema=None):
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
    if brief:
        guardado = leer(con)["brief"]
        if guardado and guardado != brief:
            return ("esta base se genero con el brief {0} y ahora se pide {1}. "
                    "Mismo codigo y distinta forma de obra **no es la misma "
                    "tanda**: comparar sus numeros seria comparar dos novelas "
                    "distintas".format(guardado, brief))
    if sistema:
        guardado = leer(con)["sistema"]
        if guardado and guardado != sistema:
            return ("esta base corrio con la configuracion de sistema {0} y "
                    "ahora se pide {1}. El modelo y los topes cambian el coste "
                    "y la calidad **sin que la novela haya cambiado**, asi que "
                    "comparar las dos tandas atribuiria a la obra lo que hizo "
                    "la maquina".format(guardado, sistema))
    return None
