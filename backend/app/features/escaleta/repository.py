"""Persistencia de la escaleta, los borradores y los hallazgos.

`Borrador.version` crece **por escena y no globalmente**: la version 3 de la
escena 7 no tiene nada que ver con la version 3 de la escena 2, y numerarlas en
comun haria imposible leer "esta escena necesito cuatro intentos", que es una
de las señales que la otra rama identifico como mas utiles al interpretar un
informe.

`Escena.intentos` no se guarda aparte: es el numero de borradores. Un contador
que se lleva al lado de lo que cuenta se desincroniza en cuanto un camino de
codigo olvida incrementarlo.
"""

import json
import sqlite3

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad

SQL = """
CREATE TABLE IF NOT EXISTS escena (
    id                 TEXT PRIMARY KEY,
    obra               TEXT NOT NULL,
    orden              INTEGER NOT NULL,
    estado             TEXT NOT NULL,
    cambio_de_valor    TEXT NOT NULL,
    beats              TEXT NOT NULL,
    pov                TEXT NOT NULL,
    lugar              TEXT NOT NULL,
    longitud_objetivo  TEXT,
    borrador_aceptado  INTEGER,
    -- `SPEC-21` C-1. `capitulo` materializa la relacion `contiene`, que estaba
    -- en la tabla de relaciones y no existia en ninguna tabla. Las tres
    -- siguientes son `MomentoNarrativo`, atributo **obligatorio** de `Escena`
    -- desde el primer dia y hasta ahora inexpresable. Nacen NULL porque las
    -- escaletas anteriores no los traen, y un NULL se puede ver; un valor por
    -- defecto inventado, no.
    capitulo             TEXT,
    t_fabula             TEXT,
    t_discurso           INTEGER,
    duracion_ficcional   INTEGER,
    personajes_presentes TEXT
);
CREATE INDEX IF NOT EXISTS idx_escena_capitulo ON escena (capitulo, orden);
CREATE TABLE IF NOT EXISTS borrador (
    escena      TEXT NOT NULL,
    version     INTEGER NOT NULL,
    texto       TEXT NOT NULL,
    modelo      TEXT,
    prompt_hash TEXT,
    PRIMARY KEY (escena, version)
);
CREATE TABLE IF NOT EXISTS hecho_canonico (
    id                      TEXT PRIMARY KEY,
    obra                    TEXT NOT NULL,
    enunciado               TEXT NOT NULL,
    durabilidad             TEXT NOT NULL DEFAULT 'permanente',
    escena_de_establecimiento TEXT,
    previsto_en             TEXT
);
CREATE TABLE IF NOT EXISTS hallazgo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invariante  TEXT NOT NULL,
    verificador TEXT NOT NULL,
    escena      TEXT NOT NULL,
    severidad   TEXT NOT NULL,
    estado      TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    motivo_de_cierre TEXT
);
"""

CUENTAN_COMO_ABIERTOS = (EH.ABIERTO.value, EH.SIN_VEREDICTO.value)


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar_escaleta(con, obra, escenas):
    asegurar_tablas(con)
    with con:
        for e in escenas:
            presentes = e.get("personajes_presentes")
            con.execute(
                "INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, "
                "beats, pov, lugar, longitud_objetivo, capitulo, t_fabula, "
                "t_discurso, duracion_ficcional, personajes_presentes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (e["id"], obra, e["orden"], EE.PLANIFICADA.value,
                 json.dumps(e["cambio_de_valor"]), json.dumps(e["beats"]),
                 e.get("pov"), e.get("lugar"),
                 json.dumps(e.get("longitud_objetivo")),
                 e.get("capitulo"), e.get("t_fabula"), e.get("t_discurso"),
                 e.get("duracion_ficcional"),
                 json.dumps(presentes) if presentes is not None else None),
            )


def declarar_hechos(con, obra, hechos):
    """`SPEC-15`: los `HechoCanonico` los declara el plan, no el texto.

    `escena_de_establecimiento` queda **vacia** hasta que una escena lo
    establezca: es opcional desde `SPEC-15` y significa *donde lo establece el
    texto*, no *donde nacio*. Un hecho declarado y nunca establecido es un
    defecto nombrable, y antes ni siquiera se podia escribir.
    """
    asegurar_tablas(con)
    with con:
        for h in hechos:
            con.execute(
                "INSERT OR REPLACE INTO hecho_canonico (id, obra, enunciado, "
                "durabilidad, previsto_en) VALUES (?, ?, ?, ?, ?)",
                (h["id"], obra, h["enunciado"], h.get("durabilidad", "permanente"),
                 h.get("previsto_en")))


