"""La obra, de principio a fin, sin abrir la base a mano.

EL TEXTO EXISTIA Y LA OBRA NO
-------------------------------
Tras generar sesenta escenas, el texto vivia en cincuenta y siete filas de la
tabla `borrador` y **no habia forma de leerlo seguido**. Para hacerlo hacia
falta saber que escena va en que capitulo, en que orden, y cual de sus
versiones se acepto — tres cosas que estan en la base y ninguna en el texto.

**Una novela que solo se puede leer con SQL no esta terminada.**

QUE VERSION DE CADA ESCENA, Y POR QUE NO ES LA ULTIMA
-------------------------------------------------------
La que dice `Escena.borrador_aceptado`; si no consta, la ultima. No son lo
mismo: una escena **rendida** tiene varias versiones y `borrador_aceptado` dice
cual se eligio (`RF-24`). Coger siempre la ultima meteria en el manuscrito una
version que se descarto, y nadie lo notaria leyendo.

ESTE MODULO NO TOCA EL TEXTO
------------------------------
`VER-60` exige que *"el texto de una escena en el manuscrito sea byte a byte el
del `Borrador` que se audito"*. Asi que aqui no se recorta, no se limpia y no
se juntan parrafos. Lo unico que se pone de nuestra parte son los titulos, y
son opcionales para que la comparacion de `VER-60` pueda mirar solo el texto.

UN HUECO SE MARCA, NO SE SALTA
--------------------------------
Una escena sin texto no desaparece del manuscrito: deja una marca con su
identificador. Un manuscrito al que le falta una escena **sin decirlo** se lee
como una novela completa, y `VER-60` avisa del mismo problema por el otro lado
— compara el texto y no ve lo que falta.
"""

import sqlite3
from dataclasses import dataclass, field

from app.commons.obra import texto as texto_elegido

MARCA_DE_HUECO = "[[ FALTA EL TEXTO DE {0} ]]"


class ObraSinTexto(Exception):
    pass


@dataclass
class Manuscrito:
    texto: str
    titulo: str
    capitulos: int
    escenas: int
    palabras: int
    escenas_sin_texto: list = field(default_factory=list)
    sin_cabecera: bool = False


@dataclass
class EscenaDelLibro:
    id: str
    texto: str | None  # `None` si no hay borrador: se dice, no se salta


@dataclass
class CapituloDelLibro:
    id: str | None  # `None`: escenas sin capitulo, de las escaletas anteriores a `SPEC-21`
    orden: int | None
    escenas: list = field(default_factory=list)


def _filas(con, obra):
    # Orden de lectura: por capitulo y, dentro, por orden de escena. Las
    # escenas sin capitulo van al final y agrupadas, porque son las de las
    # escaletas anteriores a `SPEC-21` y no hay donde situarlas sin inventar.
    # Las bases anteriores a `SPEC-21` tampoco tienen tabla `capitulo`: sin ella
    # no hay orden de capitulo que respetar, y se ordena por el de la escena.
    # `PLAN-23` A6: con versiones, las de la vigente; sin ellas, las de la obra.
    vigente = _de_la_version_vigente(con, obra)
    if vigente is not None:
        return vigente
    try:
        return con.execute(
            "SELECT e.id, e.capitulo, e.orden, e.borrador_aceptado, c.orden "
            "FROM escena e LEFT JOIN capitulo c ON c.id = e.capitulo "
            "WHERE e.obra = ? ORDER BY COALESCE(c.orden, 9999), e.orden, e.id",
            (obra,)).fetchall()
    except sqlite3.OperationalError:
        return con.execute(
            "SELECT id, capitulo, orden, borrador_aceptado, NULL "
            "FROM escena WHERE obra = ? ORDER BY orden, id", (obra,)).fetchall()


def capitulos_de(con, obra) -> list:
    """`PLAN-27` E1: los capitulos en orden de lectura, con el texto elegido de cada
    escena **sin tocarlo**. Es lo que leen el manuscrito y el PDF (`VER-60`)."""
    # Por identificador y en el orden en que aparece cada uno: sin tabla `capitulo` las
    # escenas llegan por su orden y los capitulos se intercalan.
    capitulos = {}
    for id_escena, capitulo, _orden, aceptado, orden_cap in _filas(con, obra):
        cap = capitulos.setdefault(capitulo, CapituloDelLibro(capitulo, orden_cap))
        cap.escenas.append(EscenaDelLibro(id_escena, _texto_de(con, id_escena, aceptado)))
    return list(capitulos.values())


