"""Los capitulos donde aparece una entidad (`docs/definitions.md`, `capitulos_donde_aparece[]`).

*Aparecer* tiene un significado exacto (`SPEC-22` `RF-44`): para un `Personaje`, las
escenas en que `participa_en` -`Escena.personajes_presentes`-; para un `Lugar`, las que
`ocurre_en` el -`Escena.lugar`-. **No** es que el texto lo mencione ni que su ficha
entrara en el contexto. Lo necesitan la lectura web y el libro (`PLAN-22` DP-5).

EN ORDEN DE LECTURA, Y NO DE IDENTIFICADOR
-------------------------------------------
Por `capitulo.orden`. Ordenar por `id` sale bien mientras los identificadores lleven
ceros a la izquierda, que es la Regla 11 esperando a que alguien los nombre de otra forma.

DESCONOCIDO NO ES NADIE
-------------------------
Si alguna escena de la obra no declara `personajes_presentes` (NULL), no se sabe en que
capitulos esta **ningun** personaje: una lista parcial se leeria como completa. Quien
use las listas recibe `declarados = False` y las trata como desconocidas, que la
interfaz pinta «no declarado». Se prefiere el ruidoso: una sola escena sin declarar apaga
todas las listas, y se ve.

Una lista vacia de **lugares** si es un dato, porque `Escena.lugar` es obligatorio.
"""

import json

from app.commons.obra import vigente


def _escenas(con, obra):
    """Las escenas de la version vigente, en su orden (`F-203`). La tabla `capitulo` tiene
    los capitulos de todas las versiones, y con tres versiones cada ficha enlazaba tres
    veces el mismo capitulo. Sin versiones -una obra de antes-, los de la obra."""
    numero = vigente.version_vigente(con, obra)
    if numero is not None:
        return con.execute(
            "SELECT e.capitulo, v.orden, e.lugar, e.personajes_presentes "
            "FROM capitulo_de_version v JOIN escena e "
            "  ON e.capitulo = v.capitulo AND e.obra = v.obra "
            "WHERE v.obra = ? AND v.numero = ? ORDER BY v.orden, e.orden",
            (obra, numero)).fetchall()
    return con.execute(
        "SELECT e.capitulo, c.orden, e.lugar, e.personajes_presentes "
        "FROM escena e JOIN capitulo c ON c.id = e.capitulo AND c.obra = e.obra "
        "WHERE e.obra = ? ORDER BY c.orden, e.orden", (obra,)).fetchall()


def _acumular(destino, clave, capitulo, orden):
    lista = destino.setdefault(clave, [])
    if not any(c["id"] == capitulo for c in lista):
        lista.append({"id": capitulo, "orden": orden})


def de_lugares(con, obra):
    """`{id_lugar: [{id, orden}, ...]}`: los capitulos de la obra que ocurren en el."""
    salida = {}
    for capitulo, orden, lugar, _ in _escenas(con, obra):
        if lugar:
            _acumular(salida, lugar, capitulo, orden)
    return salida


def de_personajes(con, obra):
    """`({id_personaje: [{id, orden}, ...]}, declarados)`.

    `declarados` es falso si alguna escena de la obra no declara sus presentes: entonces
    las listas son parciales y quien las use las tiene que tratar como desconocidas.
    """
    salida, declarados = {}, True
    for capitulo, orden, _, presentes in _escenas(con, obra):
        if presentes is None:
            declarados = False
            continue
        for personaje in json.loads(presentes):
            _acumular(salida, personaje, capitulo, orden)
    return salida, declarados
