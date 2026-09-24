"""Entrada y salida de los endpoints de la entrevista."""

from pydantic import BaseModel, ConfigDict, Field


class RespuestaEntrada(BaseModel):
    model_config = ConfigDict(extra="forbid")
    respuesta: str = Field(min_length=1)


class TextoLibreEntrada(BaseModel):
    """Sin `max_length`: el limite de `RF-11` lo comprueba `texto_libre`, que
    devuelve el motivo con las dos cifras. Un 422 generico de Pydantic diria que
    esta mal pero no cuanto sobra."""

    model_config = ConfigDict(extra="forbid")
    texto: str = Field(min_length=1)


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


class HistorialSalida(BaseModel):
    primera_pregunta: str
    turnos: list[TurnoDeEntrevistaSalida]


def turno_a_dict(t) -> dict:
    return {
        "id": t.id, "obra": t.obra, "pregunta": t.pregunta, "tema": t.tema,
        "falta": t.falta, "requiere_juicio": t.requiere_juicio, "avisos": t.avisos,
        "contradicciones": [{"tipo": c.tipo.value, "descripcion": c.descripcion}
                            for c in t.contradicciones],
        "puede_cerrar": t.puede_cerrar,
        "ficha": t.ficha.model_dump(mode="json"),
    }
