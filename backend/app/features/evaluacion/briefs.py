"""Los briefs de evaluacion de `harness/evals/` (`SPEC-31` `RF-01`, `PLAN-31` E1).

UN BRIEF, DOS FORMAS DE ENTRAR
------------------------------
Un brief entra al sistema por **una** de dos puertas, nunca por las dos:

- `ficha`: la `FichaDeEntrevista` ya cerrada, la que lee `novela_regalo.py`.
- `guion`: lo que diria el comprador en la entrevista, turno a turno. Es la unica forma
  de probar lo que pasa **dentro** de la entrevista: la inyeccion en el texto libre y las
  contradicciones (`PLAN-31` hallazgo 6).

Las dos a la vez harian que el resultado dependiera de cual se leyo; ninguna, que el
brief no se pudiera ejecutar.

`_meta.datos` es obligatorio y solo puede valer `inventados` (`SPEC-25` `RF-22`,
`SPEC-31` `RF-01`). **Es una declaracion, no una comprobacion**: ninguna prueba puede
saber si un nombre es de una persona real. Lo que si impide es un brief que no lo
declare.
"""

import json
import pathlib
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.dominio.enumeraciones import TipoDeContradiccion


RAIZ_DEL_REPOSITORIO = pathlib.Path(__file__).resolve().parents[4]


class BriefInvalido(ValueError):
    pass


class _Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MetaDelBrief(_Estricto):
    id: str = Field(min_length=1)
    proposito: str = Field(min_length=1)
    de_los_cinco_briefs: str = Field(min_length=1)
    datos: Literal["inventados"]
    estado: str = Field(min_length=1)
    requiere: list[str] = Field(default_factory=list)


ACCIONES = ("respuesta", "texto_libre", "cerrar")


class TurnoDelGuion(_Estricto):
    """Una intervencion del comprador. Exactamente una de las tres acciones.

    Confirmar o descartar un hecho propuesto no esta: su identificador lo pone la API
    al proponerlo, y ningun brief lo necesita hoy. El de injection mide justo que no se
    confirme nada.

    `ficha_esperada` es lo que un Entrevistador correcto dejaria en la ficha tras este
    turno, y `hechos_esperados` lo que un extractor propondria de un texto libre. Son el
    resultado esperado del brief, no una entrada: en una ejecucion real contesta el
    modelo, y con dobles se reproducen.
    """

    respuesta: str | None = None
    texto_libre: str | None = None
    cerrar: bool | None = None
    ficha_esperada: FichaDeEntrevista | None = None
    hechos_esperados: list[str] = Field(default_factory=list)
    nota: str | None = None

    @model_validator(mode="after")
    def _una_accion(self):
        acciones = [a for a in ACCIONES if getattr(self, a) not in (None, False)]
        if len(acciones) != 1:
            raise ValueError("cada turno del guion lleva una sola accion, y este lleva "
                             "{0}".format(acciones or "ninguna"))
        return self

    @property
    def accion(self) -> str:
        return next(a for a in ACCIONES if getattr(self, a) not in (None, False))


class GuionDeEntrevista(_Estricto):
    turnos: list[TurnoDelGuion] = Field(min_length=1)


class InstruccionInyectada(_Estricto):
    texto: str = Field(min_length=1)
    el_detector_la_ve: bool


class BriefDeEvaluacion(_Estricto):
    meta: MetaDelBrief = Field(alias="_meta")
    ficha: FichaDeEntrevista | None = None
    ficha_en: str | None = Field(
        default=None, description="Ruta, desde la raiz del repositorio, de una ficha que "
                                  "ya existe: se referencia en vez de copiarla")
    guion: GuionDeEntrevista | None = None
    que_deberia_pasar: dict[str, Any] = Field(min_length=1)
    # Lo que cada brief adversario declara que intenta, para que se pueda comprobar
    # que el brief lo intenta de verdad (`PLAN-31` E2).
    por_que_provoca_cada_incoherencia: dict[str, str] | None = None
    instrucciones_inyectadas: list[InstruccionInyectada] | None = None
    contradicciones_que_provoca: list[TipoDeContradiccion] | None = None
    variantes_que_intenta: dict[str, list[str]] | None = None
    claves_de_rastro: list[str] | None = Field(
        default=None, description="Lo que no puede aparecer en otra novela de la misma "
                                  "base (`RF-12`). Sin ellas, los nombres de la ficha")

    @model_validator(mode="after")
    def _ficha_o_guion(self):
        if (self.ficha is None) == (self.guion is None):
            raise ValueError("un brief lleva una ficha o un guion de entrevista, uno de "
                             "los dos: {0}".format("los dos" if self.ficha else "ninguno"))
        # `SPEC-32` (`PLAN-31` E12): la extension se pregunta. En el modelo de la ficha es
        # opcional por las fichas antiguas; un brief de evaluacion la fija siempre, y en
        # un guion la fija la ficha con la que la entrevista deberia cerrar.
        fichas = [self.ficha] if self.ficha else [
            t.ficha_esperada for t in self.guion.turnos if t.ficha_esperada]
        if not fichas or fichas[-1].extension is None:
            raise ValueError("el brief no fija la extension de capitulo (SPEC-32): corta, "
                             "media o larga")
        return self


def validar(datos: dict, raiz=None) -> BriefDeEvaluacion:
    """`ficha_en` se resuelve aqui: el brief base es la ficha de ejemplo del repositorio
    (`SPEC-31` `RF-10`), y dos copias de la misma ficha acaban divergiendo."""
    if datos.get("ficha_en"):
        if datos.get("ficha") is not None:
            raise BriefInvalido("un brief lleva `ficha` o `ficha_en`, no las dos")
        ruta = pathlib.Path(raiz or RAIZ_DEL_REPOSITORIO) / datos["ficha_en"]
        try:
            with open(ruta, encoding="utf-8") as f:
                datos = dict(datos, ficha=json.load(f))
        except OSError as e:
            raise BriefInvalido("`ficha_en` apunta a {0}, que no se puede leer: {1}".format(
                datos["ficha_en"], e)) from None
    try:
        return BriefDeEvaluacion.model_validate(datos)
    except ValidationError as e:
        raise BriefInvalido(str(e)) from None


def cargar(ruta) -> BriefDeEvaluacion:
    with open(ruta, encoding="utf-8") as f:
        return validar(json.load(f))
