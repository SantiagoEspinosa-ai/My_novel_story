"""Las consultas de la lectura. Es el unico fichero de la feature que ve SQL (`A-01`).

Lee tablas que crean otras features (`obra` y `capitulo` de `brief/`; `escena`,
`borrador` y `hallazgo` de `escaleta/`) **por SQL y sin importarlas**: una feature no
importa de otra, y leer no es escribir.

Cada consulta que baja de la obra a sus capitulos filtra por **las dos** columnas cuando
las hay (`escena.obra` y `escena.capitulo`): con una obra por capitulo, preguntar solo por
una de las dos salia bien por accidente (Regla 11, `SPEC-22` `RF-37`).
"""

HALLAZGO_ABIERTO = ("abierto", "sin_veredicto")


def obra(con, id_obra):
    f = con.execute("SELECT id, titulo, dedicatoria FROM obra WHERE id = ?",
                    (id_obra,)).fetchone()
    return None if f is None else {"id": f[0], "titulo": f[1], "dedicatoria": f[2]}


def capitulos(con, id_obra):
    """Por `capitulo.orden`, que es el orden de lectura. Nunca por `id`."""
    return [{"id": f[0], "orden": f[1], "estado": f[2], "obra": id_obra}
            for f in con.execute(
                "SELECT id, orden, estado FROM capitulo WHERE obra = ? ORDER BY orden",
                (id_obra,))]


def capitulo(con, id_capitulo):
    f = con.execute("SELECT id, orden, estado, obra FROM capitulo WHERE id = ?",
                    (id_capitulo,)).fetchone()
    return None if f is None else {"id": f[0], "orden": f[1], "estado": f[2], "obra": f[3]}


_COLUMNAS_ESCENA = "id, capitulo, estado, borrador_aceptado, obra, lugar, personajes_presentes"


def _escena(f):
    return {"id": f[0], "capitulo": f[1], "estado": f[2], "borrador_aceptado": f[3],
            "obra": f[4], "lugar": f[5], "personajes_presentes": f[6]}


def escenas_de_capitulo(con, id_obra, id_capitulo):
    return [_escena(f) for f in con.execute(
        "SELECT {0} FROM escena WHERE obra = ? AND capitulo = ? ORDER BY orden".format(
            _COLUMNAS_ESCENA), (id_obra, id_capitulo))]


def escena(con, id_escena):
    f = con.execute("SELECT {0} FROM escena WHERE id = ?".format(_COLUMNAS_ESCENA),
                    (id_escena,)).fetchone()
    return None if f is None else _escena(f)


def hallazgos_abiertos(con, id_escena):
    """`abierto` y `sin_veredicto`, cada uno con **su** estado (`docs/definitions.md`)."""
    return [{"invariante": f[0], "verificador": f[1], "severidad": f[2], "estado": f[3],
             "descripcion": f[4]}
            for f in con.execute(
                "SELECT invariante, verificador, severidad, estado, descripcion "
                "FROM hallazgo WHERE escena = ? AND estado IN (?, ?) ORDER BY id",
                (id_escena,) + HALLAZGO_ABIERTO)]
