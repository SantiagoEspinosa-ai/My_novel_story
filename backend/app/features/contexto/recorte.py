"""El recorte en dos vueltas.

    1. Reduce todo lo reducible, en orden.
    2. Solo despues elimina bloques enteros, tambien en orden.
    3. Si aun no cabe, `RF-26`: **falla en vez de generar**.

Nunca se trunca por el final y nunca se parte un bloque.

POR QUE SE ITERA SOBRE ESTA LISTA Y NO SOBRE LOS SEIS NIVELES
--------------------------------------------------------------
Porque el nivel `Recuperado` se parte en dos bloques que caen a distinto lado
de la frontera. `simular_recorte_por_niveles` existe solo para que el caso
negativo de `VER-06` pueda demostrarlo en vez de afirmarlo.
"""

from dataclasses import dataclass

from app.features.contexto.bloques import BLOQUES, FRACCION_REDUCIDA, Clase


@dataclass(frozen=True)
class Paso:
    bloque: str
    clase: Clase


class NoCabe(Exception):
    """`RF-26`. Lleva el plan que se llego a aplicar, para el informe."""

    def __init__(self, mensaje, plan):
        super().__init__(mensaje)
        self.plan = plan


def _total(tam):
    return sum(tam.values())


def planificar(tamanos: dict, techo: int):
    """Devuelve la lista de pasos aplicados. Levanta `NoCabe` si no cabe."""
    tam = dict(tamanos)
    plan = []
    if _total(tam) <= techo:
        return plan

    # Vuelta 1: reducir.
    for b in BLOQUES:
        if b.forma_reducida is None:
            continue
        if tam.get(b.nombre, 0) == 0:
            continue
        tam[b.nombre] = int(tam[b.nombre] * FRACCION_REDUCIDA)
        plan.append(Paso(b.nombre, Clase.REDUCCION))
        if _total(tam) <= techo:
            return plan

    # Vuelta 2: eliminar, solo los tres primeros.
    for b in BLOQUES:
        if not b.eliminable:
            continue
        if tam.get(b.nombre, 0) == 0:
            continue
        tam[b.nombre] = 0
        plan.append(Paso(b.nombre, Clase.ELIMINACION))
        if _total(tam) <= techo:
            return plan

    raise NoCabe(
        "el contexto no cabe tras agotar las formas reducidas y eliminar los "
        "tres primeros bloques: el trabajo falla en vez de generar (RF-26)",
        plan,
    )


def simular_recorte_por_niveles(tamanos: dict, techo: int):
    """El error que `VER-06` tiene que cazar, hecho codigo para poder probarlo.

    Recorre los seis niveles de `CLAUDE.md` en vez de los bloques de 2.4. Al
    llegar a `Recuperado` se lleva **los dos** bloques que salen de el, y con
    ellos el registro de conocimiento: `INV-03` queda sin entrada y la puerta
    sigue en pie sin poder decidir.
    """
    orden_de_niveles = ["Resumenes", "Recuperado", "Local",
                        "Estado actual + Recuperado", "Salida", "Inmutable"]
    tam = dict(tamanos)
    eliminados = []
    for nivel in orden_de_niveles:
        for b in BLOQUES:
            if nivel in b.nivel and tam.get(b.nombre, 0):
                tam[b.nombre] = 0
                eliminados.append(b.nombre)
        if _total(tam) <= techo:
            break
    return eliminados
