"""Las puertas deterministas: las invariantes de tipo `regla` de nivel escena.

Lo que se puede comprobar con codigo se comprueba con codigo. Pedirselo a un
modelo es mas caro, mas lento y menos fiable, y en el caso de `INV-17` es
ademas lo que dejo el hueco: un juez que juzga ritmo aprueba un capitulo corto.

Esta feature **no decide que pasa** con un hallazgo. Solo lo produce. Que una
`bloqueante` detenga la escena y un `mayor` impida cerrar el capitulo lo decide
`commons/invariantes/severidad.py`, una vez (`D-4`).
"""

from app.commons.dominio.enumeraciones import EstadoDeHallazgo
from app.commons.dominio.modelos import Hallazgo
from app.commons.invariantes.registro import TODAS

VERIFICADOR = "verificador_de_reglas"


def _hallazgo(inv, escena, descripcion):
    return Hallazgo(invariante=inv, verificador=VERIFICADOR, escena=escena,
                    severidad=TODAS[inv].severidad,
                    estado=EstadoDeHallazgo.ABIERTO, descripcion=descripcion)


def veredicto_ilegible(inv, escena, salida):
    """Un verificador que no contesta es un agujero en la validacion.

    Los campos obligatorios **no se relajan**: `descripcion` se rellena con que
    se intento comprobar y donde. Lo que falta es el juicio, no el contexto.
    """
    return Hallazgo(
        invariante=inv, verificador=VERIFICADOR, escena=escena,
        severidad=TODAS[inv].severidad, estado=EstadoDeHallazgo.SIN_VEREDICTO,
        descripcion="no se pudo interpretar el veredicto de {0} sobre la escena "
                    "{1}; salida recibida: {2!r}".format(inv, escena, salida[:80]),
    )


def verificar(escena, delta, mundo):
    h = []

    if not escena.get("cambio_de_valor"):
        h.append(_hallazgo("INV-01", escena["id"],
                           "la escena no mueve ningun valor dramatico"))

    for p in escena.get("personajes_presentes", []):
        if mundo["entidades_vivas"].get(p) != "vivo":
            h.append(_hallazgo("INV-02", escena["id"],
                               "{0} esta presente y su estado_vital es {1}".format(
                                   p, mundo["entidades_vivas"].get(p))))
        else:
            desde = mundo["ubicaciones"].get(p)
            hasta = escena.get("lugar")
            if hasta and desde and hasta != desde and hasta not in mundo["accesos"].get(desde, []):
                h.append(_hallazgo("INV-02", escena["id"],
                                   "{0} esta en {1} y la escena ocurre en {2}, que no es "
                                   "accesible desde alli".format(p, desde, hasta)))

    # `INV-03` mira las **acciones**, no las revelaciones (`SPEC-16` C-1).
    #
    # Revelar es **aprender**: es el momento en que el sujeto se entera, y es lo
    # que escribe el registro de conocimiento en la consolidacion. Mientras esta
    # puerta las miraba, exigia que el hecho constara **antes** de la escena
    # para poder aprenderse en ella, y el registro solo se escribe desde esas
    # mismas revelaciones. Ningun personaje podia llegar a saber nada nunca
    # (`F-31`). Actuar es **obrar sirviendose de lo ya sabido**, y eso si se
    # puede comprobar contra lo que consta.
    for acc in (delta or {}).get("acciones", []):
        clave = (acc["personaje"], acc["hecho"])
        sabido = mundo["conocimiento"].get(clave)
        if not sabido or sabido["grado"] == "ignora":
            h.append(_hallazgo("INV-03", escena["id"],
                               "{0} actua sobre {1} y no consta que lo conozca en t".format(
                                   acc["personaje"], acc["hecho"])))

    if escena.get("pov_usado") and escena.get("pov") != escena["pov_usado"]:
        h.append(_hallazgo("INV-04", escena["id"],
                           "el POV planificado es {0} y el usado {1}".format(
                               escena.get("pov"), escena["pov_usado"])))

    rango = escena.get("longitud_objetivo")
    palabras = escena.get("palabras")
    if rango and palabras is not None and not (rango[0] <= palabras <= rango[1]):
        h.append(_hallazgo("INV-17", escena["id"],
                           "{0} palabras, fuera del rango {1}-{2}".format(
                               palabras, rango[0], rango[1])))
    return h
