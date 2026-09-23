"""Que se puede editar a mano, y que no (`SPEC-20`).

LA REGLA
--------
Se puede editar **todo lo no consolidado, mas el plan**. Se puede editar **lo
que ninguna escena consolidada haya usado todavia**. El **estado consolidado no
se toca a mano nunca**.

POR QUE EL ESTADO ES INTOCABLE Y NO ES UNA CAUTELA EXAGERADA
--------------------------------------------------------------
`EstadoDelMundo` es **derivado**: se reconstruye acumulando los deltas en orden
y no se relee del texto (`CLAUDE.md`). No existe una edicion manual correcta
sobre un dato derivado — lo que hay es corregir el delta que lo produjo, y eso
ya no es editar, es **rehacer la escena**.

Un estado editado a mano deja de ser reconstruible, y a partir de ese momento
nadie puede saber si el canon sale de la obra o de una correccion que alguien
hizo un martes. Con diecisiete intervenciones previstas en una obra de sesenta
escenas (`VER-64`), eso no es un caso raro: es el caso.

ESTE MODULO NO VA A BUSCAR NADA, Y ESO NO ES UN DETALLE
--------------------------------------------------------
`se_puede_editar` recibe **quien usa el objeto**; no lo consulta. La primera
version lo averiguaba con SQL sobre las tablas `escena` y `conocimiento`, que
son de `escaleta` y de `consolidacion`, y eso es `A-02` roto por la via que
ningun comprobador de importaciones ve: **el acoplamiento tambien viaja por
SQL** (`F-28`, `PC-18`). Quien reune el material es `orquestacion/`, la unica
autorizada a componer.

POR QUE SE NIEGA LO DESCONOCIDO
--------------------------------
Una clase que este modulo no conoce **no se puede editar**. Al reves, cada clase
nueva del dominio nacería editable sin que nadie lo hubiera decidido, y el
permiso por omision es el que nadie revisa.
"""

import sqlite3
from dataclasses import dataclass, field

SQL = """
CREATE TABLE IF NOT EXISTS edicion_manual (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    clase   TEXT NOT NULL,
    objeto  TEXT NOT NULL,
    quien   TEXT NOT NULL,
    motivo  TEXT NOT NULL,
    cuando  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# El plan es **entrada**, no resultado: corregirlo es replanificar, que es una
# cosa legitima y no una correccion a escondidas.
DEL_PLAN = {"escaleta", "beat", "conocimiento_inicial", "brief"}

# Derivado o auditado. Ninguno admite edicion manual correcta.
INTOCABLES = {
    "estado_del_mundo": "es **derivado**: se reconstruye acumulando los deltas en "
                        "orden. La via correcta para arreglarlo es rehacer la "
                        "escena cuyo delta lo produjo",
    "borrador": "es lo que devolvio el agente. Editado deja de serlo, y `VER-60` "
                "-que compara el manuscrito con el borrador auditado- dejaria de "
                "significar nada",
    "conocimiento": "es el estado derivado de las revelaciones, no una tabla que "
                    "se rellene a mano",
}

# Se editan si nadie consolidado los ha usado todavia.
SEGUN_USO = {"hecho", "escena", "setup"}


class EdicionProhibida(Exception):
    pass


@dataclass(frozen=True)
class Veredicto:
    permitido: bool
    motivo: str
    usado_por: list = field(default_factory=list)


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def se_puede_editar(clase: str, objeto: str, usado_por=None) -> Veredicto:
    """El veredicto, con quien lo impide si lo impide alguien.

    `usado_por` son las escenas **consolidadas** que dependen del objeto, y las
    calcula quien llama. Recibirlas y no buscarlas es lo que mantiene a esta
    feature sin tocar tablas ajenas (`A-02`, `F-28`).

    Devolver la lista y no un booleano es deliberado: un "no se puede" sin
    decir quien lo impide obliga a ir a buscarlo a mano, que es el coste que
    `F-38` existia para quitar.
    """
    if clase in INTOCABLES:
        return Veredicto(False, "`{0}` no se edita a mano: {1}".format(
            clase, INTOCABLES[clase]))
    if clase in DEL_PLAN:
        return Veredicto(True, "el plan es entrada y no resultado: corregirlo "
                               "es replanificar")
    if clase not in SEGUN_USO:
        # Lo que no se ha pensado no se autoriza.
        return Veredicto(False, "`{0}` no es una clase que este modulo sepa "
                                "evaluar, asi que no se autoriza. Lo que no se "
                                "ha decidido no se permite por omision".format(clase))
    usan = list(usado_por or [])
    if usan:
        return Veredicto(
            False,
            "`{0}` ya lo usaron escenas consolidadas ({1}): cambiarlo cambiaria "
            "retroactivamente lo que esas escenas dijeron".format(
                objeto, ", ".join(usan)),
            usado_por=usan)
    return Veredicto(True, "ninguna escena consolidada lo ha usado todavia")


def registrar_edicion(con, clase: str, objeto: str, quien: str, motivo: str,
                      usado_por=None):
    """Deja el rastro, y **solo si la edicion estaba permitida**.

    El rastro no legitima lo prohibido: si se pudiera registrar una edicion del
    estado consolidado, el registro seria la coartada en vez del control.

    El motivo es obligatorio por lo mismo que al cerrar un hallazgo (`F-38`):
    sin el, una obra con diecisiete intervenciones es indistinguible de una que
    salio sola, y lo que `VER-64` mide deja de significar nada.
    """
    if not (motivo or "").strip():
        raise ValueError(
            "una edicion manual exige motivo: sin el no se puede distinguir "
            "una correccion de una obra intervenida")
    v = se_puede_editar(clase, objeto, usado_por)
    if not v.permitido:
        raise EdicionProhibida(v.motivo)
    asegurar_tablas(con)
    with con:
        con.execute("INSERT INTO edicion_manual (clase, objeto, quien, motivo) "
                    "VALUES (?, ?, ?, ?)", (clase, objeto, quien, motivo))


def ediciones_de(con, clase: str, objeto: str):
    asegurar_tablas(con)
    return [{"quien": f[0], "motivo": f[1], "cuando": f[2]}
            for f in con.execute(
                "SELECT quien, motivo, cuando FROM edicion_manual "
                "WHERE clase = ? AND objeto = ? ORDER BY id", (clase, objeto))]
