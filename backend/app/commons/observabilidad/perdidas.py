"""Lo que no llego a Langfuse (`SPEC-29` `RF-09`, `PLAN-29` E3).

Si Langfuse no responde la generacion sigue, y la perdida queda aqui. Se guarda **la clase
del error, no su mensaje**: un mensaje de red puede citar lo que se intentaba enviar, y lo
que se intentaba enviar no tiene por que poder guardarse.
"""

SQL = """
CREATE TABLE IF NOT EXISTS envio_perdido (
    id      INTEGER PRIMARY KEY,
    sesion  TEXT NOT NULL,
    tipo    TEXT NOT NULL,
    nombre  TEXT,
    clase   TEXT NOT NULL,
    momento TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def asegurar_tabla(con):
    with con:
        con.executescript(SQL)


def guardar(con, sesion, tipo, nombre, error):
    asegurar_tabla(con)
    with con:
        con.execute("INSERT INTO envio_perdido (sesion, tipo, nombre, clase) "
                    "VALUES (?, ?, ?, ?)", (sesion, tipo, nombre, type(error).__name__))


def de(con, sesion=None):
    asegurar_tabla(con)
    filas = con.execute("SELECT sesion, tipo, nombre, clase FROM envio_perdido "
                        "WHERE ? IS NULL OR sesion = ? ORDER BY id", (sesion, sesion))
    return [{"sesion": f[0], "tipo": f[1], "nombre": f[2], "clase": f[3]} for f in filas]
