"""La lectura de una obra: lo que la web pinta, ya resuelto (`SPEC-22` `NF-06`).

Aqui se decide lo que la interfaz no puede decidir: el orden, que escenas son de que
capitulo, si una escena se rindio y que hallazgos cuentan como abiertos. La interfaz lo
pinta tal cual llega.
"""

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
