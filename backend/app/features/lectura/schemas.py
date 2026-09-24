"""Lo que la lectura web recibe. Es el contrato (`SPEC-22` `RF-31`).

Cada campo es un atributo de `docs/definitions.md` o una de sus **vistas derivadas de la
lectura** (`se_acepto_rindiendose`, `hallazgos_abiertos[]`, `capitulos_donde_aparece[]`).
Los estados y la severidad viajan como su `Enum`, no como cadenas (`RF-34`), y lo que no
consta viaja nulo, nunca como cero ni como lista vacia (`RF-35`).
"""

from pydantic import BaseModel, Field

from app.commons.dominio.enumeraciones import EstadoDeCapitulo, EstadoDeEscena
from app.commons.dominio.enumeraciones import EstadoDeHallazgo, Severidad


class HallazgoAbierto(BaseModel):
    """Un `Hallazgo` con estado `abierto` o `sin_veredicto`, con **su** estado."""

    invariante: str = Field(description="La INV-xx que se violo o no se pudo comprobar")
    verificador: str = Field(description="Quien lo detecto")
    severidad: Severidad
    estado: EstadoDeHallazgo = Field(
        description="sin_veredicto es que falto el juicio, no que se violara")
    descripcion: str


class EscenaDelIndice(BaseModel):
    """Una escena en el indice: su estado y sus hallazgos, **nunca** sin ellos (`RF-39`)."""

    id: str
    capitulo: str = Field(description="El id del Capitulo que la contiene; nunca el de la obra")
    estado: EstadoDeEscena
    se_acepto_rindiendose: bool = Field(
        description="Resuelto en el backend: estado == aceptada_por_rendicion (RF-40)")
    hallazgos_abiertos: list[HallazgoAbierto]


class CapituloDelIndice(BaseModel):
    id: str = Field(description="El id del Capitulo; nunca el de la obra (RF-37)")
    orden: int = Field(description="Orden de lectura; la lista ya viene en este orden")
    estado: EstadoDeCapitulo
    escenas: list[EscenaDelIndice] = Field(description="En orden de lectura")


class Indice(BaseModel):
    """La portada y el indice de una obra, resueltos (`RF-38`, `RF-46`).

    No lleva partes: la base no tiene tabla `parte` y el plan de la novela regalo no las
    declara (`PLAN-22` cuestion 3). No se pinta lo que no hay.
    """

    id: str = Field(description="El id de la Obra")
    titulo: str
    dedicatoria: str | None = Field(description="Nula si la obra no tiene; nunca un relleno")
    capitulos: list[CapituloDelIndice] = Field(description="Por Capitulo.orden")
