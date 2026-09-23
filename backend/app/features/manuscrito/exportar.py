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


def _texto_de(con, escena, aceptado):
    """El borrador elegido, o el ultimo si nadie eligio."""
    if aceptado is not None:
        fila = con.execute(
            "SELECT texto FROM borrador WHERE escena = ? AND version = ?",
            (escena, aceptado)).fetchone()
        if fila:
            return fila[0]
    fila = con.execute(
        "SELECT texto FROM borrador WHERE escena = ? "
        "ORDER BY version DESC LIMIT 1", (escena,)).fetchone()
    return fila[0] if fila else None


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

    # Orden de lectura: por capitulo y, dentro, por orden de escena. Las
    # escenas sin capitulo van al final y agrupadas, porque son las de las
    # escaletas anteriores a `SPEC-21` y no hay donde situarlas sin inventar.
    # Tercera ausencia de la misma familia: las bases anteriores a `SPEC-21`
    # tampoco tienen tabla `capitulo`. Sin ella no hay orden de capitulo que
    # respetar, y se ordena por el de la escena — que es el unico que hay.
    try:
        filas = con.execute(
            "SELECT e.id, e.capitulo, e.orden, e.borrador_aceptado, "
            "       COALESCE(c.orden, 9999) AS orden_cap "
            "FROM escena e LEFT JOIN capitulo c ON c.id = e.capitulo "
            "WHERE e.obra = ? ORDER BY orden_cap, e.orden, e.id",
            (obra,)).fetchall()
    except sqlite3.OperationalError:
        filas = con.execute(
            "SELECT id, capitulo, orden, borrador_aceptado, 9999 "
            "FROM escena WHERE obra = ? ORDER BY orden, id", (obra,)).fetchall()

    partes, sin_texto, capitulos_vistos = [], [], []
    if con_titulos:
        partes.append("# " + ((cabecera[0] if cabecera else None) or obra))

    for id_escena, capitulo, _orden, aceptado, _oc in filas:
        if capitulo and capitulo not in capitulos_vistos:
            capitulos_vistos.append(capitulo)
            if con_titulos:
                partes.append("\n\n## Capitulo {0}\n".format(
                    len(capitulos_vistos)))
        texto = _texto_de(con, id_escena, aceptado)
        if texto is None:
            sin_texto.append(id_escena)
            partes.append("\n\n" + MARCA_DE_HUECO.format(id_escena))
            continue
        partes.append("\n\n" + texto)

    entero = "".join(partes).strip() + "\n"
    return Manuscrito(
        texto=entero, titulo=(cabecera[0] if cabecera else None) or obra,
        capitulos=len(capitulos_vistos),
        escenas=len([f for f in filas if f[0] not in sin_texto]),
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
