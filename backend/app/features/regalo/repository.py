"""Las consultas de la novela regalo en la web. Es el unico fichero de la feature que ve SQL.

Lee tablas que crean otras features -`obra` y `capitulo` de `brief/`, `escena` y
`valoracion_del_editor` de `escaleta/`, `entrevista` de `entrevista/`,
`progreso_de_generacion` y `gasto_de_delegacion` de las migraciones- **por SQL y sin
importarlas**: una feature no importa de otra (`docs/architecture.md`), y leer no es
escribir. Cada consulta filtra por obra.
"""

import json

from app.commons.db import migraciones


def obras_de_la_estanteria(con):
    """Cada obra montada y cada obra que solo tiene entrevista, con lo que la tarjeta ensena.

    Una entrevista nace con su obra antes de que se monte (`entrevista.crear`), asi que la
    estanteria une las dos tablas: sin eso, una entrevista a medias no tendria por donde
    volver. El nombre del destinatario sale de la ficha; si la ficha se borro (`SPEC-25`
    `RF-21`), no esta, y la dedicatoria sigue porque es de la obra (`SPEC-32`)."""
    obras = {f[0]: {"id": f[0], "titulo": f[1], "dedicatoria": f[2]} for f in con.execute(
        "SELECT id, titulo, dedicatoria FROM obra ORDER BY rowid")}
    entrevistas = {}
    if migraciones.tiene_tabla(con, "entrevista"):
        for id_e, obra, ficha, cerrada in con.execute(
                "SELECT id, obra, ficha, cerrada FROM entrevista ORDER BY rowid"):
            entrevistas[obra] = (id_e, json.loads(ficha), bool(cerrada))
            obras.setdefault(obra, {"id": obra, "titulo": None, "dedicatoria": None})
    for obra, o in obras.items():
        e = entrevistas.get(obra)
        o["entrevista"] = e[0] if e else None
        o["entrevista_cerrada"] = e[2] if e else None
        o["destinatario"] = ((e[1].get("destinatario") or {}).get("nombre") or None) if e else None
    return list(obras.values())


def texto_de_la_peticion(con, obra, numero):
    """`(existe, texto)` de la version: las palabras del lector que la originaron, o `None`
    si no nacio de una peticion (`SPEC-35` `RF-10`). La peticion se busca **de la obra**."""
    if not migraciones.tiene_tabla(con, "version_de_obra"):
        return False, None
    f = con.execute("SELECT peticion FROM version_de_obra WHERE obra = ? AND numero = ?",
                    (obra, numero)).fetchone()
    if f is None:
        return False, None
    if f[0] is None or not migraciones.tiene_tabla(con, "peticion_de_cambio"):
        return True, None
    t = con.execute("SELECT texto FROM peticion_de_cambio WHERE id = ? AND obra = ?",
                    (f[0], obra)).fetchone()
    return True, t[0] if t else None


def existe_la_obra(con, obra):
    """Montada, o todavia no (`F-206`): la obra nace con su entrevista y no entra en `obra`
    hasta que el Revisor aprueba el plan. Mientras, tiene entrevista, progreso o un
    lanzamiento, y la pagina de la generacion no puede ser un 404."""
    if con.execute("SELECT 1 FROM obra WHERE id = ?", (obra,)).fetchone() is not None:
        return True
    consultas = [("entrevista", "SELECT 1 FROM entrevista WHERE obra = ?"),
                 ("progreso_de_generacion",
                  "SELECT 1 FROM progreso_de_generacion WHERE obra = ?"),
                 ("trabajo", "SELECT 1 FROM trabajo WHERE tipo = 'generacion_regalo' AND "
                             "json_extract(carga, '$.obra') = ?")]
    return any(migraciones.tiene_tabla(con, tabla)
               and con.execute(sql, (obra,)).fetchone() is not None
               for tabla, sql in consultas)


