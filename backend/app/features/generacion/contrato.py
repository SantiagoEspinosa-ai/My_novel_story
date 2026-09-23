"""El contrato de la respuesta del Escritor.

Devuelve **dos cosas en la misma llamada**: el texto y el diff estructurado de
lo que ha cambiado en el mundo. Pedir el delta despues, releyendo la escena, es
mas caro y menos fiel.

Lo que aqui se rechaza es un **fallo de contrato**, no un hallazgo: ocurre
antes de las puertas, no produce `Hallazgo` y por `O-3` **no se reintenta**,
porque repetirlo repite el error. Lo ve una persona.
"""

from dataclasses import dataclass

import re

from app.commons.dominio.enumeraciones import EjeDeValor, SignoDeCambio

# Un identificador del dominio: ASCII, sin espacios y sin acentos. Lo que no
# encaja aqui es prosa, y la prosa en un campo de referencia es un fallo de
# **contrato**: si llega a la puerta, `INV-03` lo denunciara como "actua sobre
# un hecho que no conoce", que describe mal el defecto y hereda una severidad
# `bloqueante` que no le corresponde (Regla 4 de `Docs/verification.md`).
IDENTIFICADOR = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


class FalloDeContrato(Exception):
    pass


@dataclass(frozen=True)
class Respuesta:
    texto: str
    delta: dict


def leer(bruto: dict) -> Respuesta:
    texto = (bruto or {}).get("texto")
    if not texto or not texto.strip():
        raise FalloDeContrato(
            "la respuesta no trae texto. Un vacio que pasa es peor que un "
            "fallo: entra en el manuscrito sin que nada lo marque"
        )
    delta = bruto.get("delta")
    if not delta:
        raise FalloDeContrato(
            "la respuesta no trae delta. El Escritor devuelve dos cosas en la "
            "misma llamada; extraerlo despues releyendo la escena es mas caro "
            "y menos fiel"
        )
    cv = delta.get("cambio_de_valor")
    if not cv:
        raise FalloDeContrato("el delta no declara `cambio_de_valor`")
    try:
        EjeDeValor(cv["eje"])
        SignoDeCambio(cv["signo"])
    except (KeyError, ValueError) as e:
        raise FalloDeContrato("`cambio_de_valor` fuera de esquema: {0}".format(e))
    # Las dos listas de referencias del delta cruzan la **misma** frontera, y
    # por eso se recorren con el mismo bucle: duplicarlo dejaria dos copias de
    # la misma regla, y la que se olvidara de actualizar seria justo la que
    # dejaria pasar una frase (`SPEC-16`).
    for lista, campos in (("revelaciones", ("sujeto", "hecho")),
                          ("acciones", ("personaje", "hecho"))):
        for i, entrada in enumerate(delta.get(lista) or []):
            for campo in campos:
                valor = entrada.get(campo)
                if not isinstance(valor, str) or not IDENTIFICADOR.match(valor):
                    raise FalloDeContrato(
                        "{0}[{1}].{2} tiene que ser un identificador y es "
                        "{3!r}. `SPEC-03` decidio referencias, no prosa: una "
                        "frase aqui llega a `INV-03`, que la denuncia como un "
                        "personaje actuando sobre un hecho que no conoce y le "
                        "da severidad bloqueante. El defecto es de "
                        "formato".format(lista, i, campo, valor))
    return Respuesta(texto=texto, delta=delta)
