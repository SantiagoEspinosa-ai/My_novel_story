"""Entrada y salida de los endpoints de la entrevista."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.commons.dominio.destinatario import HechoPropuesto
from app.commons.dominio.enumeraciones import TipoDeElementoPersonal


class RespuestaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    respuesta: str = Field(min_length=1)


class TextoLibreEntrada(BaseModel):
    """Sin `max_length`: el limite de `RF-11` lo comprueba `texto_libre`, que
    devuelve el motivo con las dos cifras. Un 422 generico de Pydantic diria que
    esta mal pero no cuanto sobra."""

    model_config = ConfigDict(extra="forbid")
    texto: str = Field(min_length=1)


class OtroNombre(BaseModel):
    """Una persona o una mascota con nombre. El tipo es `tipo_de_elemento_personal`, pero
    solo los dos que llevan nombre de alguien (`SPEC-34` `RF-01`): un rasgo con nombre es
    un error de validacion."""

    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1)
    tipo: TipoDeElementoPersonal
    relacion: str | None = None

    @field_validator("tipo")
    @classmethod
    def _con_nombre(cls, v):
        if v not in (TipoDeElementoPersonal.PERSONA, TipoDeElementoPersonal.MASCOTA):
            raise ValueError("solo una persona o una mascota se declaran con nombre")
        return v


class NombresEntrada(BaseModel):
    """`SPEC-34` `RF-01`, `PLAN-34` E3: los nombres, escritos por el comprador en su campo y
    guardados sin pasar por ningun agente. Es **el estado completo** de lo declarado: una
    persona que ya no viene es una persona que se quita."""

    model_config = ConfigDict(extra="forbid")
    destinatario: str | None = None
    regalado_por: str | None = None
    otros: list[OtroNombre] = Field(default_factory=list)
    vetados: list[str] = Field(default_factory=list)


class AvisoEntrada(BaseModel):
    """Confirmar un aviso de nombre (`SPEC-25` `RF-10`) fuera del modelo."""

    model_config = ConfigDict(extra="forbid")
    vetado: str = Field(min_length=1)


class OtroNombreSalida(BaseModel):
    nombre: str
    tipo: str
    relacion: str | None
    declarado: bool


class AvisoDeNombre(BaseModel):
    vetado: str
    texto: str


class NombresSalida(BaseModel):
    """Lo que la ficha sabe de los nombres, **siempre con el nombre real** (`SPEC-35`
    `RF-06`). `declarado` dice si lo escribio el comprador en su campo o lo saco el
    Entrevistador de una respuesta."""

    destinatario: str | None
    regalado_por: str | None
    otros: list[OtroNombreSalida]
    vetados: list[str]
    avisos: list[AvisoDeNombre]


class ContradiccionSalida(BaseModel):
    tipo: str
    descripcion: str


class TurnoDeEntrevistaSalida(BaseModel):
    """`TurnoDeEntrevista` (`SPEC-33` `RF-10`). `pregunta` es la que el Entrevistador
    hizo **despues** de esta respuesta. `falta`, `avisos` y `contradicciones_abiertas` son lo
    que el codigo dijo en este turno; `None` si la fila es anterior a guardarlos."""

    orden: int
    respuesta: str
    pregunta: str
    tema: str | None
    falta: list[str] | None
    avisos: list[str] | None
    contradicciones_abiertas: list[ContradiccionSalida] | None
    cuando: str | None
    fuera_del_modelo: bool | None = Field(
        default=None, description="Se contesto en el campo de nombres, sin agente (SPEC-34 "
                                  "RF-01). None en los turnos anteriores a la migracion 19")


class HistorialSalida(BaseModel):
    """La conversacion y lo que la pagina necesita para actuar (`SPEC-33` `RF-08`..`RF-10`).
    `puede_cerrar` lo resuelve el backend con la misma regla que `cerrar`."""

    obra: str
    cerrada: bool
    puede_cerrar: bool
    hechos_propuestos: list[HechoPropuesto]
    primera_pregunta: str
    turnos: list[TurnoDeEntrevistaSalida]
    nombres: NombresSalida


def turno_a_dict(t) -> dict:
    return {
        "id": t.id, "obra": t.obra, "pregunta": t.pregunta, "tema": t.tema,
        "falta": t.falta, "requiere_juicio": t.requiere_juicio, "avisos": t.avisos,
        "contradicciones": [{"tipo": c.tipo.value, "descripcion": c.descripcion}
                            for c in t.contradicciones],
        "puede_cerrar": t.puede_cerrar,
        "ficha": t.ficha.model_dump(mode="json"),
    }
