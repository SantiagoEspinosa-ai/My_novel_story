"""El plano Destinatario de `Docs/definitions.md`, como modelos Pydantic.

POR QUE VIVE EN `commons/` Y NO EN `features/entrevista/`
----------------------------------------------------------
`PLAN-25` E5 lo situaba en la feature, y no puede estar alli: `BriefDeObra`
(en `commons/configuracion/`) tiene que poder llevar la ficha terminada, y
`commons` no importa de ninguna feature (`A-01`). La ficha la rellena la
entrevista, pero la leen el brief, el Planificador y el Escritor: es dominio
compartido.

UNA FICHA A MEDIAS ES UNA FICHA VALIDA
--------------------------------------
Todos los campos son opcionales porque la ficha se rellena turno a turno. Lo que
falta lo dice `features/entrevista/ficha.py:que_falta`, y lo que no puede pasar
a brief lo impide `a_brief`. Lo que **si** se valida siempre es la forma: un
valor fuera de la lista, un campo desconocido o un `otro` sin sus palabras.
"""

from pydantic import Field, model_validator

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio

# `SPEC-25` `RF-03`: la extension no se pregunta ni se guarda en la ficha. Es
# la misma para todas las novelas y el entrevistador solo informa de ella.
EXTENSION = {"capitulos": 10, "palabras_por_capitulo": [1000, 1500]}

# Los cuatro campos que el comprador elige de una lista con `otro`.
CAMPOS_CON_OTRO = ("ocasion", "genero", "tono", "papel")


class MomentoDelRecuerdo(_DelDominio):
    """Cuando paso un recuerdo: el año, la edad del destinatario, o los dos."""

    anio: int | None = Field(default=None, ge=1900, le=2100)
    edad: int | None = Field(default=None, ge=0, le=120)


class ElementoPersonal(_DelDominio):
    tipo: enums.TipoDeElementoPersonal
    descripcion: str = Field(min_length=1)
    nombre: str | None = None
    relacion: str | None = None
    momento: MomentoDelRecuerdo | None = None
    imprescindible: bool = False


class Destinatario(_DelDominio):
    nombre: str | None = None
    edad: int | None = Field(default=None, ge=0, le=120)
    elementos: list[ElementoPersonal] = Field(default_factory=list)


class HechoPropuesto(_DelDominio):
    id: str = Field(min_length=1)
    texto: str = Field(min_length=1)
    estado: enums.EstadoDeHechoPropuesto = enums.EstadoDeHechoPropuesto.PROPUESTO


class ContradiccionResuelta(_DelDominio):
    """Como se resolvio una contradiccion (`RF-09`).

    `tipo = juicio_del_modelo` marca que no la comprobo el codigo sino el
    Entrevistador (`RF-08b`): queda escrito para que no pase por lo que no es.
    """

    tipo: enums.TipoDeContradiccion
    descripcion: str = Field(min_length=1)
    resolucion: str = Field(min_length=1)


class FichaDeEntrevista(_DelDominio):
    destinatario: Destinatario = Field(default_factory=Destinatario)
    ocasion: enums.Ocasion | None = None
    genero: enums.GeneroDeLaHistoria | None = None
    tono: enums.TonoDeLaHistoria | None = None
    papel: enums.PapelDelDestinatario | None = None
    literales_de_otro: dict[str, str] = Field(default_factory=dict)
    regalado_por: str | None = None
    vetadas: list[str] = Field(default_factory=list)
    nombres_vetados: list[str] = Field(default_factory=list)
    dedicatoria: str | None = None
    hechos_propuestos: list[HechoPropuesto] = Field(default_factory=list)
    contradicciones_resueltas: list[ContradiccionResuelta] = Field(
        default_factory=list)

    @model_validator(mode="after")
    def _otro_lleva_sus_palabras(self):
        """`O-1`: elegir `otro` sin guardar lo que dijo el comprador dejaria al
        Escritor sin saber que escribir, y la ficha no lo delataria."""
        for campo in CAMPOS_CON_OTRO:
            if getattr(self, campo) is not None and getattr(self, campo).value == "otro":
                if not (self.literales_de_otro.get(campo) or "").strip():
                    raise ValueError(
                        "`{0}` es `otro` y falta `literales_de_otro.{0}`: las "
                        "palabras del comprador son lo unico que dice que "
                        "quiere".format(campo))
        return self
