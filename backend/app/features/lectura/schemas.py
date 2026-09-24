"""Lo que la lectura web recibe. Es el contrato (`SPEC-22` `RF-31`).

Cada campo es un atributo de `docs/definitions.md` o una de sus **vistas derivadas de la
lectura** (`se_acepto_rindiendose`, `hallazgos_abiertos[]`, `capitulos_donde_aparece[]`).
Los estados y la severidad viajan como su `Enum`, no como cadenas (`RF-34`), y lo que no
consta viaja nulo, nunca como cero ni como lista vacia (`RF-35`).
"""

from pydantic import BaseModel, Field

from app.commons.dominio.enumeraciones import EstadoDeCapitulo, EstadoDeEscena
from app.commons.dominio.enumeraciones import EstadoDeHallazgo, EstadoVital, RolDramatico
from app.commons.dominio.enumeraciones import Severidad


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
    capitulo: str | None = Field(
        description="El id del Capitulo que la contiene; nunca el de la obra. Nulo solo en "
                    "escaletas anteriores a SPEC-21, que no lo guardaban")
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


class BorradorElegido(BaseModel):
    """El `Borrador` elegido de la escena: el aceptado o, si no consta, el ultimo."""

    version: int = Field(description="Borrador.version: el ancla de una seleccion (RF-47)")
    texto: str = Field(description="Byte a byte el del borrador, sin tocar (VER-60)")


class EscenaLeida(EscenaDelIndice):
    """Una escena para leer: la del indice mas su texto. **Nunca** el texto sin estado."""

    borrador: BorradorElegido | None = Field(
        description="Nulo si la escena no tiene ningun borrador (p. ej. planificada)")


class CapituloLeido(BaseModel):
    """Un capitulo de corrido: sus escenas en orden, **una por bloque** (`RF-41`).

    Lo ensambla el backend -que escenas entran y en que orden-, pero no junta los
    textos: cada escena lleva el suyo con su estado y sus hallazgos (`RF-39`).
    """

    id: str = Field(description="El id del Capitulo; nunca el de la obra (RF-37)")
    orden: int
    estado: EstadoDeCapitulo
    escenas: list[EscenaLeida] = Field(description="En orden de lectura")


class CapituloEnlazado(BaseModel):
    """Una referencia a un `Capitulo`: su id y su orden, para enlazarlo y nombrarlo."""

    id: str = Field(description="El id del Capitulo; nunca el de la obra (RF-37)")
    orden: int


class FichaDePersonaje(BaseModel):
    """`Personaje` (`RF-43`). Lo que la base no guarda viaja nulo: «sin dato», no «ninguno»."""

    id: str
    nombre_canonico: str | None = Field(description="Nulo si la base no lo guarda (PLAN-27 E2)")
    alias: list[str] | None = Field(description="Nulo: la base no guarda alias")
    rol_dramatico: RolDramatico | None = Field(description="Nulo: la base no lo guarda")
    estado_vital: EstadoVital | None
    capitulos_donde_aparece: list[CapituloEnlazado] | None = Field(
        description="Por participa_en y Capitulo.orden. Nulo si la obra no declara sus "
                    "personajes_presentes: no declarado, que no es nadie (RF-44)")


class FichaDeLugar(BaseModel):
    """`Lugar` (`RF-43`)."""

    id: str
    nombre: str | None = Field(description="Nulo si la base no lo guarda (PLAN-27 E2)")
    atmosfera: str | None = Field(description="Nula: la base no la guarda")
    capitulos_donde_aparece: list[CapituloEnlazado] = Field(
        description="Por ocurre_en y Capitulo.orden (RF-44)")


class Fichas(BaseModel):
    personajes: list[FichaDePersonaje]
    lugares: list[FichaDeLugar]
