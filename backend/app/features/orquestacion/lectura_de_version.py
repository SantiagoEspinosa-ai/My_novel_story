"""Leer una version de la obra (`PLAN-22` E15, `SPEC-22` `RF-52`..`RF-54`).

Compone la lectura de `lectura/` -estado, hallazgos y texto de cada escena- con lo que
solo sabe `regeneracion`: la marca de «cambio» de cada capitulo y el
`estado_de_verificacion` de cada escena en esa version. **No se calcula nada aqui**: las
dos cosas salen de `regeneracion.vista_de_version`, y la interfaz las pinta tal cual.
"""

from app.features.lectura import service as lectura
from app.features.orquestacion import regeneracion


def _marcas(vista):
    return {c["capitulo"]: (c["compartido"],
                            {e["id"]: e["estado_de_verificacion"] for e in c["escenas"]})
            for c in vista["capitulos"]}


def _con_marcas(capitulo, marcas):
    compartido, verificacion = marcas[capitulo["id"]]
    capitulo["compartido"] = compartido
    for e in capitulo["escenas"]:
        e["estado_de_verificacion"] = verificacion[e["id"]]
    return capitulo


def indice(con, obra, numero):
    """El indice de la version `numero`, o `None` si la obra no la tiene."""
    vista = regeneracion.vista_de_version(con, obra, numero)
    if vista is None:
        return None
    base = lectura.indice(con, obra, version=numero)
    marcas = _marcas(vista)
    base["capitulos"] = [_con_marcas(c, marcas) for c in base["capitulos"]]
    return dict(base, numero=numero, anterior=vista["anterior"])


def capitulo(con, obra, numero, id_capitulo):
    """Un capitulo **de la version**, con su posicion en ella como `orden`. `None` si la
    version no existe o el capitulo no es suyo: el 2 viejo no se lee como de la 2."""
    vista = regeneracion.vista_de_version(con, obra, numero)
    if vista is None:
        return None
    posicion = next((c["orden"] for c in vista["capitulos"] if c["capitulo"] == id_capitulo),
                    None)
    leido = lectura.capitulo(con, id_capitulo) if posicion is not None else None
    if leido is None:
        return None
    leido = _con_marcas(dict(leido, orden=posicion), _marcas(vista))
    return dict(leido, numero=numero)
