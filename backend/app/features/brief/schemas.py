"""Esquemas de entrada y salida del alta de obra: la frontera de validacion.

`CLAUDE.md`: "Los modelos Pydantic son la frontera de validacion y replican las
clases de `docs/definitions.md`. Un campo que no esta definido alli no entra en
un esquema." La base `_DelDominio` ya trae `extra="forbid"`, asi que un campo
inventado no entra en silencio: sale por el 422.
"""

from pydantic import Field

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio


class BriefEntrada(_DelDominio):
    """Lo que hace falta para dar de alta una `Obra`.

    Solo `titulo` y `premisa` son obligatorios, que es lo que dice la ficha de
    `Obra`. `persona` y `tiempo_verbal` son de `GuiaDeEstilo` y entran aqui
    porque sin ellos el Escaletador no puede empezar; el resto de la guia llega
    con su propia feature.
    """

    titulo: str = Field(min_length=1)
    premisa: str = Field(min_length=1)
    genero: str | None = None
    subgenero: str | None = None
    extension_objetivo: int | None = Field(default=None, gt=0)
    persona: enums.PersonaNarrativa | None = None
    tiempo_verbal: enums.TiempoVerbal | None = None


class ObraSalida(_DelDominio):
    """Una obra nunca se devuelve sin su estructura.

    `RF-23` lo dice para la escena -texto, estado y hallazgos abiertos, nunca el
    texto solo- y el motivo vale igual aqui: un dato suelto induce a darlo por
    bueno. Una obra recien creada devuelve `capitulos: []`, que es informacion,
    no un hueco.
    """

    id: str
    titulo: str
    premisa: str
    genero: str | None = None
    capitulos: list[str] = Field(default_factory=list)
