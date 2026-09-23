"""Lo que cada llamada leyó del canon, guardado para poder responderlo después.

Es el primer fichero de esta feature que ve SQL, y llega tarde a proposito: el
ensamblado nunca necesito base. Lo que la necesita es **acordarse** de lo que
metio en cada prompt.

POR QUE NO VALE LA TRAZA QUE YA HABIA
---------------------------------------
`commons/modelo/traza.py` guarda que fichas, presagios y resumenes entraron, y
explica por que se guardan ids y no texto: el indice vectorial crece al
consolidar y los empates de una consulta KNN no tienen orden definido, asi que
**cual se recupero no se reconstruye**. El mismo argumento vale para los hechos
y para el registro de conocimiento, que no estaban en esa lista. Y ademas la
traza vive en memoria y se pierde al terminar el proceso: para una medida que
tiene que sobrevivir a la ejecucion, hace falta una tabla.

POR QUE LA LLAVE ES EL `prompt_hash` Y NO LA VERSION DEL BORRADOR
-------------------------------------------------------------------
Las lecturas se conocen **antes** de llamar al modelo y la version del
`Borrador` solo existe **despues**, si la llamada sale bien. Atarlas a la
version obligaria a escribir mas tarde y a perder justo las llamadas que
fallaron, que son las que hay que diagnosticar. El `prompt_hash` identifica la
llamada, lo guarda tambien el `Borrador` (`RF-11`) y por eso sirve de union
entre las dos mitades sin inventar ningun numero.

Si no consta, se guarda `NULL`. Nunca una cadena vacia: un hueco se lee como lo
que es (`RF-25`).
"""

import sqlite3

SQL = """
CREATE TABLE IF NOT EXISTS lectura_de_contexto (
    orden       INTEGER PRIMARY KEY AUTOINCREMENT,
    escena      TEXT NOT NULL,
    prompt_hash TEXT,
    tipo        TEXT NOT NULL,
    sujeto      TEXT NOT NULL DEFAULT '',
    hecho       TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS lectura_unica
    ON lectura_de_contexto (escena, prompt_hash, tipo, sujeto, hecho);
CREATE INDEX IF NOT EXISTS lectura_por_hecho ON lectura_de_contexto (hecho);
"""

# `sujeto` es cadena vacia cuando el tipo es `hecho`, y no `NULL`, porque el
# indice unico tiene que poder deduplicar: en SQLite dos `NULL` son distintos y
# un reintento del mismo prompt duplicaria las filas. La cadena vacia aqui
# significa **no aplica a este tipo**, que es una propiedad de la forma y no un
# dato que falte; un sujeto que falte de verdad seria otra cosa y no cabe en
# esta tabla.
SIN_SUJETO = ""


class SinRegistroDeLecturas(Exception):
    """No hay ni una lectura registrada, que no es lo mismo que ninguna.

    Una base generada por un proceso que arranco **antes** de que existiera
    este registro no tiene filas -ni tabla-, y preguntarle que escenas leyeron
    un hecho devolveria `[]`. Ese `[]` se lee como *ninguna* y alimentaria una
    medida con un cero creible.

    Es el mismo caso que un contador sin medir: ausente no es cero. Aqui se
    convierte en excepcion y no en valor porque quien pregunta esto suele estar
    midiendo, y una medida no puede empezar por confundir esas dos cosas.
    """


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar_lecturas(con, escena, lecturas, prompt_hash=None):
    """Escribe lo que esa llamada leyo. Idempotente por `prompt_hash`.

    `INSERT OR IGNORE` y no `REPLACE`: si la misma llamada se registra dos
    veces, lo segundo no es informacion nueva. Si el contexto cambio, cambio el
    prompt y con el su hash.
    """
    asegurar_tablas(con)
    filas = [(escena, prompt_hash, "hecho", SIN_SUJETO, h)
             for h in lecturas.get("hechos", [])]
    filas += [(escena, prompt_hash, "conocimiento", c["sujeto"], c["hecho"])
              for c in lecturas.get("conocimiento", [])]
    with con:
        con.executemany(
            "INSERT OR IGNORE INTO lectura_de_contexto "
            "(escena, prompt_hash, tipo, sujeto, hecho) VALUES (?, ?, ?, ?, ?)",
            filas)


def lecturas_de(con, escena):
    filas = con.execute(
        "SELECT prompt_hash, tipo, sujeto, hecho FROM lectura_de_contexto "
        "WHERE escena = ? ORDER BY orden", (escena,))
    return [{"prompt_hash": f[0], "tipo": f[1], "sujeto": f[2], "hecho": f[3]}
            for f in filas]


def escenas_que_leyeron(con, hecho):
    """Qué escenas tuvieron delante este hecho. **Sobre-aproxima a proposito.**

    Tuvo el hecho delante no es lo mismo que se sirvio de el: esta lista incluye
    escenas a las que el dato solo les pasaba por al lado. Es la direccion
    correcta del error —marcar de mas hace regenerar de mas, que cuesta y se ve;
    marcar de menos deja una contradiccion que nadie marca— y es lo que
    distingue este conjunto **observado** del **declarado** por el modelo
    (`SPEC-23` `S-5`).
    """
    asegurar_tablas(con)
    if not con.execute("SELECT 1 FROM lectura_de_contexto LIMIT 1").fetchone():
        raise SinRegistroDeLecturas(
            "no hay ninguna lectura registrada en esta base: no se puede "
            "distinguir 'ninguna escena leyo este hecho' de 'no consta'")
    filas = con.execute(
        "SELECT DISTINCT escena FROM lectura_de_contexto WHERE hecho = ? "
        "ORDER BY escena", (hecho,))
    return [f[0] for f in filas]
