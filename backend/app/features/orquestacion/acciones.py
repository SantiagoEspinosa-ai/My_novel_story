"""Publicar y reanudar una novela desde la web (`SPEC-39`, `PLAN-39`).

Vive en `orquestacion/` porque compone: la puerta, Lean, la ficha de la entrevista, el
progreso y el gasto. **Todo lo decide aqui el backend** (`RF-07`): si se puede, por que no,
desde donde y cuanto; la web lo ensena.

PUBLICAR ES UNA RONDA
---------------------
`publicacion.evaluar`, no `publicar`: una ronda de la puerta con Lean incluido y **sin
reescribir nada** (fuera de `SPEC-39`). Si no pasa, se devuelve cada condicion que fallo. La
ronda juzga la obra entera (`INV-27`), que es una delegacion del Editor: por eso se avisa del
gasto antes, y por eso sin Lean no se llega a llamar a nadie (`RF-03`).
"""

from app.commons import config
from app.commons.trabajos import cola
from app.features.auditoria import lean as modulo_lean
from app.features.brief import repository as brief
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import regalo

TIPO_DE_PUBLICACION = "publicacion_regalo"
_TERMINADAS = ("consolidada", "aceptada_por_rendicion")
_SIN_TERMINAR = ("en_cola", "en_curso", "esperando_presupuesto")

SIN_LEAN = ("Falta Lean (lake) en esta máquina. La puerta de publicación lo usa para "
            "comprobar la cronología de la novela (SPEC-30), y sin él ninguna versión se "
            "publica. Se instala con elan (https://elan.lean-lang.org) y se busca en "
            "HARNESS_LAKE, ELAN_HOME, el PATH y ~/.elan/bin.")


def lake_disponible():
    """`(True, None)` o `(False, motivo)`. Sin lanzar Lean: solo se busca."""
    try:
        modulo_lean.localizar_lake()
    except modulo_lean.LeanNoDisponible:
        return False, SIN_LEAN
    return True, None


def _version_que_se_escribe(con, obra):
    """La ultima version creada, que es la que se escribe o se escribio; `None` sin versiones."""
    try:
        f = con.execute("SELECT MAX(numero) FROM version_de_obra WHERE obra = ?", (obra,)).fetchone()
    except Exception:  # noqa: BLE001 — una base sin la tabla de versiones
        return None
    return f[0] if f else None


def _capitulos(con, obra, numero):
    if numero is not None:
        ids = brief.capitulos_de_version(con, obra, numero)
        if ids:
            return ids
    return [f[0] for f in con.execute("SELECT id FROM capitulo WHERE obra = ? ORDER BY orden",
                                      (obra,))]


def _terminados(con, obra, numero):
    """`[bool]` por posicion: si todas las escenas del capitulo estan terminadas."""
    salida = []
    for cap in _capitulos(con, obra, numero):
        escenas = escaleta.escenas_de_capitulo(con, cap, obra)
        salida.append(bool(escenas) and all(e["estado"] in _TERMINADAS for e in escenas))
    return salida


def _publicada(con, obra, numero):
    try:
        return con.execute("SELECT 1 FROM veredicto_de_publicacion WHERE obra = ? AND version = ? "
                           "AND publica = 1", (obra, numero or 1)).fetchone() is not None
    except Exception:  # noqa: BLE001 — sin la tabla, nunca paso por la puerta
        return False


def en_curso(con, obra):
    """Una generacion o una publicacion de la obra sin terminar."""
    if regalo.en_curso(con, obra):
        return True
    cola.asegurar_tabla(con)
    marcas = ",".join("?" * len(_SIN_TERMINAR))
    return con.execute("SELECT 1 FROM trabajo WHERE tipo = ? AND json_extract(carga, '$.obra') = ? "
                       "AND estado IN ({0})".format(marcas),
                       (TIPO_DE_PUBLICACION, obra) + _SIN_TERMINAR).fetchone() is not None


def _ficha(con, obra):
    try:
        return regalo.ficha_cerrada(con, obra)
    except regalo.NoSePuedeLanzar:
        return None


