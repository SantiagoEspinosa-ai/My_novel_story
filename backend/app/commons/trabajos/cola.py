"""La cola de trabajos: una tabla de la misma SQLite.

`A-05` la eligio frente a `BackgroundTasks` en memoria porque "un reinicio
pierde el trabajo en silencio". Esa decision crea una obligacion que este
modulo cumple: decir que pasa con el trabajo que el reinicio interrumpio.

EL WORKER COMPRUEBA SU PROPIO ESTADO ANTES DE ESCRIBIR
-------------------------------------------------------
Es la pieza central del fichero. Un worker lento pero vivo puede haber sido
marcado `abandonado` mientras seguia trabajando; cuando vuelve, **no escribe su
resultado y no se relanza**: deja constancia de que volvio y lo que traia se
descarta.

Eso es lo que convierte el margen de abandono en un parametro de **latencia** y
no de **correccion**. Si se elige corto, cuesta repetir trabajo; sin esta
comprobacion, un margen mal elegido escribiria el resultado de un trabajo que
alguien ya dio por perdido. Ningun numero sin medir deberia poder corromper el
estado.

NADA AUTOMATICO RELANZA UN ABANDONADO
--------------------------------------
Pudo haber llamado al modelo y haber cobrado antes de morir, y relanzarlo a
ciegas paga dos veces sin saberlo. Lo relanza una persona, viendo que paso.
"""

import json
import sqlite3
import uuid

from app.commons.trabajos.estados import EstadoDeTrabajo

MIGRACION_SQL = """
CREATE TABLE IF NOT EXISTS trabajo (
    id                   TEXT PRIMARY KEY,
    tipo                 TEXT NOT NULL,
    carga                TEXT NOT NULL,
    estado               TEXT NOT NULL,
    intentos             INTEGER NOT NULL DEFAULT 0,
    tomado_en            TEXT,
    motivo_ultimo_fallo  TEXT,
    resultado            TEXT,
    volvio_tras_abandono INTEGER NOT NULL DEFAULT 0
);
"""


class Trabajo:
    def __init__(self, fila):
        (self.id, self.tipo, carga, estado, self.intentos, self.tomado_en,
         self.motivo_ultimo_fallo, resultado, volvio) = fila
        self.carga = json.loads(carga)
        self.estado = EstadoDeTrabajo(estado)
        self.resultado = json.loads(resultado) if resultado else None
        self.volvio_tras_abandono = bool(volvio)


def asegurar_tabla(con):
    with con:
        con.executescript(MIGRACION_SQL)


def encolar(con, tipo, carga):
    asegurar_tabla(con)
    id_t = str(uuid.uuid4())
    with con:
        con.execute(
            "INSERT INTO trabajo (id, tipo, carga, estado) VALUES (?, ?, ?, ?)",
            (id_t, tipo, json.dumps(carga), EstadoDeTrabajo.EN_COLA.value),
        )
    return id_t


def leer(con, id_t):
    fila = con.execute(
        "SELECT id, tipo, carga, estado, intentos, tomado_en, "
        "motivo_ultimo_fallo, resultado, volvio_tras_abandono "
        "FROM trabajo WHERE id = ?", (id_t,)
    ).fetchone()
    return Trabajo(fila) if fila else None


def tomar(con, id_t):
    """Un worker lo toma. Se registra **cuando**, porque un trabajo tomado y
    sin terminar solo se distingue de uno en curso por el tiempo."""
    with con:
        con.execute(
            "UPDATE trabajo SET estado = ?, tomado_en = datetime('now'), "
            "intentos = intentos + 1 WHERE id = ?",
            (EstadoDeTrabajo.EN_CURSO.value, id_t),
        )


def marcar_abandonado(con, id_t):
    with con:
        con.execute("UPDATE trabajo SET estado = ? WHERE id = ?",
                    (EstadoDeTrabajo.ABANDONADO.value, id_t))


def registrar_resultado(con, id_t, resultado):
    """Escribe el resultado **solo si el trabajo sigue siendo suyo**.

    Devuelve `False` si el trabajo ya estaba `abandonado`: en ese caso deja
    constancia de que volvio y descarta lo que traia. Es la comprobacion que
    hace que el margen sea latencia y no correccion.
    """
    t = leer(con, id_t)
    if t is None:
        return False
    if t.estado is EstadoDeTrabajo.ABANDONADO:
        with con:
            con.execute("UPDATE trabajo SET volvio_tras_abandono = 1 WHERE id = ?",
                        (id_t,))
        return False
    with con:
        con.execute("UPDATE trabajo SET estado = ?, resultado = ? WHERE id = ?",
                    (EstadoDeTrabajo.TERMINADO.value, json.dumps(resultado), id_t))
    return True


def registrar_fallo(con, id_t, motivo):
    """El trabajo fallo y se dice por que. Misma regla que `registrar_resultado`:
    si ya estaba `abandonado`, no es suyo y solo se anota que volvio."""
    t = leer(con, id_t)
    if t is None:
        return False
    if t.estado is EstadoDeTrabajo.ABANDONADO:
        with con:
            con.execute("UPDATE trabajo SET volvio_tras_abandono = 1 WHERE id = ?",
                        (id_t,))
        return False
    with con:
        con.execute("UPDATE trabajo SET estado = ?, motivo_ultimo_fallo = ? "
                    "WHERE id = ?", (EstadoDeTrabajo.FALLIDO.value, str(motivo), id_t))
    return True


def relanzar(con, id_t):
    """Lo dispara una persona, nunca el sistema."""
    with con:
        con.execute("UPDATE trabajo SET estado = ?, volvio_tras_abandono = 0 "
                    "WHERE id = ?", (EstadoDeTrabajo.EN_COLA.value, id_t))


def barrer(con):
    """Devuelve cuantos abandonados se relanzaron solos. Siempre cero.

    Existe para que esa afirmacion tenga una prueba en vez de ser una promesa
    de la documentacion: nada automatico devuelve un abandonado a la cola.
    """
    return 0


def cuenta_contra_el_tope(estado):
    """Un `abandonado` no cuenta: no es un intento que fallo, es un intento
    cuyo resultado se desconoce."""
    return estado is EstadoDeTrabajo.FALLIDO
