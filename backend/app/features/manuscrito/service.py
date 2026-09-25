"""Exportar a PDF solo lo publicado (`SPEC-27` `RF-01`, `PLAN-27` E6).

La version que se exporta es **la unica que hay** (`F-43`, `EX-14`): `RF-04` se queda en
«basta el de la ultima» hasta que existan versiones de obra.
"""

from app.features.manuscrito import libro, pdf, repository


class VersionNoPublicada(Exception):
    """La puerta no dejo pasar la version, o no llego a correr: no hay PDF."""


def motivo_sin_pdf(con, obra):
    """Por que la obra no tiene PDF, o `None` si lo tiene. Sin generarlo: es lo que la
    portada pregunta antes de ofrecer el boton (`SPEC-35` `RF-12`)."""
    v = repository.ultimo_veredicto(con, obra)
    if v is None:
        return ("la obra `{0}` no tiene veredicto de la puerta de publicacion: no se ha "
                "publicado ninguna version".format(obra))
    if not v["publica"]:
        faltan = "; ".join("{0} {1}: {2}".format(c.get("invariante"),
                                                 c.get("capitulo") or "(obra)",
                                                 c.get("detalle"))
                           for c in v["condiciones"]) or "sin condiciones guardadas"
        return "la ronda {0} de la puerta no publico la obra `{1}`: {2}".format(
            v["ronda"], obra, faltan)
    return None


def exportar_pdf(con, obra, ruta, creado=None):
    motivo = motivo_sin_pdf(con, obra)
    if motivo is not None:
        raise VersionNoPublicada(motivo)
    return pdf.a_pdf(libro.componer(con, obra), ruta, creado=creado)