def _fase(con, obra):
    try:
        f = con.execute("SELECT fase FROM progreso_de_generacion WHERE obra = ? ORDER BY id DESC "
                        "LIMIT 1", (obra,)).fetchone()
    except Exception:  # noqa: BLE001
        return None
    return f[0] if f else None


def _coste_medio_del_editor(con):
    f = con.execute("SELECT AVG(coste_usd), COUNT(coste_usd) FROM gasto_de_delegacion WHERE "
                    "agente = 'editor' AND coste_usd IS NOT NULL").fetchone()
    return (f[0], f[1]) if f and f[1] else (None, 0)


def _coste_por_capitulo(con, obra):
    """Lo medido en esta novela por capitulo (con la atribucion de `SPEC-37`) o, si no hay,
    la referencia de la novela de ejemplo entre sus diez capitulos."""
    from app.features.regalo import historia
    d = historia._datos(con, obra)
    medidos = []
    if d is not None:
        for clave, filas in d["cubos"].items():
            if clave[0] == "capitulo":
                usd = [g["usd"] for g in filas if g["usd"] is not None]
                if usd:
                    medidos.append(sum(usd))
    if medidos:
        return (sum(medidos) / len(medidos),
                "el coste del único capítulo medido de esta novela" if len(medidos) == 1
                else "la media de los {0} capítulos medidos de esta novela".format(len(medidos)))
    ref = config.REFERENCIA_NOVELA_DE_EJEMPLO
    return (ref["usd"] / 10, "la referencia de la novela de ejemplo ({0:.2f} USD en 10 "
                             "capítulos): esta novela no tiene capítulos medidos".format(ref["usd"]))


def _existe(con, obra):
    """`SPEC-44` `RF-02`: la obra no se monta hasta que hay plan, asi que una novela que solo
    tiene entrevista existe igual."""
    if con.execute("SELECT 1 FROM obra WHERE id = ?", (obra,)).fetchone() is not None:
        return True
    try:
        return con.execute("SELECT 1 FROM entrevista WHERE obra = ?", (obra,)).fetchone() is not None
    except Exception:  # noqa: BLE001 — una base sin entrevistas
        return False


def _coste_de_una_novela(con):
    """`SPEC-44` `RF-03`: la media de lo gastado por las novelas publicadas en esta base o, sin
    ninguna, la referencia de la novela de ejemplo. Con su fuente dicha."""
    try:
        filas = con.execute(
            "SELECT g.obra, SUM(g.coste_usd) FROM gasto_de_delegacion g WHERE g.coste_usd IS NOT "
            "NULL AND g.obra IN (SELECT p.obra FROM progreso_de_generacion p WHERE p.id = (SELECT "
            "MAX(q.id) FROM progreso_de_generacion q WHERE q.obra = p.obra) AND p.fase = "
            "'publicada') GROUP BY g.obra").fetchall()
    except Exception:  # noqa: BLE001
        filas = []
    if filas:
        media = sum(f[1] for f in filas) / len(filas)
        return media, "la media de las {0} novelas publicadas en esta base".format(len(filas))             if len(filas) > 1 else "la única novela publicada en esta base"
    ref = config.REFERENCIA_NOVELA_DE_EJEMPLO
    return ref["usd"], "la referencia de la novela de ejemplo: no hay novelas publicadas en esta base"