def hechos_declarados(con, obra):
    """Los hechos que el plan declaro. **Esto es lo que va al prompt.**

    Derivar la lista del registro de conocimiento creo un punto muerto: no
    habia hechos hasta que alguien los sabia, y nadie podia saberlos hasta que
    existian (`F-29`). Que hechos existen lo declara el plan; quien los sabe lo
    comprueba `INV-03`.
    """
    asegurar_tablas(con)
    return [{"id": f[0], "enunciado": f[1], "establecido_en": f[2]}
            for f in con.execute(
                "SELECT id, enunciado, escena_de_establecimiento FROM hecho_canonico "
                "WHERE obra = ? ORDER BY id", (obra,))]


def establecer_hecho(con, hecho, escena):
    """Marca donde el texto lo establece. Solo la primera vez."""
    with con:
        con.execute("UPDATE hecho_canonico SET escena_de_establecimiento = ? "
                    "WHERE id = ? AND escena_de_establecimiento IS NULL",
                    (escena, hecho))


# Las columnas de una escena y como se reconstruye la fila viven en un solo
# sitio. Antes estaban copiadas en `escenas_de` y en `escena`, y al añadir las
# cinco de `SPEC-21` habria habido que acertar dos veces: la copia que alguien
# olvide es justo la que lea quien pregunte por el capitulo.
_COLUMNAS = ("id, orden, estado, cambio_de_valor, beats, longitud_objetivo, "
             "borrador_aceptado, pov, lugar, capitulo, t_fabula, t_discurso, "
             "duracion_ficcional, personajes_presentes")


def _fila(f):
    return {"id": f[0], "orden": f[1], "estado": f[2],
            "cambio_de_valor": json.loads(f[3]), "beats": json.loads(f[4]),
            "longitud_objetivo": json.loads(f[5]) if f[5] else None,
            "borrador_aceptado": f[6], "pov": f[7], "lugar": f[8],
            # `capitulo` vacio se devuelve vacio. Sustituirlo por la obra daria
            # una respuesta con forma de capitulo que no es un capitulo.
            "capitulo": f[9], "t_fabula": f[10], "t_discurso": f[11],
            "duracion_ficcional": f[12],
            "personajes_presentes": json.loads(f[13]) if f[13] else None}


def escenas_de(con, obra):
    return [_fila(f) for f in con.execute(
        "SELECT {0} FROM escena WHERE obra = ? ORDER BY orden".format(_COLUMNAS),
        (obra,))]


def escenas_de_capitulo(con, id_capitulo):
    """Las escenas de un capitulo, filtrando **por capitulo**.

    `orquestacion/router.py` lo resolvia llamando a `escenas_de`, que filtra
    por obra: con un solo capitulo por obra daba el resultado correcto por
    accidente, y con dos, cerrar el primero miraba las escenas del segundo.
    """
    return [_fila(f) for f in con.execute(
        "SELECT {0} FROM escena WHERE capitulo = ? ORDER BY orden".format(_COLUMNAS),
        (id_capitulo,))]


def escena(con, id_escena):
    for f in con.execute(
            "SELECT {0} FROM escena WHERE id = ?".format(_COLUMNAS), (id_escena,)):
        return _fila(f)
    return None


def guardar_borrador(con, escena, texto, modelo, prompt_hash):
    """Devuelve la version, que crece por escena."""
    with con:
        fila = con.execute("SELECT MAX(version) FROM borrador WHERE escena = ?",
                           (escena,)).fetchone()
        version = (fila[0] or 0) + 1
        con.execute("INSERT INTO borrador VALUES (?, ?, ?, ?, ?)",
                    (escena, version, texto, modelo, prompt_hash))
        con.execute("UPDATE escena SET estado = ? WHERE id = ?",
                    (EE.GENERADA.value, escena))
    return version


def marcar_consolidada(con, escena):
    """`aceptada` -> `consolidada`, la transicion del Consolidador.

    Existia en la tabla de `Docs/architecture.md` y **no la aplicaba nadie**:
    las escenas se quedaban en `generada` para siempre, asi que la puerta de
    capitulo veia un capitulo con tres escenas a medias y no podia cerrarse
    nunca. El delta se aplicaba igual, de modo que el estado del mundo era
    correcto y el de la escena mentia.
    """
    with con:
        con.execute("UPDATE escena SET estado = ? WHERE id = ?",
                    (EE.CONSOLIDADA.value, escena))


