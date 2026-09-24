"""Que version de una obra es la vigente, en un solo sitio (`PLAN-23` `F-121`).

LA ULTIMA PUBLICADA, NO LA ULTIMA CREADA
----------------------------------------
La cascada (`S-1`) crea la version `n+1` **antes** de escribir sus capitulos, y la vigente
era la ultima creada: en el paso siguiente a pedir el cambio, todo lo que lee «la vigente»
-el alta de `brief/`, el manuscrito, la lectura web- veia una version con capitulos sin
escribir, y si la regeneracion paraba a mitad se quedaba asi. Lo encontro TLC (`CE-14`,
`LectorVeLoPublicado`). La vigente es **la ultima que la puerta publico**; si todavia no se
publico ninguna, **la 1**, que es la que se esta escribiendo por primera vez.

Vive en `commons/` porque la necesitan `brief/` y `manuscrito/`, y ninguna feature importa
a otra (`A-02`). Lee dos tablas por SQL -las versiones y los veredictos de la puerta-, que
es el acoplamiento que `manuscrito/` ya tenia con las dos (`F-28`), dicho aqui.
"""

import sqlite3


def _uno(con, sql, args):
    try:
        fila = con.execute(sql, args).fetchone()
    except sqlite3.OperationalError:
        # Sin tabla no hay filas: una base sin versiones o sin puerta todavia.
        return None
    return fila[0] if fila else None


def version_vigente(con, obra):
    """La ultima version publicada de la obra; si no hay ninguna, la mas baja que exista
    (la 1). `None` si la obra no tiene versiones."""
    primera = _uno(con, "SELECT MIN(numero) FROM version_de_obra WHERE obra = ?", (obra,))
    if primera is None:
        return None
    publicada = _uno(con, "SELECT MAX(p.version) FROM veredicto_de_publicacion p "
                          "JOIN version_de_obra v ON v.obra = p.obra AND v.numero = p.version "
                          "WHERE p.obra = ? AND p.publica = 1", (obra,))
    return publicada if publicada is not None else primera
