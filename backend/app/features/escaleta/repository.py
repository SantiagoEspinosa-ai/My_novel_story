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
    borrador_aceptado  INTEGER
);
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
    descripcion TEXT NOT NULL
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
            con.execute(
                "INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, "
                "beats, pov, lugar, longitud_objetivo) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (e["id"], obra, e["orden"], EE.PLANIFICADA.value,
                 json.dumps(e["cambio_de_valor"]), json.dumps(e["beats"]),
                 e.get("pov"), e.get("lugar"),
                 json.dumps(e.get("longitud_objetivo"))),
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


def escenas_de(con, obra):
    filas = con.execute(
        "SELECT id, orden, estado, cambio_de_valor, beats, longitud_objetivo, "
        "borrador_aceptado, pov, lugar FROM escena WHERE obra = ? ORDER BY orden",
        (obra,))
    return [{"id": f[0], "orden": f[1], "estado": f[2],
             "cambio_de_valor": json.loads(f[3]), "beats": json.loads(f[4]),
             "longitud_objetivo": json.loads(f[5]) if f[5] else None,
             "borrador_aceptado": f[6], "pov": f[7], "lugar": f[8]}
            for f in filas]


def escena(con, id_escena):
    for e in con.execute(
            "SELECT id, orden, estado, cambio_de_valor, beats, longitud_objetivo, "
            "borrador_aceptado, pov, lugar FROM escena WHERE id = ?", (id_escena,)):
        return {"id": e[0], "orden": e[1], "estado": e[2],
                "cambio_de_valor": json.loads(e[3]), "beats": json.loads(e[4]),
                "longitud_objetivo": json.loads(e[5]) if e[5] else None,
                "borrador_aceptado": e[6], "pov": e[7], "lugar": e[8]}
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
        "SELECT invariante, verificador, severidad, estado, descripcion FROM hallazgo "
        "WHERE escena = ? AND estado IN (?, ?)",
        (escena, CUENTAN_COMO_ABIERTOS[0], CUENTAN_COMO_ABIERTOS[1]))
    return [{"invariante": f[0], "verificador": f[1],
             "severidad": Severidad(f[2]), "estado": EH(f[3]),
             "descripcion": f[4]} for f in filas]


def aceptar_borrador(con, escena, version, rindiendose):
    estado = EE.ACEPTADA_POR_RENDICION if rindiendose else EE.ACEPTADA
    with con:
        con.execute("UPDATE escena SET estado = ?, borrador_aceptado = ? WHERE id = ?",
                    (estado.value, version, escena))
