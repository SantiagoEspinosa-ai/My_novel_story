"""Entregar una obra: borrar la entrevista y conservar la novela (`SPEC-25` `RF-21`).

Vive en `orquestacion/` porque compone dos features (`PLAN-25` v2): copia las
vetadas de la ficha a `politica/` y **despues** borra la entrevista. En ese
orden: si se borrara primero y la copia fallara, las regeneraciones del lector
perderian el guardrail sin que nada lo avisara.

QUE SE BORRA Y QUE NO
---------------------
Se borran la conversacion y la ficha. El texto libre no hace falta borrarlo
porque nunca se guardo: solo sus hechos, dentro de la ficha. Se conservan la
novela, las vetadas de la novela y los hechos de la story bible.

LA MARCA DE ENTREGADA ES EL AUDIT LOG
-------------------------------------
La tabla `obra` no tiene estado, y darselo pediria una migracion que el plan no
contempla. La fila `borrado_al_entregar` ya es inmutable y dice cuando: es la
marca, y es lo que hace que entregar dos veces no duplique nada.
"""

from app.commons.dominio.enumeraciones import NivelDeVeto as NV
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.politica import auditoria
from app.features.entrevista import repository as entrevistas
from app.features.politica import repository as politica


class NoSePuedeEntregar(RuntimeError):
    pass


def entregada(con, obra) -> bool:
    return any(d["tipo"] is TD.BORRADO_AL_ENTREGAR
               for d in auditoria.decisiones(con, obra))


def entregar(con, obra) -> dict:
    """Idempotente: una obra ya entregada devuelve lo que se registro entonces."""
    politica.asegurar_tablas(con)
    entrevistas.asegurar_tablas(con)
    for d in auditoria.decisiones(con, obra):
        if d["tipo"] is TD.BORRADO_AL_ENTREGAR:
            return d["detalle"]
    abiertas = [i for i in entrevistas.de_la_obra(con, obra)
                if not entrevistas.leer(con, i).cerrada]
    if abiertas:
        raise NoSePuedeEntregar(
            "la entrevista {0} sigue abierta: borrarla perderia lo que dijo el "
            "comprador antes de que sirviera para nada".format(", ".join(abiertas)))
    for i in entrevistas.de_la_obra(con, obra):
        ficha = entrevistas.leer(con, i).ficha
        politica.vetar_en_novela(con, obra, palabras=ficha.vetadas,
                                 nombres=ficha.nombres_vetados)
    conservadas = sum(1 for v in politica.vetadas_para(con, obra, None, [])
                      if v.nivel is NV.NOVELA)
    borrado = entrevistas.borrar_de_la_obra(con, obra)
    detalle = dict(borrado, vetadas_conservadas=conservadas)
    auditoria.registrar_decision(con, TD.BORRADO_AL_ENTREGAR, obra, detalle)
    return detalle
