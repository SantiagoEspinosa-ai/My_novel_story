"""Lo que devuelve la novela regalo en la web (`SPEC-33`).

Ningun nombre de aqui puede ser el de una seccion o una clave de `config/sistema.json`
(`SPEC-22` `RF-57`): por eso una nota dice `bajo_el_umbral` y no trae el umbral.
"""

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio


class NotaDelEditor(_DelDominio):
    """Una `ValoracionDelEditor` del borrador aceptado. `bajo_el_umbral` es `INV-26`
    (`nota < umbral`), resuelto en el backend."""

    criterio: enums.CriterioDeEdicion
    nota: int
    justificacion: str
    instruccion: str | None
    bajo_el_umbral: bool


class CapituloEnGeneracion(_DelDominio):
    """`RF-14`: `fase` es la de la ultima fila de progreso con este capitulo, o nula si la
    generacion no ha llegado a el. Nula no es un valor de `fase_de_generacion`."""

    numero: int
    fase: enums.FaseDeGeneracion | None
    motivo: str | None
    desde: str | None
    notas: list[NotaDelEditor]


class CosteDeLaGeneracion(_DelDominio):
    """`RF-19`, `RF-20`. `usd` es nulo si ninguna delegacion trajo coste; con alguna sin
    coste, es un suelo y `es_suelo` lo dice."""

    generacion: str
    usd: float | None
    delegaciones: int
    sin_coste: int
    es_suelo: bool


class GeneracionEnVivo(_DelDominio):
    obra: str
    total_de_capitulos: int
    capitulos: list[CapituloEnGeneracion]
    coste: CosteDeLaGeneracion | None