def _texto_de(con, escena, aceptado):
    """El borrador elegido, o el ultimo si nadie eligio. La regla vive en
    `commons/obra/texto.py` (`PLAN-22` DP-5): la lectura web usa la misma."""
    e = texto_elegido.elegido(con, escena, aceptado)
    return e.texto if e else None


def _de_la_version_vigente(con, obra):
    """Las escenas de la version vigente, en su orden, o `None` si la obra no tiene
    versiones (`PLAN-23` A6). Con dos versiones, la tabla `capitulo` tiene el capitulo
    sustituido y el nuevo en la misma posicion, y el manuscrito tendria dos capitulos 2.

    Lee las tablas de versiones por SQL, como ya leia `capitulo`: es el acoplamiento
    que esta feature ya tenia (`F-28`), dicho aqui en vez de callado."""
    try:
        fila = con.execute("SELECT MAX(numero) FROM version_de_obra WHERE obra = ?",
                           (obra,)).fetchone()
    except sqlite3.OperationalError:
        return None
    if fila is None or fila[0] is None:
        return None
    return con.execute(
        "SELECT e.id, e.capitulo, e.orden, e.borrador_aceptado, v.orden AS orden_cap "
        "FROM capitulo_de_version v JOIN escena e "
        "  ON e.capitulo = v.capitulo AND e.obra = v.obra "
        "WHERE v.obra = ? AND v.numero = ? ORDER BY v.orden, e.orden, e.id",
        (obra, fila[0])).fetchall()


def manuscrito(con, obra, con_titulos=True) -> Manuscrito:
    """La obra entera como una sola cadena, en orden de lectura."""
    # Dos ausencias distintas, y solo una es un error.
    #
    # Sin **escenas** no hay nada que exportar, y devolver un manuscrito vacio
    # se leeria como "no se escribio nada" en vez de "pregunte por otra obra".
    #
    # Sin **cabecera** si hay algo: las bases anteriores a `SPEC-21` no tienen
    # tabla `obra` y sus escenas son texto real. Negarse a exportarlas seria
    # perder una novela por una fila que falta. Lo que no se hace es fingir que
    # la cabecera estaba: el titulo es el identificador y `sin_cabecera` lo
    # dice, para que nadie lea ese titulo como el que el autor puso.
    hay_escenas = con.execute(
        "SELECT COUNT(*) FROM escena WHERE obra = ?", (obra,)).fetchone()[0]
    if not hay_escenas:
        raise ObraSinTexto(
            "no hay ninguna escena de la obra `{0}`. Si la obra existe con "
            "otro identificador, el manuscrito saldria vacio y un vacio se lee "
            "como 'no se escribio nada'".format(obra))
    try:
        cabecera = con.execute("SELECT titulo FROM obra WHERE id = ?",
                               (obra,)).fetchone()
    except sqlite3.OperationalError:
        cabecera = None
    sin_cabecera = cabecera is None

    capitulos = capitulos_de(con, obra)
    partes, sin_texto, numero = [], [], 0
    if con_titulos:
        partes.append("# " + ((cabecera[0] if cabecera else None) or obra))
    for cap in capitulos:
        if cap.id is not None:
            numero += 1
            if con_titulos:
                partes.append("## Capitulo {0}".format(numero))
        for e in cap.escenas:
            if e.texto is None:
                sin_texto.append(e.id)
                partes.append(MARCA_DE_HUECO.format(e.id))
            else:
                partes.append(e.texto)

    # `F-63`: se junta sin recortar. El separador lo pone este modulo y el texto de
    # cada escena va tal cual, con sus bordes (`VER-60`).
    entero = "\n\n".join(partes)
    if not entero.endswith("\n"):
        entero += "\n"
    total = sum(len(c.escenas) for c in capitulos)
    return Manuscrito(
        texto=entero, titulo=(cabecera[0] if cabecera else None) or obra,
        capitulos=numero,
        escenas=total - len(sin_texto),
        palabras=len(entero.split()),
        escenas_sin_texto=sin_texto, sin_cabecera=sin_cabecera)


def a_fichero(con, obra, ruta, con_titulos=True) -> Manuscrito:
    """Escribe el manuscrito y devuelve lo que se escribio.

    En UTF-8 explicito: la consola de Windows no lo es por defecto, y una
    novela con acentos escrita en la codificacion del sistema se lee mal en
    cualquier otra maquina.
    """
    m = manuscrito(con, obra, con_titulos=con_titulos)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(m.texto)
    return m
