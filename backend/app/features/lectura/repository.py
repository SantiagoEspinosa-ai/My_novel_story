"""Las consultas de la lectura. Es el unico fichero de la feature que ve SQL (`A-01`).

Lee tablas que crean otras features (`obra` y `capitulo` de `brief/`; `escena`,
`borrador` y `hallazgo` de `escaleta/`) **por SQL y sin importarlas**: una feature no
importa de otra, y leer no es escribir.

Cada consulta que baja de la obra a sus capitulos filtra por **las dos** columnas cuando
las hay (`escena.obra` y `escena.capitulo`): con una obra por capitulo, preguntar solo por
una de las dos salia bien por accidente (Regla 11, `SPEC-22` `RF-37`).
"""

import json

from app.commons.obra import vigente as obra_vigente

HALLAZGO_ABIERTO = ("abierto", "sin_veredicto")


def obra(con, id_obra):
    f = con.execute("SELECT id, titulo, dedicatoria FROM obra WHERE id = ?",
                    (id_obra,)).fetchone()
    return None if f is None else {"id": f[0], "titulo": f[1], "dedicatoria": f[2]}


def capitulos(con, id_obra, version=None):
    """Los capitulos de la version `version` -la vigente si no se dice-, en su orden y con
    su posicion como `orden` (`SPEC-23` `D-2`). La version se lee por SQL de
    `capitulo_de_version`, como el manuscrito: con dos versiones, `capitulo` tiene el 2
    viejo y el nuevo, los dos con `orden` 2, y leer la tabla entera daba dos «Capitulo 2».

    Una obra sin versiones (anterior a `PLAN-23`) se lee como siempre: por
    `capitulo.orden`, que es el orden de lectura. Nunca por `id`."""
    if version is None:
        version = _version_vigente(con, id_obra)
    if version is not None:
        return [{"id": f[0], "orden": f[1], "estado": f[2], "obra": id_obra}
                for f in con.execute(
                    "SELECT c.id, v.orden, c.estado FROM capitulo_de_version v "
                    "JOIN capitulo c ON c.id = v.capitulo "
                    "WHERE v.obra = ? AND v.numero = ? ORDER BY v.orden",
                    (id_obra, version))]
    return [{"id": f[0], "orden": f[1], "estado": f[2], "obra": id_obra}
            for f in con.execute(
                "SELECT id, orden, estado FROM capitulo WHERE obra = ? ORDER BY orden",
                (id_obra,))]


def _version_vigente(con, id_obra):
    """La vigente, por la regla de `commons/obra/vigente.py`: la ultima **publicada**, no
    la ultima creada (`F-121`). Aqui habia una copia con `MAX(numero)` que llego de otra
    rama, y la web ensenaba como vigente la version que la cascada escribia (`F-150`).
    `None` si la obra no tiene versiones (o no hay tabla)."""
    if "numero" not in _columnas(con, "version_de_obra"):
        return None
    return obra_vigente.version_vigente(con, id_obra)


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


def hechos_que_usa(con, id_escena, id_obra):
    """Los hechos de `uso_de_hecho` de la escena, **de su obra**, uno por hecho y con
    todos los tipos de uso: el mismo `id` en dos obras son dos hechos (`SPEC-21`)."""
    return [{"id": f[0], "enunciado": f[1]} for f in con.execute(
        "SELECT DISTINCT h.id, h.enunciado FROM uso_de_hecho u "
        "JOIN hecho_canonico h ON h.id = u.hecho AND h.obra = ? "
        "WHERE u.escena = ? ORDER BY h.id", (id_obra, id_escena))]


def _columnas(con, tabla):
    return {f[1] for f in con.execute("PRAGMA table_info({0})".format(tabla))}


def personajes_de_la_obra(con, id_obra):
    """Los `id` de personaje que las escenas de la obra nombran (pov y presentes).

    `entidad` no tiene columna de obra (`F-64`), asi que no se listan sus filas: saldrian
    los personajes de todas las obras de la base.
    """
    ids = set()
    for pov, presentes in con.execute(
            "SELECT pov, personajes_presentes FROM escena WHERE obra = ?", (id_obra,)):
        if pov:
            ids.add(pov)
        if presentes:
            ids.update(json.loads(presentes))
    return sorted(ids)


