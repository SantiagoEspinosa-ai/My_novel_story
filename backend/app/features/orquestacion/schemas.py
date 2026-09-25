"""Los esquemas de salida de las versiones y de la peticion de cambio (`PLAN-23`).

Replican `VersionDeObra` de `docs/definitions.md`, con las enumeraciones como
enumeraciones (`RF-34`). `compartido` es lo que `RF-52` pide decir -si el capitulo
cambio respecto a la anterior- y lo calcula el backend por identidad (`CE-5`).

`RF-57`: ningun campo expone modelos, topes ni la ruta de la base.
"""

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio
from app.commons.trabajos.estados import EstadoDeTrabajo
from app.features.lectura import schemas as lectura
from pydantic import Field


class VersionSalida(_DelDominio):
    numero: int
    anterior: int | None
    peticion: int | None
    commit: str
    creada_en: str


class VersionesSalida(_DelDominio):
    obra: str
    versiones: list[VersionSalida]
    vigente: int = Field(description="El numero de la version vigente: la ultima publicada, "
                                     "o la 1 si no hay ninguna (`F-121`, `F-150`)")


class EscenaDeVersionSalida(_DelDominio):
    id: str
    estado: enums.EstadoDeEscena
    estado_de_verificacion: enums.EstadoDeVerificacion


class CapituloDeVersionSalida(_DelDominio):
    orden: int
    capitulo: str
    compartido: bool | None
    estado: enums.EstadoDeCapitulo | None
    escenas: list[EscenaDeVersionSalida]


class VersionDetalleSalida(VersionSalida):
    obra: str
    capitulos: list[CapituloDeVersionSalida]


# --- La peticion de cambio (`PLAN-23` A7, `C-4`) -------------------------------------

class PeticionEntrada(_DelDominio):
    """Los campos de `PeticionDeCambio` que da el lector. Con `hecho`, `hecho` y
    `enunciado_nuevo`; con `nombre`, `personaje` y `nombre_nuevo`. La obra va en la ruta
    y la version de partida, si no se dice, es la vigente."""

    clase: enums.ClaseDePeticion
    texto: str
    hecho: str | None = None
    enunciado_nuevo: str | None = None
    personaje: str | None = None
    nombre_nuevo: str | None = None
    version_de_partida: int | None = None


class CambioEntrada(PeticionEntrada):
    """La misma peticion y la lista que el lector acepta, que tiene que ser la
    propuesta (`RF-48`, `RF-50`)."""

    capitulos_propuestos: list[str]


class CapitulosPorSalida(_DelDominio):
    cascada: list[str]
    selectiva: list[str]


class PropuestaSalida(_DelDominio):
    obra: str
    version_de_partida: int
    clase: enums.ClaseDePeticion
    capitulos: CapitulosPorSalida
    salida: enums.SalidaDeRegeneracion | None
    capitulos_propuestos: list[str] | None
    motivo: str | None
    promesa: str
    punto_ciego: str


# --- Seguir un trabajo (`RF-48`, `PLAN-22` E14) ---------------------------------------

class TrabajoSalida(_DelDominio):
    """Lo que `GET /trabajos/{id}` devuelve. `estado_de_trabajo` no es dominio: su
    vocabulario lo declara `docs/architecture.md` § "Los estados de un trabajo".
    `abandonado` no es `fallido` (no se sabe si llego a pasar): viajan distintos."""

    id: str
    tipo: str
    estado: EstadoDeTrabajo
    resultado: dict | None
    motivo: str | None
    volvio_tras_abandono: bool


# --- Leer una version (`PLAN-22` E15, `RF-52`..`RF-54`) --------------------------------
# La forma de la lectura (`lectura/`) con lo que solo sabe una version: si el capitulo es
# el mismo que el de esa posicion en la anterior (`compartido`, por identidad: `CE-5`) y
# el `estado_de_verificacion` de cada escena **en esa version** (`D-1`). Se componen
# aqui porque aqui se puede componer (`A-02`); no se calcula nada nuevo.

class EscenaDelIndiceDeVersion(lectura.EscenaDelIndice):
    estado_de_verificacion: enums.EstadoDeVerificacion = Field(
        description="sin_reverificar es un verde heredado de otra version: no es verde")


class CapituloDelIndiceDeVersion(lectura.CapituloDelIndice):
    compartido: bool | None = Field(
        description="True si es el mismo capitulo que el de su posicion en la anterior; "
                    "False si cambio; nulo si la version no tiene anterior")
    escenas: list[EscenaDelIndiceDeVersion]


class IndiceDeVersion(lectura.Indice):
    numero: int = Field(description="VersionDeObra.numero")
    anterior: int | None
    capitulos: list[CapituloDelIndiceDeVersion] = Field(description="En el orden de la version")


class EscenaLeidaDeVersion(lectura.EscenaLeida):
    estado_de_verificacion: enums.EstadoDeVerificacion


class CapituloLeidoDeVersion(lectura.CapituloLeido):
    numero: int = Field(description="VersionDeObra.numero")
    compartido: bool | None
    escenas: list[EscenaLeidaDeVersion]
