"""Los esquemas de las tres tools de lectura de la story bible (`SPEC-28`).

Replican clases de `docs/definitions.md` —`HechoCanonico` y la relacion `usa`,
`Personaje`, `Lugar`, `EventoCronologico`— y nada mas: un campo que no esta alli no
entra (`CLAUDE.md` § "FastAPI").

TRES REGLAS QUE VIVEN EN LOS TIPOS
----------------------------------
- **Ninguna salida lleva el texto de una escena** (`RF-05`): una tool es otra forma de
  mandar texto al modelo, y el texto de las escenas no se manda.
- **La obra no es argumento de ninguna entrada** (`RF-06`, `D-4`): la fija el harness en
  el servidor. `extra="forbid"` hace que pedir otra obra sea un error de validacion.
- **`hechos` devuelve cada uso con su tipo**, todos los tipos: `SPEC-21` `C-2` deja a
  cada consumidor elegir cuales cuentan, y la tool no elige por el.

`alias`, `rol_dramatico` y `atmosfera` salen vacios hoy (`D-5`): no los guarda ninguna
tabla ni el plan, y se dice en vez de inventarlos.
"""

from pydantic import Field, model_validator

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio


class EntradaHechos(_DelDominio):
    hecho: str | None = Field(default=None, description="Un hecho concreto, o todos")


class UsoDeHecho(_DelDominio):
    capitulo: str | None = None
    tipo: enums.TipoDeUsoDeHecho


class HechoConUsos(_DelDominio):
    id: str
    enunciado: str
    usos: list[UsoDeHecho] = Field(default_factory=list)


class SalidaHechos(_DelDominio):
    hechos: list[HechoConUsos] = Field(default_factory=list)


class EntradaFicha(_DelDominio):
    id: str = Field(min_length=1, description="El id de un personaje o de un lugar")


class FichaDePersonaje(_DelDominio):
    """`SPEC-22` `RF-43`."""

    id: str
    nombre_canonico: str
    alias: list[str] = Field(default_factory=list)
    rol_dramatico: enums.RolDramatico | None = None
    estado_vital: enums.EstadoVital


class FichaDeLugar(_DelDominio):
    id: str
    nombre: str
    atmosfera: str | None = None


class SalidaFicha(_DelDominio):
    personaje: FichaDePersonaje | None = None
    lugar: FichaDeLugar | None = None

    @model_validator(mode="after")
    def _una_y_solo_una(self):
        if (self.personaje is None) == (self.lugar is None):
            raise ValueError("una ficha es de un personaje o de un lugar, y solo de uno")
        return self


class EntradaCronologia(_DelDominio):
    capitulo: str | None = Field(default=None, description="Un capitulo, o toda la obra")


class EventoDeLaCronologia(_DelDominio):
    """De `EventoCronologico`, sin `descripcion`: no es atributo de la clase."""

    id: str
    t_fabula: str | None = None
    duracion_min: int | None = None
    lugar: str | None = None
    capitulo: str | None = None
    personajes_presentes: list[str] = Field(default_factory=list)


class SalidaCronologia(_DelDominio):
    eventos: list[EventoDeLaCronologia] = Field(default_factory=list)
