"""La logica del alta de obra.

Hoy es fina a proposito: el alta no llama al modelo ni verifica nada. Existe
como fichero porque `A-01` dice que todas las features tienen la misma forma, y
una feature a la que le falte el servicio invita a poner logica en el router.
"""

from app.features.brief import repository


def dar_de_alta(con, entrada: dict) -> str:
    return repository.crear(con, entrada)


def consultar(con, id_obra: str):
    return repository.leer(con, id_obra)
