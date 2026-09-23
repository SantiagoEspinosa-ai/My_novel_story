"""Persistencia de los usos de un hecho y de la cronologia de la fabula.

`A-01`: es el unico fichero de la feature que ve SQL.

QUE GUARDA ESTA FEATURE Y POR QUE NO LO GUARDA `escaleta/`
-----------------------------------------------------------
`escaleta/` guarda **lo que el plan declara**: que escenas hay y que hechos
existen. Aqui se guarda **lo que el texto resulto hacer con ellos**, que es
otra cosa y se escribe en otro momento -al consolidar, no al planificar-.
Juntarlas en la misma feature volveria a mezclar el plan con el acta, que es la
confusion que `SPEC-15` costo separar.

LAS DOS TABLAS RESPONDEN A DOS PREGUNTAS DISTINTAS
---------------------------------------------------
`uso_de_hecho` responde *"¿donde se usa este hecho?"* y `evento_cronologico`
responde *"¿que paso, cuando y quien estaba?"*. Viven juntas porque las dos son
el acta de lo ocurrido y las dos se escriben en el mismo instante, dentro de la
misma transaccion.
"""

import sqlite3

from app.commons.dominio.enumeraciones import OrigenDeUso as O
from app.commons.dominio.enumeraciones import TipoDePresencia as P
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U

SQL = """
CREATE TABLE IF NOT EXISTS uso_de_hecho (
    hecho    TEXT NOT NULL,
    escena   TEXT NOT NULL,
    capitulo TEXT,
    tipo     TEXT NOT NULL,
    origen   TEXT NOT NULL,
    -- El **origen forma parte de la clave**, y dejarlo fuera costaba una fila.
    -- El mismo hecho puede constar como `depende` por dos caminos que no valen
    -- lo mismo: observado -el ensamblador lo metio en el prompt, sobre-aproxima
    -- y falla ruidoso- y declarado -el delta dice que se uso, se ajusta mas y
    -- falla en silencio-. Con la clave `(hecho, escena, tipo)`, el segundo
    -- `INSERT OR REPLACE` pisaba al primero y **cual sobrevivia dependia del
    -- orden de escritura**, destruyendo sin avisar la distincion para la que
    -- existe `origen_de_uso`. La tabla se quedaba con una fila creible.
    PRIMARY KEY (hecho, escena, tipo, origen)
);
CREATE TABLE IF NOT EXISTS evento_cronologico (
    id           TEXT PRIMARY KEY,
    obra         TEXT NOT NULL,
    t_fabula     TEXT NOT NULL,
    duracion_min INTEGER,
    lugar        TEXT,
    escena       TEXT,
    capitulo     TEXT,
    descripcion  TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS participacion_en_evento (
    evento    TEXT NOT NULL,
    personaje TEXT NOT NULL,
    presencia TEXT NOT NULL DEFAULT 'presente',
    PRIMARY KEY (evento, personaje)
);
"""

# Los indices van aparte del `CREATE TABLE` porque sirven a consultas concretas
# y conviene que se lea cual sostiene cada uno.
INDICES = """
-- «¿en que capitulos se usa este hecho?»: regeneracion selectiva y fichas.
CREATE INDEX IF NOT EXISTS idx_uso_por_hecho ON uso_de_hecho (hecho, tipo);
-- «¿que hechos toca este capitulo?»: el fichero Lean y la vista de capitulo.
CREATE INDEX IF NOT EXISTS idx_uso_por_capitulo ON uso_de_hecho (capitulo, tipo);
-- El orden de la fabula. Es la consulta de la que cuelgan las tres de Lean.
CREATE INDEX IF NOT EXISTS idx_evento_por_t ON evento_cronologico (obra, t_fabula);
CREATE INDEX IF NOT EXISTS idx_evento_por_capitulo ON evento_cronologico (capitulo);
-- «¿donde estuvo este personaje?»: la comprobacion de ubicuidad la recorre
-- por personaje, no por evento, asi que el indice va por la otra columna.
CREATE INDEX IF NOT EXISTS idx_participacion_por_personaje
    ON participacion_en_evento (personaje, presencia);
"""

# `SPEC-21` C-2: existe, se puede escribir y **nadie lo deduce todavia**.
# Esta constante es lo que permite que una consulta diga "no se ha mirado" en
# vez de devolver una lista vacia que se lee como "no hay ninguno".
TIPOS_QUE_NADIE_DEDUCE = (U.CONTRADICE,)


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)
        con.executescript(INDICES)


# ---------------------------------------------------------------------------
# Usos de un hecho
# ---------------------------------------------------------------------------


def registrar_usos(con, usos, dentro_de_transaccion=False):
    """Escribe los usos. Idempotente por `(hecho, escena, tipo, origen)`.

    `dentro_de_transaccion` existe porque la consolidacion ya abrio la suya:
    anidar `with con` en SQLite hace commit del bloque interno y romperia la
    atomicidad que `SPEC-21` C-4 exige. Quien llama desde dentro lo dice.
    """
    def _escribir():
        for u in usos:
            con.execute(
                "INSERT OR REPLACE INTO uso_de_hecho (hecho, escena, capitulo, "
                "tipo, origen) VALUES (?, ?, ?, ?, ?)",
                (u["hecho"], u["escena"], u.get("capitulo"),
                 str(u["tipo"]), str(u["origen"])))

    if dentro_de_transaccion:
        _escribir()
    else:
        with con:
            _escribir()
    return len(usos)


