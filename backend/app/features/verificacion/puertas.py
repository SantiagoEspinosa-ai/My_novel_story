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


def dato_ausente(inv, escena, campo, para):
    """Le falta el dato, asi que **no puede evaluar**, y lo dice.

    `F-34`: una invariante que se salta en silencio cuando le falta un campo
    **esta ausente, no en verde**, y desde fuera las dos se ven igual. Ocurrio
    en real: el modelo escribio la escena sobre otro personaje del planificado
    e `INV-04` no miro nada, porque la escena no traia `pov`.

    Es el mismo argumento de `veredicto_ilegible` y usa el mismo estado:
    **un verificador que no contesta es un agujero en la validacion**, y da
    igual que la causa sea una salida ilegible o un campo que nadie relleno.

    QUE CAMPO ES IMPRESCINDIBLE LO DICE EL DOMINIO, NO ESTE MODULO
    ---------------------------------------------------------------
    `Docs/definitions.md` marca en negrita lo obligatorio: `Escena.pov`,
    `Escena.lugar` y `Borrador.pov_usado` lo son; `personajes_presentes` y
    `longitud_objetivo` no. La ausencia de un opcional es legitima y la
    invariante simplemente no aplica — si no, esto se vuelve ruido y se aprende
    a ignorarlo, que es el final de cualquier validador.
    """
    return Hallazgo(
        invariante=inv, verificador=VERIFICADOR, escena=escena,
        severidad=TODAS[inv].severidad, estado=EstadoDeHallazgo.SIN_VEREDICTO,
        descripcion="no se pudo comprobar {0} sobre la escena {1}: falta {2}, "
                    "que es lo que se necesita para {3}".format(
                        inv, escena, campo, para),
    )


def verificar(escena, delta, mundo):
    h = []

    if not escena.get("cambio_de_valor"):
        h.append(_hallazgo("INV-01", escena["id"],
                           "la escena no mueve ningun valor dramatico"))

    presentes = escena.get("personajes_presentes", [])
    if presentes and not escena.get("lugar"):
        # La mitad de accesibilidad se saltaba en silencio. `lugar` es
        # obligatorio en el dominio, y sin el no hay contra que comprobar de
        # donde viene nadie.
        h.append(dato_ausente("INV-02", escena["id"], "Escena.lugar",
                              "comprobar la accesibilidad de los presentes"))
    for p in presentes:
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

    # `INV-04` necesita los dos, y los dos son obligatorios en el dominio.
    # Sin cualquiera de ellos no hay comparacion posible, y callarse seria
    # decir que el POV se respeto cuando nadie lo miro (`F-34`).
    falta_pov = [campo for campo, valor in (("Escena.pov", escena.get("pov")),
                                            ("Borrador.pov_usado", escena.get("pov_usado")))
                 if not valor]
    if falta_pov:
        h.append(dato_ausente("INV-04", escena["id"], " y ".join(falta_pov),
                              "comparar el POV planificado con el usado"))
    elif escena["pov"] != escena["pov_usado"]:
        h.append(_hallazgo("INV-04", escena["id"],
                           "el POV planificado es {0} y el usado {1}".format(
                               escena["pov"], escena["pov_usado"])))

    # `longitud_objetivo` es **opcional**: sin rango no hay nada que comprobar
    # y eso es legitimo. Pero con rango y sin recuento, el texto existe y se
    # podia haber contado: no contarlo es no comprobarlo.
    rango = escena.get("longitud_objetivo")
    palabras = escena.get("palabras")
    if rango and palabras is None:
        h.append(dato_ausente("INV-17", escena["id"], "Borrador.palabras",
                              "contrastar la longitud contra el rango previsto"))
    elif rango and not (rango[0] <= palabras <= rango[1]):
        h.append(_hallazgo("INV-17", escena["id"],
                           "{0} palabras, fuera del rango {1}-{2}".format(
                               palabras, rango[0], rango[1])))
    return h
