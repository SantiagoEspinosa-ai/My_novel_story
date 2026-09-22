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