def motivo_del_ultimo_lanzamiento(con, obra):
    """`SPEC-35` `RF-13`: el motivo del ultimo lanzamiento desde la web si fallo o se
    abandono; `None` si salio bien, sigue en curso o no hubo ninguno."""
    if not migraciones.tiene_tabla(con, "trabajo"):
        return None
    f = con.execute("SELECT estado, motivo_ultimo_fallo FROM trabajo WHERE tipo = "
                    "'generacion_regalo' AND json_extract(carga, '$.obra') = ? "
                    "ORDER BY rowid DESC LIMIT 1", (obra,)).fetchone()
    if f is None or f[0] not in ("fallido", "abandonado"):
        return None
    return f[1] or "el lanzamiento termino en {0} sin motivo guardado".format(f[0])


def numero_de_capitulos(con, obra):
    return con.execute("SELECT COUNT(DISTINCT orden) FROM capitulo WHERE obra = ?",
                       (obra,)).fetchone()[0]


def ultima_fase_por_capitulo(con, obra):
    """`{numero: {fase, motivo, desde}}` con la ultima fila de cada capitulo."""
    if not migraciones.tiene_tabla(con, "progreso_de_generacion"):
        return {}
    filas = con.execute(
        "SELECT capitulo, fase, motivo, desde FROM progreso_de_generacion p "
        "WHERE obra = ? AND capitulo IS NOT NULL AND id = (SELECT MAX(id) FROM "
        "progreso_de_generacion q WHERE q.obra = p.obra AND q.capitulo = p.capitulo)",
        (obra,)).fetchall()
    return {f[0]: {"fase": f[1], "motivo": f[2], "desde": f[3]} for f in filas}


def capitulo_actual(con, obra):
    """El numero del capitulo en el que esta la generacion, o `None` si no esta en ninguno:
    no ha empezado, esta en la planificacion o en la puerta, o ya se publico (`F-200`)."""
    if not migraciones.tiene_tabla(con, "progreso_de_generacion"):
        return None
    f = con.execute("SELECT capitulo FROM progreso_de_generacion WHERE obra = ? "
                    "ORDER BY id DESC LIMIT 1", (obra,)).fetchone()
    return f[0] if f else None


def escenas_del_capitulo(con, obra, capitulo):
    """Cada escena del capitulo con su `estado_de_escena`, en su orden."""
    return [{"id": f[0], "estado": f[1]} for f in con.execute(
        "SELECT id, estado FROM escena WHERE obra = ? AND capitulo = ? ORDER BY orden",
        (obra, capitulo))]


def ultima_fase(con, obra):
    """La ultima fila de progreso de la obra, o `None`: el estado de la estanteria."""
    if not migraciones.tiene_tabla(con, "progreso_de_generacion"):
        return None
    f = con.execute("SELECT fase FROM progreso_de_generacion WHERE obra = ? "
                    "ORDER BY id DESC LIMIT 1", (obra,)).fetchone()
    return f[0] if f else None


def capitulo_de_la_ultima_version(con, obra, numero):
    """El capitulo que ocupa `numero` en la ultima version **creada** de la obra
    (`SPEC-23`), o el que hay si la obra no tiene versiones.

    No es la vigente: la vigente es la ultima **publicada** (`commons/obra/vigente.py`). La
    generacion en vivo ensena la version que se esta escribiendo, que es la ultima creada."""
    if migraciones.tiene_tabla(con, "capitulo_de_version"):
        f = con.execute(
            "SELECT capitulo FROM capitulo_de_version WHERE obra = ? AND orden = ? AND "
            "numero = (SELECT MAX(numero) FROM capitulo_de_version WHERE obra = ?)",
            (obra, numero, obra)).fetchone()
        if f:
            return f[0]
    f = con.execute("SELECT id FROM capitulo WHERE obra = ? AND orden = ? ORDER BY rowid "
                    "DESC LIMIT 1", (obra, numero)).fetchone()
    return f[0] if f else None


def notas_aceptadas(con, obra, capitulo):
    """Las valoraciones del borrador **aceptado** de cada escena del capitulo. Una escena
    sin borrador aceptado no aporta nada: el capitulo no se ha cerrado (`RF-16`)."""
    if not migraciones.tiene_tabla(con, "valoracion_del_editor"):
        return []
    return [{"criterio": f[0], "nota": f[1], "justificacion": f[2], "instruccion": f[3]}
            for f in con.execute(
                "SELECT v.criterio, v.nota, v.justificacion, v.instruccion FROM escena e "
                "JOIN valoracion_del_editor v ON v.escena = e.id "
                "AND v.version = e.borrador_aceptado "
                "WHERE e.obra = ? AND e.capitulo = ? ORDER BY e.orden, v.rowid",
                (obra, capitulo))]


