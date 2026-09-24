"""La regla del texto elegido de una escena, en un solo sitio (`PLAN-22` DP-5).

QUE VERSION, Y POR QUE NO ES LA ULTIMA
----------------------------------------
La que dice `Escena.borrador_aceptado`; si no consta -o apunta a una version que no
existe-, la ultima. Una escena **rendida** tiene varias versiones y `borrador_aceptado`
dice cual se eligio: coger siempre la ultima meteria en la lectura una version que se
descarto, y nadie lo notaria leyendo.

La regla vivia en `features/manuscrito/exportar.py` y la lectura web la necesita igual.
Dos copias de la misma regla divergen el dia que una aprende algo, asi que sube aqui y las
dos la llaman.

**No toca el texto.** `VER-60` exige que sea byte a byte el del `Borrador` auditado: ni
se recorta ni se normaliza. Y devuelve **la version** con el texto, porque una seleccion
sobre "el texto" sin decir de que borrador es no se puede anclar (`SPEC-22` `RF-47`).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Elegido:
    version: int
    texto: str


def elegido(con, escena, borrador_aceptado):
    """El `Borrador` elegido de la escena, o `None` si no tiene ninguno."""
    if borrador_aceptado is not None:
        fila = con.execute(
            "SELECT version, texto FROM borrador WHERE escena = ? AND version = ?",
            (escena, borrador_aceptado)).fetchone()
        if fila:
            return Elegido(version=fila[0], texto=fila[1])
    fila = con.execute(
        "SELECT version, texto FROM borrador WHERE escena = ? "
        "ORDER BY version DESC LIMIT 1", (escena,)).fetchone()
    return Elegido(version=fila[0], texto=fila[1]) if fila else None
