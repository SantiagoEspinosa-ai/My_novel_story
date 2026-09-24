"""Dobles de la evaluacion: reproducen lo que un brief declara que deberia pasar.

Tienen la forma de lo real (`llamar(prompt) -> dict`), y lo que devuelven sale del propio
brief —`ficha_esperada`, `hechos_esperados`—, no de la prueba: si el brief cambia, el
doble cambia con el.
"""


class EntrevistadorDelGuion:
    """Devuelve, turno a turno, la `ficha_esperada` de cada respuesta del guion."""

    nombre = "doble-entrevistador"

    def __init__(self, guion):
        self.fichas = [t.ficha_esperada.model_dump(mode="json")
                       for t in guion.turnos if t.respuesta is not None]
        self.i = 0

    def llamar(self, prompt):
        f = self.fichas[min(self.i, len(self.fichas) - 1)]
        self.i += 1
        return {"ficha": f, "pregunta": "pregunta {0}".format(self.i)}


class ExtractorDelGuion:
    """Devuelve los `hechos_esperados` de cada texto libre del guion, en orden."""

    nombre = "doble-extractor"

    def __init__(self, guion):
        self.hechos = [list(t.hechos_esperados) for t in guion.turnos if t.texto_libre]
        self.i = 0

    def llamar(self, prompt):
        h = self.hechos[min(self.i, len(self.hechos) - 1)] if self.hechos else []
        self.i += 1
        return {"hechos": h}