def ultima_generacion(con, obra=None):
    """El identificador de la ultima generacion anotada, de la obra o de toda la base."""
    if not migraciones.tiene_tabla(con, "gasto_de_delegacion"):
        return None
    sql = "SELECT generacion FROM gasto_de_delegacion WHERE generacion IS NOT NULL"
    args = ()
    if obra is not None:
        sql, args = sql + " AND obra = ?", (obra,)
    f = con.execute(sql + " ORDER BY id DESC LIMIT 1", args).fetchone()
    return f[0] if f else None


def gasto_de(con, obra=None, generacion=None):
    """`(usd, delegaciones, sin_coste)` de lo anotado; `usd` nulo si nada trajo coste.
    `SUM` de solo nulos es nulo en SQLite, que es justo lo que se quiere."""
    if not migraciones.tiene_tabla(con, "gasto_de_delegacion"):
        return None, 0, 0
    donde, args = [], []
    if obra is not None:
        donde.append("obra = ?")
        args.append(obra)
    if generacion is not None:
        donde.append("generacion = ?")
        args.append(generacion)
    sql = ("SELECT SUM(coste_usd), COUNT(*), SUM(coste_usd IS NULL) FROM gasto_de_delegacion"
           + (" WHERE " + " AND ".join(donde) if donde else ""))
    usd, n, nulos = con.execute(sql, args).fetchone()
    return usd, n, nulos or 0


# --- `SPEC-36`: el titulo en la generacion y la administracion -------------------------

def titulo_de(con, obra):
    """El titulo de la obra montada, o `None` si todavia no se ha montado."""
    f = con.execute("SELECT titulo FROM obra WHERE id = ?", (obra,)).fetchone()
    return f[0] if f else None


def hallazgos_abiertos_por_severidad(con, obra):
    """Los hallazgos `abierto` o `sin_veredicto` de las escenas de la obra, por severidad."""
    cuenta = {"bloqueante": 0, "mayor": 0, "menor": 0}
    if not migraciones.tiene_tabla(con, "hallazgo"):
        return cuenta
    for severidad, n in con.execute(
            "SELECT h.severidad, COUNT(*) FROM hallazgo h JOIN escena e ON e.id = h.escena "
            "WHERE e.obra = ? AND h.estado IN ('abierto', 'sin_veredicto') "
            "GROUP BY h.severidad", (obra,)):
        if severidad in cuenta:
            cuenta[severidad] = n
    return cuenta


def codigo_lean_de(con, obra):
    """El codigo de Lean del ultimo veredicto de la puerta de la obra, o `None`."""
    if not migraciones.tiene_tabla(con, "veredicto_de_publicacion"):
        return None
    f = con.execute("SELECT codigo_lean FROM veredicto_de_publicacion WHERE obra = ? "
                    "ORDER BY version DESC, ronda DESC LIMIT 1", (obra,)).fetchone()
    return f[0] if f else None


# --- `SPEC-41`: retirar de la estanteria ---------------------------------------------------

def _asegurar_retiradas(con):
    from app.commons.db.migraciones import RETIRADA_SQL
    with con:
        con.executescript(RETIRADA_SQL)


def retiradas(con):
    """`{obra: {motivo, quien, cuando}}` de las retiradas."""
    _asegurar_retiradas(con)
    return {f[0]: {"motivo": f[1], "quien": f[2], "cuando": f[3]} for f in con.execute(
        "SELECT obra, motivo, quien, cuando FROM retirada_de_la_estanteria")}


def retirar(con, obra, motivo, quien):
    _asegurar_retiradas(con)
    with con:
        con.execute("INSERT OR REPLACE INTO retirada_de_la_estanteria (obra, motivo, quien) "
                    "VALUES (?, ?, ?)", (obra, motivo, quien))


def devolver(con, obra):
    _asegurar_retiradas(con)
    with con:
        return con.execute("DELETE FROM retirada_de_la_estanteria WHERE obra = ?",
                           (obra,)).rowcount
