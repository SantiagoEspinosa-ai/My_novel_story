"""Regenerar en una obra acumulativa (`SPEC-23` v2, `PLAN-23`).

Compone features, que es lo unico autorizado a `orquestacion/` (`A-02`): el plan
aprobado es de `planificacion/`, el mundo y los deltas de `consolidacion/`, las
versiones de `brief/` y las escenas de `escaleta/`.

**Ningun paso de este modulo llama al modelo.** Lo que cuesta dinero -escribir los
capitulos nuevos- es de la Parte B, y va con la salida que elija la medida.
"""

import sqlite3

from app.features.consolidacion.mundo import ANTERIOR_AL_RELATO
from app.features.planificacion import repository as planes


class SinSemilla(Exception):
    """Sin plan aprobado no hay semilla: no se sabe de que mundo parte la obra."""


def semilla_de(con, obra):
    """El mundo **antes del capitulo 1** de la obra, en la forma de `mundo.leer`.

    Personajes, lugares y accesos salen del plan aprobado. El conocimiento inicial,
    de las filas `anterior_al_relato` del registro: es lo que sembro `novela.montar`,
    incluido lo que sale de la ficha -que el destinatario conoce sus imprescindibles-,
    y la ficha se borra al entregar (`SPEC-25` `RF-21`), asi que no se puede volver a
    calcular. Lo revelado por una escena no es semilla: es de su delta.
    """
    planes.asegurar_tablas(con)
    plan = planes.aprobado(con, obra)
    if plan is None:
        raise SinSemilla(
            "la obra {0} no tiene plan aprobado: sin el no se sabe de que mundo parte, "
            "y reconstruir su estado seria inventarlo".format(obra))
    conocimiento = {}
    try:
        filas = con.execute("SELECT sujeto, hecho, grado FROM conocimiento "
                            "WHERE desde_escena IS NULL AND fuente = ?",
                            (ANTERIOR_AL_RELATO,)).fetchall()
    except sqlite3.OperationalError:
        # Sin tabla de conocimiento nadie sembro nada: la semilla no sabe nada.
        filas = []
    for sujeto, hecho, grado in filas:
        conocimiento[(sujeto, hecho)] = {"desde": None, "grado": grado}
    return {
        "entidades_vivas": {p.id: p.estado_vital.value for p in plan.mundo.personajes},
        "ubicaciones": {p.id: p.empieza_en for p in plan.mundo.personajes},
        "accesos": {l.id: list(l.accesos) for l in plan.mundo.lugares},
        "conocimiento": conocimiento,
    }
