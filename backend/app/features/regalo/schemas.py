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


class Gastado(_DelDominio):
    """Lo gastado en toda la base. **Siempre es un suelo**: lo anterior a la migracion 18
    no tiene coste guardado, y `por_que_es_suelo` lo dice (decision del autor, `SPEC-33`)."""

    usd: float | None
    delegaciones: int
    sin_coste: int
    es_suelo: bool
    por_que_es_suelo: str


class Referencia(_DelDominio):
    """Una medida de **otra** base, con su fuente: se ensena como referencia."""

    usd: float
    delegaciones: int
    fuente: str


class ConfirmacionDeGasto(_DelDominio):
    """`RF-12`: las tres cifras que la web ensena antes de gastar. `alcanzado` es
    `usd >= techo_usd`, resuelto aqui; el backend tambien lo impone al lanzar (`RF-13`)."""

    gastado: Gastado
    techo_usd: float
    alcanzado: bool
    ultima: CosteDeLaGeneracion | None
    referencia: Referencia


class ObraEnLaEstanteria(_DelDominio):
    """`RF-01`..`RF-03`. `titulo` es nulo mientras la obra solo tiene entrevista; `fase`, si
    no ha empezado ninguna generacion; `destinatario` y `entrevista`, si la ficha se borro."""

    id: str
    titulo: str | None
    dedicatoria: str | None
    destinatario: str | None
    fase: enums.FaseDeGeneracion | None
    entrevista: str | None
    entrevista_cerrada: bool | None


class Estanteria(_DelDominio):
    obras: list[ObraEnLaEstanteria]


class GeneracionEnVivo(_DelDominio):
    obra: str
    total_de_capitulos: int
    capitulos: list[CapituloEnGeneracion]
    coste: CosteDeLaGeneracion | None
