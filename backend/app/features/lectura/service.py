"""La lectura de una obra: lo que la web pinta, ya resuelto (`SPEC-22` `NF-06`).

Aqui se decide lo que la interfaz no puede decidir: el orden, que escenas son de que
capitulo, si una escena se rindio y que hallazgos cuentan como abiertos. La interfaz lo
pinta tal cual llega.
"""

import json

from app.commons.obra import apariciones, texto
from app.features.lectura import repository as repo
from app.features.lectura import vista


def _escena_del_indice(con, fila):
    return {"id": fila["id"], "capitulo": fila["capitulo"], "estado": fila["estado"],
            "se_acepto_rindiendose": fila["estado"] == vista.RENDIDA,
            "hallazgos_abiertos": repo.hallazgos_abiertos(con, fila["id"])}


def indice(con, id_obra):
    """`None` si la obra no existe: un id de capitulo no es una obra (`RF-37`)."""
    obra = repo.obra(con, id_obra)
    if obra is None:
        return None
    obra["capitulos"] = [
        {"id": c["id"], "orden": c["orden"], "estado": c["estado"],
         "escenas": [_escena_del_indice(con, e)
                     for e in repo.escenas_de_capitulo(con, id_obra, c["id"])]}
        for c in repo.capitulos(con, id_obra)]
    return obra


def _escena_leida(con, fila):
    e = _escena_del_indice(con, fila)
    elegido = texto.elegido(con, fila["id"], fila["borrador_aceptado"])
    e["borrador"] = None if elegido is None else {"version": elegido.version,
                                                   "texto": elegido.texto}
    presentes = fila["personajes_presentes"]
    e["personajes_presentes"] = None if presentes is None else json.loads(presentes)
    return e


def capitulo(con, id_capitulo):
    """`None` si no existe: un id de obra no es un capitulo (`RF-37`)."""
    c = repo.capitulo(con, id_capitulo)
    if c is None:
        return None
    return {"id": c["id"], "orden": c["orden"], "estado": c["estado"],
            "escenas": [_escena_leida(con, e)
                        for e in repo.escenas_de_capitulo(con, c["obra"], c["id"])]}


def escena(con, id_escena):
    """La misma forma que dentro de su capitulo: una sola regla para las dos."""
    fila = repo.escena(con, id_escena)
    return None if fila is None else _escena_leida(con, fila)


def hechos_de_escena(con, id_escena):
    """`None` si la escena no existe; si existe, sus hechos, vacia si no usa ninguno."""
    fila = repo.escena(con, id_escena)
    if fila is None:
        return None
    return {"escena": id_escena,
            "hechos_que_usa": repo.hechos_que_usa(con, id_escena, fila["obra"])}


def fichas(con, id_obra):
    """Las fichas de la obra, con los capitulos donde aparece cada entidad (`RF-43`, `RF-44`).

    `alias`, `rol_dramatico` y `atmosfera` viajan nulos: la base no los guarda.
    """
    if repo.obra(con, id_obra) is None:
        return None
    de_personajes, declarados = apariciones.de_personajes(con, id_obra)
    de_lugares = apariciones.de_lugares(con, id_obra)
    personajes = [
        dict(id=p, alias=None, rol_dramatico=None, **repo.canon_de_personaje(con, p),
             capitulos_donde_aparece=de_personajes.get(p, []) if declarados else None)
        for p in repo.personajes_de_la_obra(con, id_obra)]
    lugares = [dict(id=id_l, atmosfera=None, **repo.canon_de_lugar(con, id_l),
                    capitulos_donde_aparece=de_lugares.get(id_l, []))
               for id_l in repo.lugares_de_la_obra(con, id_obra)]
    return {"personajes": personajes, "lugares": lugares}


def progreso(con, id_obra):
    """`None` si la obra no tiene ninguna fila de progreso: no se esta generando."""
    return repo.progreso(con, id_obra)