def _uso(f):
    # Los valores vuelven como miembros de su enumeracion, no como cadenas.
    # Devolverlos como texto fue lo que abrio la puerta de capitulo en silencio
    # en `hallazgos_abiertos`: `"mayor" is Severidad.MAYOR` es falso.
    return {"hecho": f[0], "escena": f[1], "capitulo": f[2],
            "tipo": U(f[3]), "origen": O(f[4])}


def usos_de_hecho(con, hecho, tipos=None, origenes=None):
    """Las filas de un hecho, filtrables por tipo y por origen.

    Son **dos ejes independientes** y por eso son dos filtros. El tipo dice
    *que relacion* tiene la escena con el hecho; el origen, *quien lo afirma*.
    Sin `origenes` cuentan todos, que es lo que quiere casi todo el mundo: a
    quien pregunta "¿donde se usa esto?" le da igual si lo midio el codigo o lo
    declaro el delta.

    Lo quiere quien compara. Preguntar solo por `regla` da el conjunto
    **observado** -sobre-aproxima, falla ruidoso- y solo por `delta` el
    **declarado** -se ajusta mas, falla en silencio-. Poder pedir cada uno por
    separado es lo que permite medir cuanto se separan antes de elegir.
    """
    sql = ("SELECT hecho, escena, capitulo, tipo, origen FROM uso_de_hecho "
           "WHERE hecho = ?")
    args = [hecho]
    if tipos is not None:
        sql += " AND tipo IN ({0})".format(",".join("?" * len(tipos)))
        args += [str(t) for t in tipos]
    if origenes is not None:
        sql += " AND origen IN ({0})".format(",".join("?" * len(origenes)))
        args += [str(o) for o in origenes]
    return [_uso(f) for f in con.execute(sql + " ORDER BY escena, tipo, origen", args)]


def usos_de_capitulo(con, capitulo, tipos=None):
    sql = ("SELECT hecho, escena, capitulo, tipo, origen FROM uso_de_hecho "
           "WHERE capitulo = ?")
    args = [capitulo]
    if tipos is not None:
        sql += " AND tipo IN ({0})".format(",".join("?" * len(tipos)))
        args += [str(t) for t in tipos]
    return [_uso(f) for f in con.execute(sql + " ORDER BY hecho, tipo", args)]


# ---------------------------------------------------------------------------
# Cronologia
# ---------------------------------------------------------------------------


def registrar_evento(con, evento, participantes=(), dentro_de_transaccion=False):
    """Un evento y quien estaba. Idempotente por `id` del evento.

    `participantes` son pares `(personaje, presencia)`. Estar y ser nombrado no
    es lo mismo: la comprobacion de ubicuidad solo mira los `presente`.
    """
    def _escribir():
        con.execute(
            "INSERT OR REPLACE INTO evento_cronologico (id, obra, t_fabula, "
            "duracion_min, lugar, escena, capitulo, descripcion) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (evento["id"], evento["obra"], evento["t_fabula"],
             evento.get("duracion_min"), evento.get("lugar"),
             evento.get("escena"), evento.get("capitulo"),
             evento.get("descripcion", "")))
        for personaje, presencia in participantes:
            con.execute(
                "INSERT OR REPLACE INTO participacion_en_evento (evento, "
                "personaje, presencia) VALUES (?, ?, ?)",
                (evento["id"], personaje, str(presencia)))

    if dentro_de_transaccion:
        _escribir()
    else:
        with con:
            _escribir()
    return evento["id"]


def eventos_de(con, obra):
    """En orden de fabula, que no tiene por que ser el orden de lectura.

    Se ordena por `t_fabula` y, a igualdad, por capitulo: dos eventos
    simultaneos existen -pasan a la vez en dos sitios- y el desempate tiene que
    ser estable o la consulta devolveria un orden distinto cada vez.
    """
    return [{"id": f[0], "t_fabula": f[1], "duracion_min": f[2], "lugar": f[3],
             "escena": f[4], "capitulo": f[5], "descripcion": f[6]}
            for f in con.execute(
                "SELECT id, t_fabula, duracion_min, lugar, escena, capitulo, "
                "descripcion FROM evento_cronologico WHERE obra = ? "
                "ORDER BY t_fabula, capitulo, id", (obra,))]


def participantes_de(con, id_evento, presencia=P.PRESENTE):
    return [f[0] for f in con.execute(
        "SELECT personaje FROM participacion_en_evento WHERE evento = ? "
        "AND presencia = ? ORDER BY personaje", (id_evento, str(presencia)))]


def presencias_de_personaje(con, obra, personaje):
    """Donde y cuando estuvo, en orden. Lo que lee la comprobacion de ubicuidad.

    Solo `presente`: que hablen de alguien en una escena no lo pone alli.
    """
    return [{"evento": f[0], "t_fabula": f[1], "duracion_min": f[2],
             "lugar": f[3], "capitulo": f[4]}
            for f in con.execute(
                "SELECT e.id, e.t_fabula, e.duracion_min, e.lugar, e.capitulo "
                "FROM evento_cronologico e "
                "JOIN participacion_en_evento p ON p.evento = e.id "
                "WHERE e.obra = ? AND p.personaje = ? AND p.presencia = ? "
                "ORDER BY e.t_fabula, e.id",
                (obra, personaje, str(P.PRESENTE)))]
