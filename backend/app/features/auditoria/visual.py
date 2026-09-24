"""El validador visual de la lectura web: `INV-30` (`SPEC-22` `RF-58`, `PLAN-22` E13b).

Un agente con Playwright MCP (`inspector_visual`) recorre la web servida de una version y
devuelve un veredicto por pieza. Aqui se **juzga ese veredicto**, no la web: se valida con
esquema y se decide el hallazgo. Quien lo guarda y quien sube los scores es el guion que
lo lanza (`backend/inspeccion_visual.py`), porque una feature no escribe en las tablas de
otra.

UN ILEGIBLE NO PASA
--------------------
Una respuesta que no valida -falta una pieza, una repetida, un veredicto que no es `pasa`
ni `falla`, un motivo vacio, un campo de mas- es `sin_veredicto`, y deja su hallazgo
`sin_veredicto`: **no consta que la web se vea bien**, y darlo por bueno seria la Regla 8.

PUNTO EN EL HARNESS Y LO QUE NO HACE
-------------------------------------
Corre en la puerta de publicacion, **despues** de publicar, como `INV-27`. Es `mayor`: deja
hallazgo y no despublica. **No devuelve el fallo al Escritor ni a nadie**: el hallazgo
queda abierto y lo resuelve una persona (fuera de `RF-58`, documentado como no hecho).
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.commons.invariantes.registro import TODAS

PIEZAS = ("portada", "indice", "capitulos", "fichas", "enlaces")
INVARIANTE = "INV-30"


class Comprobacion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pieza: Literal["portada", "indice", "capitulos", "fichas", "enlaces"]
    veredicto: Literal["pasa", "falla"]
    motivo: str = Field(min_length=1)


class Veredicto(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comprobaciones: list[Comprobacion]

    @model_validator(mode="after")
    def _cada_pieza_una_vez(self):
        vistas = [c.pieza for c in self.comprobaciones]
        if sorted(vistas) != sorted(PIEZAS):
            raise ValueError("hace falta exactamente una comprobacion por pieza: {0}".format(
                ", ".join(PIEZAS)))
        return self


@dataclass
class Juicio:
    estado: str  # pasa | falla | sin_veredicto
    comprobaciones: list = field(default_factory=list)
    hallazgo: dict | None = None


def _hallazgo(estado, descripcion):
    return {"invariante": INVARIANTE, "verificador": "inspector_visual",
            "severidad": TODAS[INVARIANTE].severidad.value, "estado": estado,
            "descripcion": descripcion}


def juzgar(bruto) -> Juicio:
    """El veredicto del inspector, validado. Nunca lanza: un ilegible es `sin_veredicto`."""
    try:
        v = Veredicto.model_validate(bruto)
    except (ValidationError, TypeError, ValueError):
        return Juicio("sin_veredicto", [], _hallazgo(
            "sin_veredicto", "el inspector visual no devolvio un veredicto legible"))
    ordenadas = sorted(v.comprobaciones, key=lambda c: PIEZAS.index(c.pieza))
    fallos = [c for c in ordenadas if c.veredicto == "falla"]
    if not fallos:
        return Juicio("pasa", ordenadas, None)
    return Juicio("falla", ordenadas, _hallazgo("abierto", "; ".join(
        "{0}: {1}".format(c.pieza, c.motivo) for c in fallos)))


PROMPT = (
    "Inspecciona en el navegador la lectura web que empieza en {url} (datos de la "
    "obra que se acaba de publicar).\n\n"
    "Recorre la portada, el indice, CADA capitulo enlazado desde el indice y las "
    "fichas, y sigue CADA enlace de una ficha a un capitulo. Haz una captura de cada "
    "pagina y mirala, y pide los mensajes de consola: un error de consola es un "
    "fallo.\n\n"
    "Juzga cinco piezas: {piezas}. Responde UNICAMENTE con este JSON, una "
    "comprobacion por pieza, sin texto alrededor:\n"
    '{{"comprobaciones": [{{"pieza": "portada", "veredicto": "pasa|falla", '
    '"motivo": "que viste, en una frase"}}, ...]}}'
)
"""La plantilla sin rellenar: es la que versiona `orquestacion/prompts.py` (`SPEC-29`)."""


def prompt(url):
    """Lo que se le pide al inspector. La URL es la de la portada de la version."""
    return PROMPT.format(url=url, piezas=", ".join(PIEZAS))
