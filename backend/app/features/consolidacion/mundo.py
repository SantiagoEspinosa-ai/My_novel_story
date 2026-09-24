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


def leer(con, obra=None) -> dict:
    """El mundo en `t`, en la forma que esperan las puertas.

    No lee ningun texto: sale de las tablas que los deltas han ido dejando.

    `F-100`, salida (a) del autor: con `obra`, solo las entidades, los lugares y el
    conocimiento cuyo identificador lleva el prefijo de esa obra, que es como los deja
    `planificacion.acotar_a_la_obra` desde `F-64`. Sin esto, la segunda novela de una base
    recibia el mundo de la primera. **Solo vale donde los identificadores estan acotados**
    -la novela regalo-: por eso es opcional, y la salida (b), una columna `obra` con su
    migracion, queda anotada.
    """
    asegurar_tablas(con)
    prefijo = (obra + "-%") if obra else "%"
    vivas, ubic = {}, {}
    for id_e, vital, lugar in con.execute(
            "SELECT id, vital, lugar FROM entidad WHERE id LIKE ?", (prefijo,)):
        vivas[id_e] = vital
        ubic[id_e] = lugar
    accesos = {i: json.loads(a) for i, a in con.execute(
        "SELECT id, accesos FROM lugar WHERE id LIKE ?", (prefijo,))}
    conocimiento = {}
    for s, h, desde, grado in con.execute(
            "SELECT sujeto, hecho, desde_escena, grado FROM conocimiento WHERE sujeto LIKE ?",
            (prefijo,)):
        conocimiento[(s, h)] = {"desde": desde, "grado": grado}
    return {"entidades_vivas": vivas, "ubicaciones": ubic,
            "accesos": accesos, "conocimiento": conocimiento}


# --- `PLAN-23` A2: el mundo desde la semilla y los deltas guardados ------------

def _copia(m):
    return {"entidades_vivas": dict(m.get("entidades_vivas") or {}),
            "ubicaciones": dict(m.get("ubicaciones") or {}),
            "accesos": {k: list(v) for k, v in (m.get("accesos") or {}).items()},
            "conocimiento": {k: dict(v) for k, v in (m.get("conocimiento") or {}).items()}}


def _incompatibilidad(m, delta):
    """Lo mismo que hace fallar `aplicar.consolidar`, en diccionarios. `None` si entra."""
    vivas = m["entidades_vivas"]
    for mv in delta.get("movimientos", []):
        if mv["personaje"] not in vivas:
            return ("el delta mueve a {0}, que no existe en el estado en t".format(
                mv["personaje"]))
    # Los cambios de estado vital se aplican despues de los movimientos, y en orden:
    # dos cambios sobre el mismo personaje se encadenan como en la base.
    estado = dict(vivas)
    for c in delta.get("cambios_de_estado_vital", []):
        if estado.get(c["personaje"]) != c["de"]:
            return ("el delta lleva a {0} de {1} a {2}, y su estado en t no es "
                    "{1}".format(c["personaje"], c["de"], c["a"]))
        estado[c["personaje"]] = c["a"]
    return None


def acumular(semilla, deltas):
    """El mundo tras aplicar `deltas` -pares `(escena, delta)`, en orden- a la semilla.

    **Puro**: no lee ni escribe la base y no toca la semilla. Devuelve
    `(mundo, incompatibles)`, con el mundo en la forma de `leer`. Un delta que no
    entra **no se aplica entero** -como en `aplicar.consolidar`, que es atomico- y se
    anota con su escena y su motivo, sin lanzar excepcion: quien reverifica necesita
    saber donde deja de sostenerse la obra, no que se pare la cuenta.
    """
    m = _copia(semilla)
    incompatibles = []
    for escena, delta in deltas:
        delta = delta or {}
        motivo = _incompatibilidad(m, delta)
        if motivo is not None:
            incompatibles.append({"escena": escena, "motivo": motivo})
            continue
        for mv in delta.get("movimientos", []):
            m["ubicaciones"][mv["personaje"]] = mv["a"]
        for c in delta.get("cambios_de_estado_vital", []):
            m["entidades_vivas"][c["personaje"]] = c["a"]
        # `INSERT OR IGNORE`: lo que ya constaba no se pisa, tampoco su `desde`.
        for rev in delta.get("revelaciones", []):
            m["conocimiento"].setdefault((rev["sujeto"], rev["hecho"]),
                                         {"desde": escena, "grado": "sabe"})
    return m, incompatibles


def rebobinar(con, m):
    """Escribe el mundo `m` en `entidad`, `lugar` y `conocimiento`, **en una sola
    transaccion** (`PLAN-23` `C-2`): el mundo vivo es el de la version que se escribe.

    Conserva la fecha de nacimiento, que no es estado sino dato del personaje. Lo que
    no esta en `m` deja de existir en el mundo vivo. La fuente del conocimiento se
    reconstruye como la escribe la consolidacion: la escena que lo revelo, o
    `anterior_al_relato` si no tiene escena.
    """
    asegurar_tablas(con)
    with con:
        vivas = m.get("entidades_vivas") or {}
        ubic = m.get("ubicaciones") or {}
        con.execute("DELETE FROM entidad WHERE id NOT IN ({0})".format(
            ",".join("?" * len(vivas))), list(vivas))
        for id_e, vital in vivas.items():
            con.execute("INSERT INTO entidad (id, vital, lugar) VALUES (?, ?, ?) "
                        "ON CONFLICT(id) DO UPDATE SET vital = excluded.vital, "
                        "lugar = excluded.lugar", (id_e, vital, ubic.get(id_e)))
        con.execute("DELETE FROM lugar")
        for id_l, vecinos in (m.get("accesos") or {}).items():
            con.execute("INSERT INTO lugar (id, accesos) VALUES (?, ?)",
                        (id_l, json.dumps(vecinos)))
        con.execute("DELETE FROM conocimiento")
        for (sujeto, hecho), v in (m.get("conocimiento") or {}).items():
            con.execute("INSERT INTO conocimiento (sujeto, hecho, desde_escena, grado, "
                        "fuente) VALUES (?, ?, ?, ?, ?)",
                        (sujeto, hecho, v.get("desde"), v.get("grado", "sabe"),
                         v.get("desde") or ANTERIOR_AL_RELATO))


def huella(semilla, deltas):
    """Lo que identifica un estado del mundo (`PLAN-23` `C-3`): la semilla y la lista
    ordenada de deltas `(escena, delta)` aplicados para llegar a el, resumidas en un
    hash. Dos estados con la misma huella son el mismo; un verde cuya huella no es la
    del estado vigente de su version **no cuenta** (`D-1`)."""
    import hashlib
    canon = {
        "semilla": {
            "entidades_vivas": sorted((semilla.get("entidades_vivas") or {}).items()),
            "ubicaciones": sorted((semilla.get("ubicaciones") or {}).items()),
            "accesos": sorted((k, sorted(v)) for k, v in (semilla.get("accesos") or {}).items()),
            "conocimiento": sorted(
                (list(k), v.get("desde"), v.get("grado"))
                for k, v in (semilla.get("conocimiento") or {}).items()),
        },
        "deltas": [[escena, delta] for escena, delta in deltas],
    }
    texto = json.dumps(canon, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()