def rendir_escena(con, escena, version):
    """`aceptada_por_rendicion`, y **no** `aceptada` (`RF-24`).

    Son dos estados y no uno porque quien lea el manuscrito tiene que poder
    distinguir una escena limpia de una que paso con hallazgos abiertos.
    `borrador_aceptado` dice **cual** de los intentos se eligio, que es la otra
    mitad: sin eso, "se eligio el menos malo" no es comprobable.
    """
    with con:
        con.execute("UPDATE escena SET estado = ?, borrador_aceptado = ? "
                    "WHERE id = ?", (EE.ACEPTADA_POR_RENDICION.value, version, escena))


def intentos_de(con, escena):
    """No hay contador aparte: es cuantos borradores hay."""
    return con.execute("SELECT COUNT(*) FROM borrador WHERE escena = ?",
                       (escena,)).fetchone()[0]


# Los dos estados en los que un hallazgo deja de contar. `sin_veredicto` no
# esta: significa que **falta el juicio**, no que se haya emitido.
DE_CIERRE = (EH.RESUELTO, EH.DESCARTADO)


def cerrar_hallazgo(con, id_hallazgo, estado, motivo: str):
    """`resuelto` o `descartado`, **con motivo**.

    Los dos estados existian en `estado_de_hallazgo` desde el primer dia y
    **ninguna funcion los escribia** (`F-38`): un hallazgo nacia abierto y se
    quedaba abierto para siempre, asi que aunque alguien arreglara la causa el
    capitulo no podia cerrarse nunca.

    **Resuelto y descartado no son lo mismo** y por eso son dos valores:
    resuelto es *se arreglo*, descartado es *se decidio que no aplica*. Si se
    confundieran, el recuento por invariante mezclaria las veces que la regla
    acerto con las que se equivoco, y ese recuento es lo unico que dice si una
    regla sirve.

    El motivo es obligatorio porque un hallazgo cerrado sin motivo es
    indistinguible de uno que alguien cerro para que dejara de molestar.
    """
    if estado not in DE_CIERRE:
        raise ValueError(
            "`{0}` no es un estado de cierre. Solo {1}: `sin_veredicto` "
            "significa que falta el juicio, no que se haya emitido".format(
                estado, " y ".join(str(e) for e in DE_CIERRE)))
    if not (motivo or "").strip():
        raise ValueError(
            "cerrar un hallazgo exige un motivo: sin el, no se distingue de "
            "uno que se cerro para que dejara de molestar")
    with con:
        con.execute("UPDATE hallazgo SET estado = ?, motivo_de_cierre = ? "
                    "WHERE id = ?", (str(estado), motivo, id_hallazgo))


def guardar_hallazgo(con, invariante, verificador, escena, severidad, estado, descripcion):
    with con:
        con.execute(
            "INSERT INTO hallazgo (invariante, verificador, escena, severidad, "
            "estado, descripcion) VALUES (?, ?, ?, ?, ?, ?)",
            (invariante, verificador, escena, str(severidad), str(estado), descripcion))


def hallazgos_abiertos(con, escena):
    """Devuelve `severidad` y `estado` como **miembros de su enumeracion**.

    La primera version los devolvia como cadenas, y eso abrio la puerta de
    capitulo en silencio: `impide_cerrar_el_capitulo` compara con `is` contra
    `Severidad.MAYOR`, y `"mayor" is Severidad.MAYOR` es falso. Un `mayor`
    leido de la base **no bloqueaba nada**, y las pruebas unitarias de la puerta
    no lo veian porque le pasaban miembros directamente.

    La leccion es de frontera: si los modelos Pydantic son la frontera de
    validacion de la API, **la deserializacion es la frontera de validacion de
    la base**. Un dato que entra al dominio entra con el tipo del dominio o no
    entra.
    """
    filas = con.execute(
        "SELECT invariante, verificador, severidad, estado, descripcion, id "
        "FROM hallazgo WHERE escena = ? AND estado IN (?, ?)",
        (escena, CUENTAN_COMO_ABIERTOS[0], CUENTAN_COMO_ABIERTOS[1]))
    return [{"invariante": f[0], "verificador": f[1],
             "severidad": Severidad(f[2]), "estado": EH(f[3]),
             "descripcion": f[4], "id": f[5]} for f in filas]


def aceptar_borrador(con, escena, version, rindiendose):
    estado = EE.ACEPTADA_POR_RENDICION if rindiendose else EE.ACEPTADA
    with con:
        con.execute("UPDATE escena SET estado = ?, borrador_aceptado = ? WHERE id = ?",
                    (estado.value, version, escena))