def acciones(con, obra, sistema, lean, techo):
    """`{publicar, reanudar, generar}`, o `None` si la obra no existe. `lean` es `(disponible,
    motivo)`."""
    if not _existe(con, obra):
        return None
    numero = _version_que_se_escribe(con, obra)
    terminados = _terminados(con, obra, numero)
    todos = bool(terminados) and all(terminados)
    ocupada = en_curso(con, obra)
    ficha = _ficha(con, obra)
    fase = _fase(con, obra)
    lean_ok, lean_motivo = lean
    media_editor, medidas_editor = _coste_medio_del_editor(con)

    motivo_p = None
    if ocupada:
        motivo_p = "hay una generación o una publicación de esta novela en curso"
    elif not todos:
        motivo_p = "faltan capítulos por escribir: desde el {0}".format(terminados.index(False) + 1
                                                                      if terminados else 1)
    elif _publicada(con, obra, numero):
        motivo_p = "la versión {0} ya está publicada".format(numero or 1)
    elif ficha is None:
        motivo_p = "no hay una ficha cerrada de esta novela: la puerta la necesita"
    elif not lean_ok:
        motivo_p = lean_motivo
    elif not sistema.modelos.editor:
        motivo_p = "config/sistema.json no declara el modelo del Editor"

    usd, _, _ = regalo.lecturas.gasto_de(con)
    alcanzado = usd is not None and usd >= techo
    desde = None if todos or not terminados else terminados.index(False) + 1
    faltan = terminados.count(False)
    motivo_r = None
    if ocupada:
        motivo_r = "hay una generación o una publicación de esta novela en curso"
    elif todos:
        motivo_r = "todos los capítulos están escritos: si falta publicarla, usa «Publicar»"
    elif fase != "parada":
        motivo_r = "la novela no está parada"
    elif ficha is None:
        motivo_r = "no hay una ficha cerrada de esta novela"
    elif alcanzado:
        motivo_r = "lo gastado en esta base ya alcanza el techo de {0:g} USD".format(techo)
    coste, fuente = _coste_por_capitulo(con, obra) if desde else (None, None)

    # `SPEC-44` `RF-01`: generar es para la que nunca se lanzo; la lanzada se reanuda.
    motivo_g = None
    if ocupada:
        motivo_g = "hay una generación o una publicación de esta novela en curso"
    elif fase is not None:
        motivo_g = ("ya se lanzó: si está parada, usa «Reanudar»" if fase == "parada"
                    else "ya se lanzó (fase: {0})".format(fase))
    elif ficha is None:
        motivo_g = "la entrevista no está cerrada: hay que terminarla antes de generar"
    elif alcanzado:
        motivo_g = "lo gastado en esta base ya alcanza el techo de {0:g} USD".format(techo)
    coste_g, fuente_g = _coste_de_una_novela(con)
    return {
        "generar": {"posible": motivo_g is None, "motivo": motivo_g, "estimacion_usd": coste_g,
                    "fuente": fuente_g},
        "publicar": {"posible": motivo_p is None, "motivo": motivo_p, "version": numero or 1,
                     "lean_disponible": lean_ok, "lean_motivo": lean_motivo,
                     "coste_medio_del_editor": media_editor,
                     "delegaciones_medidas_del_editor": medidas_editor},
        "reanudar": {"posible": motivo_r is None, "motivo": motivo_r, "desde_capitulo": desde,
                     "faltan": faltan, "coste_por_capitulo": coste, "fuente": fuente,
                     "estimacion_usd": None if coste is None else coste * faltan},
    }


def publicar_una_ronda(con, obra, ficha, lean, juez, sistema):
    """Una ronda de la puerta (`RF-01`). Si publica, la obra queda publicada."""
    from app.features.orquestacion import novela, progreso
    from app.features.orquestacion import publicacion
    numero = _version_que_se_escribe(con, obra)
    vetadas, _ = novela.vetadas_de_la_version(con, obra, ficha, sistema, numero)
    e = publicacion.evaluar(con, obra, ficha, lean, juez, vetadas,
                            umbral_nombre=sistema.edicion.umbral_repeticion_nombre,
                            longitud_frase=sistema.edicion.longitud_frase_repetida,
                            version=numero)
    if e.decision.publica:
        progreso.fijar(con, obra, "publicada")
    return {"publicada": e.decision.publica, "ronda": e.ronda, "version": numero or 1,
            "condiciones": [{"invariante": c.invariante, "capitulo": c.capitulo,
                             "detalle": c.detalle} for c in e.decision.condiciones],
            "lean": {"codigo": e.lean.codigo, "detalle": e.lean.detalle or None}}
