"""Que le falta a una ficha y como se convierte en brief (`SPEC-25` `RF-02`, `RF-05`).

Lo decide el codigo y no el Entrevistador: un modelo puede dar por terminada una
entrevista a la que le falta la edad, y la ficha pasaria a brief sin que nadie
lo viera. Aqui la lista de obligatorios es una lista, no una impresion.
"""

from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.dominio.enumeraciones import EstadoDeHechoPropuesto as EH
from app.commons.dominio.enumeraciones import TipoDeElementoPersonal as TE


class FichaIncompleta(ValueError):
    def __init__(self, faltan):
        self.faltan = faltan
        super().__init__("la ficha no puede pasar a brief, faltan: {0}".format(
            ", ".join(faltan)))


def que_falta(ficha: FichaDeEntrevista) -> list:
    """Los obligatorios vacios, en el orden del anexo de `SPEC-25`.

    El orden importa: es el de la siguiente pregunta (`RF-07`).
    """
    d = ficha.destinatario
    tipos = {e.tipo for e in d.elementos}
    comprobaciones = [
        ("nombre", bool((d.nombre or "").strip())),
        ("edad", d.edad is not None),
        ("ocasion", ficha.ocasion is not None),
        ("genero", ficha.genero is not None),
        ("tono", ficha.tono is not None),
        ("papel", ficha.papel is not None),
        ("rasgo", TE.RASGO in tipos),
        ("recuerdo", TE.RECUERDO in tipos),
        # `SPEC-25` v3 `RF-02b`: despues de los recuerdos, porque salen de ellos.
        ("premisa", bool((ficha.premisa or "").strip())),
        ("titulo", bool((ficha.titulo or "").strip())),
    ]
    return [nombre for nombre, esta in comprobaciones if not esta]


def a_brief(ficha: FichaDeEntrevista) -> FichaDeEntrevista:
    """La ficha tal como la leera el Escritor: completa y solo con lo confirmado.

    Los hechos propuestos o descartados no pasan: un hecho extraido del texto
    libre que el comprador no confirmo no es algo que el comprador haya dicho
    (`RF-13`).
    """
    faltan = que_falta(ficha)
    if faltan:
        raise FichaIncompleta(faltan)
    return ficha.model_copy(update={"hechos_propuestos": [
        h for h in ficha.hechos_propuestos if h.estado is EH.CONFIRMADO]})