def lugares_de_la_obra(con, id_obra):
    return [f[0] for f in con.execute(
        "SELECT DISTINCT lugar FROM escena WHERE obra = ? AND lugar IS NOT NULL "
        "ORDER BY lugar", (id_obra,))]


def canon_de_personaje(con, id_personaje):
    """`nombre_canonico` y `estado_vital` si la base los guarda; si no, `None`.

    La columna del nombre llega con `PLAN-27` E2. Hasta entonces no existe y el nombre
    viaja nulo: **no se finge** con el identificador.
    """
    vacio = {"nombre_canonico": None, "estado_vital": None}
    columnas = _columnas(con, "entidad")
    if not columnas:
        return vacio
    nombre = "nombre_canonico" if "nombre_canonico" in columnas else "NULL"
    f = con.execute("SELECT {0}, vital FROM entidad WHERE id = ?".format(nombre),
                    (id_personaje,)).fetchone()
    return vacio if f is None else {"nombre_canonico": f[0], "estado_vital": f[1]}


def canon_de_lugar(con, id_lugar):
    """`nombre` si la base lo guarda (`PLAN-27` E2); si no, `None`."""
    if "nombre" not in _columnas(con, "lugar"):
        return {"nombre": None}
    f = con.execute("SELECT nombre FROM lugar WHERE id = ?", (id_lugar,)).fetchone()
    return {"nombre": f[0] if f else None}


def progreso(con, id_obra):
    """El ultimo `ProgresoDeGeneracion` de la obra, con su ultima actividad y los segundos
    desde ella **calculados aqui, con el reloj de la base** (`SPEC-22` `RF-60`).

    La ultima actividad es lo mas reciente entre la entrada en la fase, la ultima traza de
    delegacion de una escena **de esta obra** y la ultima llamada a tool de la obra. Una
    tabla que no existe no aporta nada: no se inventa actividad.
    """
    if "fase" not in _columnas(con, "progreso_de_generacion"):
        return None
    f = con.execute(
        "SELECT fase, capitulo, total_de_capitulos, motivo, desde FROM progreso_de_generacion "
        "WHERE obra = ? ORDER BY id DESC LIMIT 1", (id_obra,)).fetchone()
    if f is None:
        return None
    marcas = [f[4]]
    if "cuando" in _columnas(con, "traza_de_delegacion"):
        marcas.append(con.execute(
            "SELECT MAX(t.cuando) FROM traza_de_delegacion t JOIN escena e ON e.id = t.escena "
            "WHERE e.obra = ?", (id_obra,)).fetchone()[0])
    if "cuando" in _columnas(con, "llamada_a_herramienta"):
        marcas.append(con.execute(
            "SELECT MAX(cuando) FROM llamada_a_herramienta WHERE obra = ?",
            (id_obra,)).fetchone()[0])
    ultima = max(m for m in marcas if m)
    segundos = con.execute(
        "SELECT CAST(ROUND((julianday('now') - julianday(?)) * 86400) AS INTEGER)",
        (ultima,)).fetchone()[0]
    return {"obra": id_obra, "fase": f[0], "capitulo": f[1], "total_de_capitulos": f[2],
            "motivo": f[3], "desde": f[4], "ultima_actividad": ultima,
            "segundos_desde_la_ultima_actividad": max(0, segundos)}


def titulos_de_capitulo(con, id_obra):
    """`SPEC-43` `RF-02`: `{capitulo: titulo}` del ultimo plan aprobado. El titulo es del plan
    (`Capitulo.titulo`, opcional): sin plan, o sin tabla, no hay ninguno, y no se inventa."""
    if not _columnas(con, "plan_de_obra"):
        return {}
    f = con.execute("SELECT plan FROM plan_de_obra WHERE obra = ? AND aprobado = 1 "
                    "ORDER BY version DESC LIMIT 1", (id_obra,)).fetchone()
    if f is None or not f[0]:
        return {}
    return {c.get("id"): c.get("titulo") for c in json.loads(f[0]).get("capitulos") or []}
