"""Que hace cada severidad, implementado una vez.

`D-4` de `SPEC-01` y `Docs/architecture.md`: la diferencia entre severidades se
implementa aqui y **no se resuelve caso por caso en cada verificador**. Si cada
uno decidiera por su cuenta que hacer con un `mayor`, la escala seria una
sugerencia.

LAS TRES REGLAS, Y DONDE VIVE CADA DIFERENCIA
---------------------------------------------
    bloqueante  detiene la escena en la puerta. No pasa a `aceptada`.
    mayor       genera hallazgo y deja seguir, pero impide cerrar el capitulo.
    menor       genera hallazgo, deja seguir y solo se lista al firmar.

La diferencia entre `mayor` y `menor` esta **una puerta mas arriba**, no en la
escena: las dos dejan pasar la escena y se separan en el cierre de capitulo
(`SPEC-04` C-2). Sin esa puerta las dos producirian exactamente el mismo
comportamiento, y una escala cuyos valores no se distinguen en nada es una
etiqueta, no un control.
"""

from app.commons.dominio.enumeraciones import Severidad


def detiene_la_escena(severidad: Severidad) -> bool:
    """`bloqueante` detiene la escena en la puerta; las otras dos no."""
    return severidad is Severidad.BLOQUEANTE


def impide_cerrar_el_capitulo(severidad: Severidad) -> bool:
    """Un `mayor` abierto impide firmar el capitulo; un `menor` no.

    `bloqueante` no llega a plantearse: una escena con una abierta no esta
    `consolidada`, asi que el capitulo no esta completo (`SPEC-04` C-2).
    """
    return severidad is Severidad.MAYOR


def se_lista_al_firmar(severidad: Severidad) -> bool:
    """Los `menor` abiertos se enseñan al cerrar, para que quien firma vea
    que deja pasar. Si no se enseñaran, `mayor` y `menor` volverian a ser lo
    mismo."""
    return severidad is Severidad.MENOR


# --- SPEC-18 C-3: un `sin_veredicto` no es una violacion -------------------
#
# Las tres funciones de arriba miran **la severidad**, que dice cuanto pesa una
# violacion CONFIRMADA. Un hallazgo cuyo `estado` es `sin_veredicto` no afirma
# que nada se haya roto: afirma que **no se pudo mirar**, y tratarlo igual hacia
# que un dato ausente detuviera la obra como una violacion (`F-36`).
#
# Tampoco puede pasar como exito: `SPEC-10` C-2 decidio que quien no se dejo
# auditar no gana por defecto. El sitio donde las dos cosas son verdad a la vez
# es el cierre de capitulo, que es exactamente donde vive un `mayor`.
#
# Estas dos funciones reciben el **hallazgo**, no la severidad, y son las que
# debe usar quien decide. Las de arriba se quedan porque siguen siendo la
# definicion de cada severidad, y `D-4` exige que esa definicion viva una vez.

def _sin_veredicto(hallazgo) -> bool:
    return str(getattr(hallazgo, "estado", "")) == "sin_veredicto"


def detiene_la_escena_por(hallazgo) -> bool:
    """Solo una violacion confirmada detiene la escena."""
    if _sin_veredicto(hallazgo):
        return False
    return detiene_la_escena(hallazgo.severidad)


def impide_cerrar_el_capitulo_por(hallazgo) -> bool:
    """Un `mayor` abierto **y** cualquier cosa que no se pudo comprobar."""
    if _sin_veredicto(hallazgo):
        return True
    return impide_cerrar_el_capitulo(hallazgo.severidad)
