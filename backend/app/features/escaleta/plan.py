"""Validacion de la escaleta: las invariantes en su forma prevista.

"En su forma prevista" significa **contra el plan, antes de que exista texto**.
El Escaletador puede decir si una escena planificada tiene `cambio_de_valor` y
si sus beats sirven a un arco; no puede decir si el texto que se escriba
despues los realiza. Por eso estas cuatro se comprueban dos veces y el Auditor
no sobra: un plan correcto que se ejecuta mal sigue fallando.
"""

from app.commons.dominio.enumeraciones import EjeDeValor, SignoDeCambio
from app.commons.invariantes import registro

INVARIANTES_PREVISTAS = ("INV-01", "INV-07", "INV-12", "INV-16")


def invariantes_previstas(genero):
    """`SPEC-26` `RF-20`: la curva de miedo (`INV-12`, `INV-16`) solo se preve en
    una obra de terror. En otra seria exigirle al plan algo que no quiere."""
    return tuple(i for i in INVARIANTES_PREVISTAS if registro.aplica(i, genero))
SUSTITUYE_AL_AUDITOR = False


class EscaletaInvalida(Exception):
    pass


def validar(escenas):
    for e in escenas:
        cv = e.get("cambio_de_valor")
        if not cv:
            raise EscaletaInvalida(
                "INV-01 en su forma prevista: la escena {0} no cambia ningun "
                "valor. Si no cambia nada, sobra".format(e.get("id"))
            )
        try:
            EjeDeValor(cv["eje"])
            SignoDeCambio(cv["signo"])
        except (KeyError, ValueError) as exc:
            # Un valor fuera de la enumeracion es un error de validacion, no
            # un aviso. Se traduce al error de la feature para que quien la
            # llama no tenga que conocer los tipos de `commons/dominio/`.
            raise EscaletaInvalida(
                "cambio_de_valor fuera de esquema en la escena {0}: {1}".format(
                    e.get("id"), exc)
            ) from exc
        if not e.get("beats"):
            raise EscaletaInvalida(
                "INV-07 en su forma prevista: la escena {0} no realiza ningun "
                "beat que sirva a un arco".format(e.get("id"))
            )
    return escenas
