"""Exportar a PDF solo lo publicado (`SPEC-27` `RF-01`, `PLAN-27` E6).

La version que se exporta es **la unica que hay** (`F-43`, `EX-14`): `RF-04` se queda en
«basta el de la ultima» hasta que existan versiones de obra.
"""

from app.features.manuscrito import libro, pdf, repository


class VersionNoPublicada(Exception):
    """La puerta no dejo pasar la version, o no llego a correr: no hay PDF."""


def exportar_pdf(con, obra, ruta, creado=None):
    v = repository.ultimo_veredicto(con, obra)
    if v is None:
        raise VersionNoPublicada(
            "la obra `{0}` no tiene veredicto de la puerta de publicacion: no se ha "
            "publicado ninguna version".format(obra))
    if not v["publica"]:
        faltan = "; ".join("{0} {1}: {2}".format(c.get("invariante"),
                                                 c.get("capitulo") or "(obra)",
                                                 c.get("detalle"))
                           for c in v["condiciones"]) or "sin condiciones guardadas"
        raise VersionNoPublicada(
            "la ronda {0} de la puerta no publico la obra `{1}`: {2}".format(
                v["ronda"], obra, faltan))
    return pdf.a_pdf(libro.componer(con, obra), ruta, creado=creado)
