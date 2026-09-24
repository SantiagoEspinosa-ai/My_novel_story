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
    PRIMARY KEY (ejecucion, capitulo)
);
"""


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def anotar(con, ejecucion, brief, pasada, capitulo, usd, delegaciones, sin_coste,
           version_del_escritor=None):
    """`capitulo` es el numero del capitulo, o `entrevista`, `plan` o `cierre`. Anotar
    otra vez el mismo tramo lo sustituye: relanzar no suma dos veces lo mismo."""
    if pasada not in PASADAS:
        raise ValueError("la pasada es {0}, no «{1}»".format(" o ".join(PASADAS), pasada))
    capitulo = str(capitulo)
    if capitulo not in TRAMOS_SIN_CAPITULO and not capitulo.isdigit():
        raise ValueError("el tramo es un numero de capitulo o uno de {0}, no «{1}»".format(
            ", ".join(TRAMOS_SIN_CAPITULO), capitulo))
    medido = usd if delegaciones > sin_coste else None
    asegurar_tablas(con)
    with con:
        con.execute(
            "INSERT OR REPLACE INTO gasto_de_evaluacion (ejecucion, brief, pasada, capitulo, "
            "usd, delegaciones, sin_coste, version_del_escritor) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ejecucion, brief, pasada, capitulo, medido, delegaciones, sin_coste,
             version_del_escritor))


def filas(con, ejecucion=None) -> list:
    asegurar_tablas(con)
    sql = ("SELECT ejecucion, brief, pasada, capitulo, usd, delegaciones, sin_coste, "
           "version_del_escritor, cuando FROM gasto_de_evaluacion")
    args = ()
    if ejecucion is not None:
        sql += " WHERE ejecucion = ?"
        args = (ejecucion,)
    claves = ("ejecucion", "brief", "pasada", "capitulo", "usd", "delegaciones",
              "sin_coste", "version_del_escritor", "cuando")
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
