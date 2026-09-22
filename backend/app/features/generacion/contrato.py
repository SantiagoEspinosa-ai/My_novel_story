"""El contrato de la respuesta del Escritor.

Devuelve **dos cosas en la misma llamada**: el texto y el diff estructurado de
lo que ha cambiado en el mundo. Pedir el delta despues, releyendo la escena, es
mas caro y menos fiel.

Lo que aqui se rechaza es un **fallo de contrato**, no un hallazgo: ocurre
antes de las puertas, no produce `Hallazgo` y por `O-3` **no se reintenta**,
porque repetirlo repite el error. Lo ve una persona.
"""

from dataclasses import dataclass

from app.commons.dominio.enumeraciones import EjeDeValor, SignoDeCambio


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
    return Respuesta(texto=texto, delta=delta)
