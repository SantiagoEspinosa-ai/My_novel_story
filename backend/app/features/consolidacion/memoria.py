"""La memoria a largo plazo: resumenes y fichas.

Son dos de los siete bloques del contexto, y hasta `PLAN-01` F3 **no existian**:
el Resumidor devolvia su resumen y se tiraba. Sin ellos el contexto no crece, y
sin contexto que crezca `VER-37` no se puede contestar.

EL ORDEN LLEGA COMO PARAMETRO, Y NO SE CONSULTA
-------------------------------------------------
La primera version hacia `JOIN escena` para saber que escenas van antes. La
tabla `escena` es de `features/escaleta/`, asi que eso **acoplaba dos features
por la base de datos** — y `A-02` dice que una feature nunca depende de otra.
El comprobador de importaciones **no lo vio, porque no hay importacion**: el
acoplamiento viajaba por SQL.

Ahora el orden narrativo entra como numero y lo pasa quien lo sabe, que es
`orquestacion/`. Es una linea mas en el llamador y una dependencia menos.

`Ficha` Y `Resumen` LLEVAN VERSION, Y NO ES SIMETRIA GRATUITA
---------------------------------------------------------------
`Ficha.version_en_t` estaba en el dominio desde el principio; `Resumen` lo gano
con `SPEC-09` al descubrir que sin el no se puede reconstruir el nivel
`Resumenes` de una traza. Las dos se reescriben segun avanza la obra, asi que
las dos necesitan saber **de cuando** es lo que dicen.

HECHOS CLAVE SON IDENTIFICADORES
---------------------------------
`SPEC-03` lo decidio: `Resumen.hechos_clave` son referencias y no prosa, porque
un dato en prosa solo se comprueba buscando palabras dentro de palabras y todos
los validadores lexicos comparten el mismo punto ciego. Se hace cumplir aqui,
en la **frontera** (Regla 4): lo que no sea identificador no entra.
"""

import json
import re
import sqlite3

IDENTIFICADOR = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

SQL = """
CREATE TABLE IF NOT EXISTS resumen (
    escena       TEXT NOT NULL,
    obra         TEXT,
    orden        INTEGER NOT NULL,
    version_en_t TEXT NOT NULL,
    nivel        TEXT NOT NULL,
    texto        TEXT NOT NULL,
    hechos_clave TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (escena, version_en_t)
);
CREATE TABLE IF NOT EXISTS ficha (
    entidad      TEXT NOT NULL,
    obra         TEXT,
    orden        INTEGER NOT NULL,
    version_en_t TEXT NOT NULL,
    resumen      TEXT NOT NULL,
    PRIMARY KEY (entidad, version_en_t)
);
"""


class HechoNoEsIdentificador(Exception):
    pass


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar_resumen(con, escena, orden, texto, hechos_clave=None,
                    nivel="escena", obra=None):
    """`version_en_t` es la escena: el `t` en el que ese resumen es cierto."""
    hechos_clave = list(hechos_clave or [])
    for h in hechos_clave:
        if not isinstance(h, str) or not IDENTIFICADOR.match(h):
            raise HechoNoEsIdentificador(
                "hechos_clave tiene que traer identificadores y trae {0!r}. "
                "`SPEC-03`: referencias, no prosa — y se comprueba aqui, en la "
                "frontera, no mas adentro".format(h))
    asegurar_tablas(con)
    with con:
        con.execute("INSERT OR REPLACE INTO resumen (escena, obra, orden, "
                    "version_en_t, nivel, texto, hechos_clave) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (escena, obra, orden, escena, nivel, texto,
                     json.dumps(hechos_clave)))


def resumenes_hasta(con, orden_actual, obra=None):
    """Los resumenes de las escenas anteriores **de esta obra**, en orden.

    El `t` de una obra es su orden narrativo, no el reloj de quien la genero.

    `obra` no es opcional por comodidad, es lo que impide mezclar (`F-40`): el
    `orden` de una escena va del 1 al N **dentro de su obra**, asi que con dos
    obras en la misma base habia dos escenas con orden 1. Sin el filtro, la
    escena 4 de la segunda recibia los resumenes de la primera entremezclados y
    en orden equivocado, y la escena 1 de cada obra recibia **cero**: arrancaba
    sin memoria de todo lo anterior. Se midio en una obra de diez capitulos.
    """
    asegurar_tablas(con)
    if obra is None:
        filas = con.execute(
            "SELECT escena, texto, hechos_clave FROM resumen "
            "WHERE orden < ? ORDER BY orden", (orden_actual,))
    else:
        filas = con.execute(
            "SELECT escena, texto, hechos_clave FROM resumen "
            "WHERE orden < ? AND obra = ? ORDER BY orden", (orden_actual, obra))
    return [{"escena": f[0], "texto": f[1], "hechos_clave": json.loads(f[2])}
            for f in filas]


def actualizar_fichas(con, escena, orden, entidades, obra=None):
    """Una version nueva por entidad tocada, no una sobrescritura.

    Sobrescribir haria irreconstruible el contexto de una escena pasada, que es
    justo el agujero que `SPEC-09` cerro para `Resumen`.
    """
    asegurar_tablas(con)
    with con:
        for entidad, resumen in entidades.items():
            con.execute("INSERT OR REPLACE INTO ficha (entidad, obra, orden, "
                        "version_en_t, resumen) VALUES (?, ?, ?, ?, ?)",
                        (entidad, obra, orden, escena, resumen))


def fichas_en(con, orden_actual, obra=None):
    """La version mas reciente de cada ficha **en o antes** de este orden.

    Acotada a la obra por lo mismo que `resumenes_hasta` (`F-40`).
    """
    asegurar_tablas(con)
    if obra is None:
        filas = con.execute(
            "SELECT entidad, resumen, version_en_t FROM ficha "
            "WHERE orden <= ? ORDER BY orden", (orden_actual,))
    else:
        filas = con.execute(
            "SELECT entidad, resumen, version_en_t FROM ficha "
            "WHERE orden <= ? AND obra = ? ORDER BY orden", (orden_actual, obra))
    ultimas = {}
    for entidad, resumen, version in filas:
        ultimas[entidad] = {"entidad": entidad, "resumen": resumen,
                            "version_en_t": version}
    return list(ultimas.values())
