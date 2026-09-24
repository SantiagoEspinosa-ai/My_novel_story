"""La maquina de estados de la escena, con quien dispara cada transicion.

Es la copia en codigo de la tabla de `docs/architecture.md`, y como con el
registro de invariantes se escribe a mano: generarla leyendo el documento
dejaria a su validador comparandolo consigo mismo.

`todos_los_caminos` explora la maquina entera en vez de probar un camino. Un
camino que pasa no dice nada de los otros, y lo que `VER-28` afirma es que
**ninguno** salta la puerta.
"""

from app.commons.dominio.enumeraciones import EstadoDeEscena as E


class TransicionIlegal(Exception):
    pass


DISPARADORES = {
    (E.PLANIFICADA, E.GENERADA): "Worker",
    (E.GENERADA, E.EN_VERIFICACION): "Orquestador",
    (E.EN_VERIFICACION, E.RECHAZADA): "Verificador de reglas",
    (E.EN_VERIFICACION, E.EN_REVISION): "Juez de rubrica",
    (E.EN_VERIFICACION, E.ACEPTADA): "Orquestador",
    (E.RECHAZADA, E.GENERADA): "Persona desde el frontend",
    (E.EN_REVISION, E.GENERADA): "Revisor",
    (E.EN_REVISION, E.ACEPTADA_POR_RENDICION): "Orquestador",
    (E.ACEPTADA, E.CONSOLIDADA): "Consolidador",
}


def destinos(origen):
    return {d for (o, d) in DISPARADORES if o is origen}


def mover(origen, destino):
    if (origen, destino) not in DISPARADORES:
        raise TransicionIlegal(
            "{0} -> {1} no es legal. El cuerpo del 409 dice que estado tiene y "
            "cual se esperaba".format(origen.value, destino.value)
        )
    return destino


def todos_los_caminos(origen, destino, visitados=None):
    """Exploracion exhaustiva. La maquina es aciclica salvo los rebotes a
    `generada`, que se cortan con `visitados`."""
    visitados = visitados or ()
    if origen in visitados:
        return []
    visitados = visitados + (origen,)
    if origen is destino:
        return [visitados]
    caminos = []
    for d in destinos(origen):
        caminos.extend(todos_los_caminos(d, destino, visitados))
    return caminos
