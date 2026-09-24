"""El libro de gasto de la evaluacion: `gasto_de_evaluacion` (`SPEC-31` `RF-06`, `PLAN-31` E5).

Una fila por **tramo** de una ejecucion: la entrevista, el plan, cada capitulo y el
cierre (la puerta de publicacion, con el juicio de obra y sus reescrituras). Se anota al
terminar cada tramo, asi que lo gastado sobrevive a una caida a mitad de novela; y el
techo se comprueba contra estas filas, que son lo **gastado**, nunca contra una prevision.

UN TRAMO SIN COSTE NO VALE CERO
-------------------------------
`usd` es `NULL` cuando ninguna delegacion del tramo trajo coste: un cero se leeria como un
tramo gratis. Con alguna sin coste, el total es un suelo y `texto_del_total` lo dice.

La tabla la crea esta feature (`PLAN-31`: sin migraciones de tablas existentes).
"""

import sqlite3
from dataclasses import dataclass

PASADAS = ("antes", "despues")
"""Las dos pasadas de la iteracion de tuning (`SPEC-31` `RF-03`)."""

TRAMOS_SIN_CAPITULO = ("entrevista", "plan", "cierre")

SQL = """
CREATE TABLE IF NOT EXISTS gasto_de_evaluacion (
    ejecucion    TEXT NOT NULL,
    brief        TEXT NOT NULL,
    pasada       TEXT NOT NULL,
    capitulo     TEXT NOT NULL,
    usd          REAL,
    delegaciones INTEGER NOT NULL,
    sin_coste    INTEGER NOT NULL,
    version_del_escritor TEXT,
    cuando       TEXT NOT NULL DEFAULT (datetime('now')),
    -- `PLAN-31` E10: la obra que escribio la ejecucion (en un guion la pone la
    -- entrevista) y la base donde vive, que no es la del libro: `F-100`.
    obra         TEXT,
    base         TEXT,
    PRIMARY KEY (ejecucion, capitulo)
);
"""


def asegurar_tablas(con: sqlite3.Connection):
    from app.commons.db.migraciones import anadir_columnas
    with con:
        # Un libro creado con el esquema de E5 gana las dos columnas de E10. La tabla no
        # esta en la cadena de migraciones: la crea esta feature.
        anadir_columnas(con, "gasto_de_evaluacion", {"obra": "TEXT", "base": "TEXT"})
        con.executescript(SQL)


def anotar(con, ejecucion, brief, pasada, capitulo, usd, delegaciones, sin_coste,
           version_del_escritor=None, obra=None, base=None):
    """`capitulo` es el numero del capitulo, o `entrevista`, `plan` o `cierre`.

    `F-119`: anotar otra vez el mismo tramo **suma**. Antes lo sustituia, y al reanudar
    la novela de ejemplo los capitulos 1 a 8 -saltados, con coste 0- pisaron 11,9010 USD
    medidos. Cada anotacion es gasto nuevo: el intento parado de un capitulo y el que lo
    termina son dos. Lo que no gasto nada no se anota (`evaluar.py`)."""
    if pasada not in PASADAS:
        raise ValueError("la pasada es {0}, no «{1}»".format(" o ".join(PASADAS), pasada))
    capitulo = str(capitulo)
    if capitulo not in TRAMOS_SIN_CAPITULO and not capitulo.isdigit():
        raise ValueError("el tramo es un numero de capitulo o uno de {0}, no «{1}»".format(
            ", ".join(TRAMOS_SIN_CAPITULO), capitulo))
    medido = usd if delegaciones > sin_coste else None
    asegurar_tablas(con)
    with con:
        # Un `usd` a NULL es «sin medir», no cero: sumarlo con otro da el otro, y dos
        # nulos siguen siendo nulo. `sin_coste` y `delegaciones` dicen si es un suelo.
        con.execute(
            "INSERT INTO gasto_de_evaluacion (ejecucion, brief, pasada, capitulo, "
            "usd, delegaciones, sin_coste, version_del_escritor, obra, base) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(ejecucion, capitulo) DO UPDATE SET "
            "usd = CASE WHEN usd IS NULL AND excluded.usd IS NULL THEN NULL "
            "           ELSE COALESCE(usd, 0) + COALESCE(excluded.usd, 0) END, "
            "delegaciones = delegaciones + excluded.delegaciones, "
            "sin_coste = sin_coste + excluded.sin_coste, "
            "version_del_escritor = excluded.version_del_escritor, "
            "cuando = datetime('now')",
            (ejecucion, brief, pasada, capitulo, medido, delegaciones, sin_coste,
             version_del_escritor, obra, base))


