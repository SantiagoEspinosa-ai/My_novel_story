"""Lo que sube a Langfuse, escrito como tipos (`SPEC-29` § "El limite", `PLAN-29` E2).

Los campos de estos cuatro modelos son **la columna izquierda de la tabla de la spec y
nada mas**: nombres de rol, de tool y de validador; tokens, coste, latencia y modelos;
identificadores opacos; el resultado de un validador; y la plantilla de un prompt sin
rellenar. `extra="forbid"` hace que un campo nuevo —la respuesta, el prompt tal como se
envio, un fragmento— no se pueda ni construir: el limite lo hacen cumplir los tipos, no la
disciplina de quien llama.

TRES REGLAS QUE VIVEN AQUI
--------------------------
- **Lo ausente se queda ausente** (`RF-03`): `a_enviar()` quita los `None`, nunca los
  convierte en cero. Un cero se lee como un dato y un hueco no.
- **Un score lleva valor o categoria, no los dos**, y «sin veredicto» es una categoria
  propia (`RF-04`): el `2` de Lean no es un aprobado.
- **El termino de una vetada solo viaja si es global** (`RF-06`): una vetada de novela la
  define el cliente y puede ser el nombre de una persona.
"""

import enum
import hashlib

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.commons.dominio.enumeraciones import NivelDeVeto


def sesion_de(obra: str) -> str:
    """`PLAN-29`: la sesion es una huella del id de la obra, no el id. Determinista, para
    que la entrevista y la generacion caigan en la misma sin guardar nada; opaca, porque
    alguien puede pasar un `--obra` con un nombre."""
    return "ses-" + hashlib.sha256(obra.encode("utf-8")).hexdigest()[:16]


class Categoria(str, enum.Enum):
    PASA = "pasa"
    FALLA = "falla"
    SIN_VEREDICTO = "sin_veredicto"
    NO_APLICA = "no_aplica"


class _Enviado(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    def a_enviar(self) -> dict:
        return self.model_dump(mode="json", exclude_none=True)


class TrazaEnviada(_Enviado):
    id: str
    nombre: str = Field(description="generacion | turno_de_entrevista")
    sesion: str


class SpanEnviado(_Enviado):
    id: str
    traza: str
    padre: str | None = None
    nombre: str = Field(description="rol, tool o grupo: planificacion, capitulo, cierre")
    tipo: str = Field(pattern="^(rol|tool|grupo)$")
    capitulo: int | None = Field(default=None, description="El numero, nunca el id del plan")
    tokens_entrada: int | None = None
    tokens_salida: int | None = None
    tokens_cache_creados: int | None = None
    tokens_cache_leidos: int | None = None
    tokens_estimados: int | None = Field(default=None, description="Lo que devolvio una tool")
    coste_usd: float | None = None
    coste_es_suelo: bool | None = Field(
        default=None, description="Un agregado con alguna llamada sin coste es un suelo")
    latencia_ms: int | None = None
    modelos: list[str] | None = None
    version_de_prompt: str | None = None
    resultado: str | None = None
    clase_de_fallo: str | None = None
    validacion: str | None = Field(default=None, description="De una llamada a una tool")


class ScoreEnviado(_Enviado):
    traza: str
    span: str | None = None
    nombre: str = Field(description="INV-xx, schema, INV-26.<criterio>…")
    valor: float | None = None
    categoria: Categoria | None = None
    capitulo: int | None = None
    nivel: NivelDeVeto | None = None
    referencia: str | None = Field(default=None, description="vetada-<nivel>-<rowid>")
    termino: str | None = None
    motivo: str | None = Field(default=None, description="Texto fijo del codigo, nunca de la obra")

    @model_validator(mode="after")
    def _valor_o_categoria(self):
        if (self.valor is None) == (self.categoria is None):
            raise ValueError("un score lleva valor o categoria, uno de los dos")
        if self.termino is not None and self.nivel is not NivelDeVeto.GLOBAL:
            raise ValueError("el termino de una vetada solo viaja si es global (RF-06)")
        return self


class VersionDePrompt(_Enviado):
    rol: str
    version: str
    plantilla: str
