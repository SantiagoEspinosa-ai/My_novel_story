"""El estado del mundo, reconstruido desde los deltas.

    "El estado del mundo se reconstruye acumulando los deltas de escena en
     orden. No se relee el texto para averiguar que paso."

Hasta `PLAN-01` E5b el mundo se le pasaba al ciclo **escrito a mano**, asi que
la escena 2 habria generado contra el mundo de la 1 y el contexto nunca habria
crecido. Este modulo es lo que cierra ese circuito.

EL REGISTRO DE CONOCIMIENTO SE ESCRIBE AQUI
--------------------------------------------
`INV-03` lo **lee** y hasta ahora **nadie lo escribia**: funcionaba porque el
fixture lo sembraba. En una generacion de verdad eso significa que `INV-03`
bloquearia cada escena que construyera sobre la anterior, porque lo revelado en
la 1 no constaria en la 2.

La regla: **lo que el delta declara como revelacion queda sabido a partir de
esa escena**, para el sujeto que la hizo. No para todos: que Ana revele algo no
hace que Marta lo sepa, y esa distincion es media novela de terror.
"""

import json
import sqlite3

SQL = """
CREATE TABLE IF NOT EXISTS conocimiento (
    sujeto       TEXT NOT NULL,
    hecho        TEXT NOT NULL,
    desde_escena TEXT,
    grado        TEXT NOT NULL DEFAULT 'sabe',
    fuente       TEXT,
    PRIMARY KEY (sujeto, hecho)
);
CREATE TABLE IF NOT EXISTS lugar (
    id      TEXT PRIMARY KEY,
    accesos TEXT NOT NULL DEFAULT '[]',
    -- `PLAN-27` E2: `Lugar.nombre`. Lo fija `montar` desde el plan.
    nombre  TEXT
);
"""


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


# `SPEC-17` C-3: lo que se sabe desde antes de la escena 1 no tiene escena de
# origen, asi que necesita un valor propio de `fuente`. Sin el, la invariante de
# la fuente que `SPEC-16` dejo abierta nace ya incumplida por estas entradas.
ANTERIOR_AL_RELATO = "anterior_al_relato"


def sembrar_conocimiento(con, entradas):
    """Lo que los personajes saben **antes de la escena 1** (`SPEC-17` C-1).

    Va en esta misma tabla y no en una aparte: tener dos sitios donde consta
    "quien sabe que" garantiza que la copia que alguien olvide actualizar sea
    justo la que `INV-03` lea. `desde_escena` queda vacio, que es lo que
    significa *anterior al relato*.

    Sin esto el registro arrancaba vacio y **ninguna accion era posible en la
    primera escena de una obra** (`F-32`): un personaje llega sabiendo cosas de
    antes del relato, y eso no lo revela ninguna escena.
    """
    asegurar_tablas(con)
    with con:
        for e in entradas:
            con.execute(
                "INSERT OR REPLACE INTO conocimiento (sujeto, hecho, "
                "desde_escena, grado, fuente) VALUES (?, ?, NULL, ?, ?)",
                (e["sujeto"], e["hecho"], e.get("grado", "sabe"),
                 ANTERIOR_AL_RELATO))


def sembrar_lugares(con, accesos: dict):
    """El grafo de accesos. Vive en el bloque 4 desde `SPEC-12`, porque
    `INV-02` lo lee y el bloque 2 se elimina."""
    asegurar_tablas(con)
    with con:
        for id_lugar, vecinos in accesos.items():
            # Columnas con nombre (una migracion cambia el orden) y sin `OR REPLACE`,
            # que borraria el nombre ya fijado (`PLAN-27` E2).
            con.execute("INSERT INTO lugar (id, accesos) VALUES (?, ?) "
                        "ON CONFLICT(id) DO UPDATE SET accesos = excluded.accesos",
                        (id_lugar, json.dumps(vecinos)))


def fijar_nombre_de_lugar(con, lugar, nombre):
    """`Lugar.nombre`."""
    asegurar_tablas(con)
    with con:
        con.execute("UPDATE lugar SET nombre = ? WHERE id = ?", (nombre, lugar))


def aplicar_conocimiento(con, escena, delta):
    """Escribe lo que el delta revela. Se llama **dentro** de la transaccion
    de la consolidacion, o un delta a medias dejaria conocimiento sin estado."""
    for rev in (delta or {}).get("revelaciones", []):
        con.execute(
            "INSERT OR IGNORE INTO conocimiento (sujeto, hecho, desde_escena, "
            "grado, fuente) VALUES (?, ?, ?, 'sabe', ?)",
            (rev["sujeto"], rev["hecho"], escena, escena))


def leer(con) -> dict:
    """El mundo en `t`, en la forma que esperan las puertas.

    No lee ningun texto: sale de las tablas que los deltas han ido dejando.
    """
    asegurar_tablas(con)
    vivas, ubic = {}, {}
    for id_e, vital, lugar in con.execute("SELECT id, vital, lugar FROM entidad"):
        vivas[id_e] = vital
        ubic[id_e] = lugar
    accesos = {i: json.loads(a) for i, a in con.execute("SELECT id, accesos FROM lugar")}
    conocimiento = {}
    for s, h, desde, grado in con.execute(
            "SELECT sujeto, hecho, desde_escena, grado FROM conocimiento"):
        conocimiento[(s, h)] = {"desde": desde, "grado": grado}
    return {"entidades_vivas": vivas, "ubicaciones": ubic,
            "accesos": accesos, "conocimiento": conocimiento}
