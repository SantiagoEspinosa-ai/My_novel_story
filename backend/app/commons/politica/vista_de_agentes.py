"""La ficha tal como la ven los agentes (`SPEC-40`, `PLAN-40` Q1).

`F-146` siguio con `SPEC-34`: el Planificador recibio el pseudonimo del destinatario y lo
escribio como `[NOMBRE_ANONIMIZADO]`. La politica de la organizacion no mira si el nombre es
real: mira que sea **la persona que recibe el regalo**, y los prompts se lo decian. Aqui el
destinatario pasa a ser `protagonista` y se quitan quien regala, la dedicatoria y los nombres
vetados. La base guarda la ficha tal cual; esto se hace en la frontera.

`PALABRAS_DEL_REGALO` es la guarda: ningun prompt ni definicion de agente del pipeline las
lleva (`RF-02`, `RF-05`).
"""

import re

PALABRAS_DEL_REGALO = re.compile(
    r"destinatari[oa]s?|regal\w*|comprador\w*|dedicatoria\w*", re.IGNORECASE)

_FUERA = ("regalado_por", "dedicatoria", "nombres_vetados")


def ficha_para_agentes(ficha) -> dict:
    """La ficha como diccionario, con el `protagonista` y sin lo que dice que es un regalo."""
    d = ficha.model_dump(mode="json")
    for campo in _FUERA:
        d.pop(campo, None)
    d["protagonista"] = d.pop("destinatario")
    return d


def ficha_desde_agentes(datos) -> dict:
    """Lo que devuelve un agente, leido de vuelta: `protagonista` es el `destinatario`."""
    if isinstance(datos, dict) and "protagonista" in datos and "destinatario" not in datos:
        datos = dict(datos)
        datos["destinatario"] = datos.pop("protagonista")
    return datos
