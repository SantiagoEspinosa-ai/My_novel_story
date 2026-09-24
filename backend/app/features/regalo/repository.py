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


def existe_la_obra(con, obra):
    return con.execute("SELECT 1 FROM obra WHERE id = ?", (obra,)).fetchone() is not None


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


def ultima_fase(con, obra):
    """La ultima fila de progreso de la obra, o `None`: el estado de la estanteria."""
    if not migraciones.tiene_tabla(con, "progreso_de_generacion"):
        return None
    f = con.execute("SELECT fase FROM progreso_de_generacion WHERE obra = ? "
                    "ORDER BY id DESC LIMIT 1", (obra,)).fetchone()
    return f[0] if f else None


def capitulo_vigente(con, obra, numero):
    """El capitulo que ocupa `numero` en la ultima version de la obra (`SPEC-23`), o el
    que hay si la obra no tiene versiones."""
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