def filas(con, ejecucion=None) -> list:
    asegurar_tablas(con)
    sql = ("SELECT ejecucion, brief, pasada, capitulo, usd, delegaciones, sin_coste, "
           "version_del_escritor, cuando, obra, base FROM gasto_de_evaluacion")
    args = ()
    if ejecucion is not None:
        sql += " WHERE ejecucion = ?"
        args = (ejecucion,)
    claves = ("ejecucion", "brief", "pasada", "capitulo", "usd", "delegaciones",
              "sin_coste", "version_del_escritor", "cuando", "obra", "base")
    return [dict(zip(claves, f)) for f in con.execute(sql + " ORDER BY rowid", args)]


@dataclass(frozen=True)
class Total:
    usd: float
    delegaciones: int
    sin_coste: int

    @property
    def es_suelo(self) -> bool:
        return self.sin_coste > 0

    @property
    def medido(self) -> bool:
        return self.delegaciones > self.sin_coste


def gastado(con, ejecucion=None) -> Total:
    fs = filas(con, ejecucion)
    return Total(usd=sum(f["usd"] for f in fs if f["usd"] is not None),
                 delegaciones=sum(f["delegaciones"] for f in fs),
                 sin_coste=sum(f["sin_coste"] for f in fs))


def texto_del_total(total: Total) -> str:
    if not total.medido:
        return "sin medir: {0} delegaciones, ninguna con coste".format(total.delegaciones) \
            if total.delegaciones else "sin medir: ninguna delegacion anotada"
    texto = "{0:.4f} USD en {1} delegaciones".format(total.usd, total.delegaciones)
    if total.es_suelo:
        texto += " (SUELO: {0} delegaciones sin coste)".format(total.sin_coste)
    return texto


def puede_empezar(con, techo) -> bool:
    """`RF-06`: con lo gastado en el techo o por encima, no empieza nada. Lo gastado es un
    suelo si hay delegaciones sin coste, asi que esta comprobacion puede dejar empezar una
    ejecucion que en realidad ya no cabe: sesga hacia gastar de mas, y por eso el guion
    enseña el total con su marca de suelo antes de pedir el si."""
    return gastado(con).usd < techo


def mayor_coste_de_novela_completa(con):
    """El mayor total medido de una ejecucion que llego al cierre, o `None`. Una
    ejecucion sin `cierre` no es una novela completa, y su coste no dice lo que cuesta
    una."""
    completas = {f["ejecucion"] for f in filas(con) if f["capitulo"] == "cierre"}
    totales = [gastado(con, e) for e in completas]
    medidos = [t.usd for t in totales if t.medido]
    return max(medidos) if medidos else None


def ejecuciones(con) -> list:
    """Una por ejecucion, en el orden en que se anotaron, con su obra y su base."""
    vistas = {}
    for f in filas(con):
        e = vistas.setdefault(f["ejecucion"], {k: f[k] for k in (
            "ejecucion", "brief", "pasada", "obra", "base", "version_del_escritor")})
        for k in ("obra", "base", "version_del_escritor"):
            e[k] = e[k] or f[k]
    return list(vistas.values())


def siguiente_ejecucion(con, brief, pasada) -> str:
    previas = [e for e in ejecuciones(con) if e["brief"] == brief and e["pasada"] == pasada]
    return "{0}-{1}-{2}".format(brief, pasada, len(previas) + 1)
