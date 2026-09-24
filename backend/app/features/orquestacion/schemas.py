"""Los esquemas de salida de las versiones y de la peticion de cambio (`PLAN-23`).

Replican `VersionDeObra` de `docs/definitions.md`, con las enumeraciones como
enumeraciones (`RF-34`). `compartido` es lo que `RF-52` pide decir -si el capitulo
cambio respecto a la anterior- y lo calcula el backend por identidad (`CE-5`).

`RF-57`: ningun campo expone modelos, topes ni la ruta de la base.
"""

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio


class VersionSalida(_DelDominio):
    numero: int
    anterior: int | None
    peticion: int | None
    commit: str
    creada_en: str


class VersionesSalida(_DelDominio):
    obra: str
    versiones: list[VersionSalida]


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
