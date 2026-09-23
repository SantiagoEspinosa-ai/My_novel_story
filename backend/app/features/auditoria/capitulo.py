"""La puerta de cierre de capitulo: la segunda firma humana.

La dispara el cliente de la API, nunca el worker. Y es la que **da sentido a la
primera**: al decidir que un hallazgo `mayor` no detiene la escena, el control
no desaparecio, se movio aqui -que es donde una persona puede juzgar si el
conjunto se sostiene-.

Los `menor` abiertos no bloquean, pero **se listan al firmar**. Si no se
enseñaran, `mayor` y `menor` volverian a producir el mismo comportamiento.
"""

from dataclasses import dataclass

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad as S
from app.commons.invariantes.severidad import (
    impide_cerrar_el_capitulo_por,
    se_lista_al_firmar,
)

COMPLETAS = {EE.CONSOLIDADA, EE.ACEPTADA_POR_RENDICION}

# Un hallazgo sin veredicto cuenta como abierto: su verificador no llego a
# emitir juicio, asi que nadie ha dicho que este bien.
CUENTAN_COMO_ABIERTOS = {EH.ABIERTO, EH.SIN_VEREDICTO}


class NoSePuedeCerrar(Exception):
    pass


@dataclass(frozen=True)
class _Vista:
    """Adaptador: la puerta recibe diccionarios y `severidad.py` decide sobre
    objetos con `severidad` y `estado`. La decision vive en un solo sitio
    (`D-4`) y esto solo le da la forma que espera."""

    fila: dict

    @property
    def severidad(self):
        return self.fila["severidad"]

    @property
    def estado(self):
        return self.fila["estado"]


@dataclass(frozen=True)
class Cierre:
    estado: str
    menores_que_se_dejan_pasar: list


def cerrar(estados_de_escena, hallazgos):
    a_medias = [e for e in estados_de_escena if e not in COMPLETAS]
    if a_medias:
        raise NoSePuedeCerrar(
            "hay {0} escenas que no estan consolidada: un capitulo con escenas "
            "a medias no es un capitulo".format(len(a_medias))
        )
    abiertos = [h for h in hallazgos if h["estado"] in CUENTAN_COMO_ABIERTOS]
    # Se mira el **hallazgo entero**, no solo su severidad (`SPEC-18` C-3):
    # un `sin_veredicto` impide cerrar sea cual sea la severidad que habria
    # tenido la violacion, porque lo que falta es el juicio. Mirando solo la
    # severidad, un `menor` sin veredicto pasaba — y eso es justo un hueco en
    # la auditoria colandose por la puerta que existe para taparlo.
    bloquean = [h for h in abiertos
                if impide_cerrar_el_capitulo_por(_Vista(h))]
    if bloquean:
        raise NoSePuedeCerrar(
            "hay {0} hallazgos `mayor` abiertos: hay que resolverlos o "
            "descartarlos antes de firmar".format(len(bloquean))
        )
    return Cierre(
        estado="cerrado",
        menores_que_se_dejan_pasar=[h for h in abiertos
                                    if se_lista_al_firmar(h["severidad"])],
    )


def reabrir(cierre):
    raise NoSePuedeCerrar(
        "un capitulo cerrado no se reabre: `estado_de_capitulo` tiene dos "
        "valores y una sola transicion"
    )
