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


def cerrar(estados_de_escena, hallazgos, orden_temporal=None):
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
    # `INV-08` es de **nivel capitulo**, asi que su sitio es esta puerta y no
    # `verificacion/puertas.py`, que ejecuta las de nivel escena. Estaba
    # declarada, con su consulta escrita y sus pruebas en verde, y **no la
    # llamaba nadie** (`F-47`): desde fuera no se distinguia de una que si se
    # ejecuta. La lo detecto la verificacion formal al escribir la misma regla
    # en Lean y preguntarse contra que contrastarla.
    #
    # El dato lo trae quien compone -`orquestacion/`- porque esta feature no
    # puede importar de `cronologia/` (`A-02`).
    if orden_temporal is not None:
        inversiones = orden_temporal.get("inversiones") or []
        if inversiones:
            raise NoSePuedeCerrar(
                "`INV-08`: el capitulo avanza y el tiempo de la fabula "
                "retrocede en {0} sitio(s) {1}. Una analepsis es exactamente "
                "eso y no es un error, pero **hoy no hay donde declararla**, "
                "asi que toda inversion sale aqui hasta que lo haya".format(
                    len(inversiones), inversiones[:3]))
        sin_fecha = orden_temporal.get("sin_fecha_legible") or []
        if sin_fecha:
            # Regla 8: *no se pudo comprobar* no es *se comprobo y esta bien*.
            # Cerrar aqui seria firmar que el orden temporal es correcto
            # habiendo mirado cero escenas.
            raise NoSePuedeCerrar(
                "`INV-08` no se pudo comprobar: {0} escena(s) sin `t_fabula` "
                "legible {1}. Sin fecha no hay orden temporal que verificar, y "
                "eso **no es lo mismo que estar en orden**".format(
                    len(sin_fecha), sin_fecha[:3]))

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
