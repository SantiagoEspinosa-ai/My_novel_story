"""La tabla por brief: `harness/evals/resultados.md` (`SPEC-31` `RF-02`, `PLAN-31` E6).

Una fila por brief y pasada, una columna por validador. **Las columnas salen del registro
de invariantes** (`commons/invariantes/registro.py`), no de una lista a mano: una
invariante que se anada manana aparece sola, y hasta que alguien diga donde queda
constancia de que se ejecuto, su celda dice «sin veredicto». Se anaden los validadores que
no son una invariante: `INV-26` por criterio, el schema del plan, las dos comprobaciones
de la entrevista y la puerta de publicacion. `INV-28` es la columna de Lean.

LOS SEIS RESULTADOS, Y POR QUE NO SON CUATRO
--------------------------------------------
Los cuatro de `RF-02` —pasó, falló, no aplica, sin veredicto— y dos que la spec separa:

- **sin ejecutar**: el brief no llego a ejecutarse. No se rellena.
- **no ejecutado**: el sistema no ejecuta nunca ese validador (`INV-06`, `SPEC-30`
  `RF-12`), en todas las filas: un validador que no corre no es uno que paso.

Un validador que disparo y se resolvio dice «pasó (2 disparos)»: el disparo es lo que
convierte ese pase en un pase que dice algo (`harness/evals/README.md`, «Como se lee un
cero»).

Aqui no se calcula ninguna celda de una obra: eso lo reune `orquestacion/evaluacion.py`,
que es quien puede componer features (`A-02`). Esto solo sabe de columnas y de texto.
"""

import enum
from dataclasses import dataclass

from app.commons.dominio.enumeraciones import CriterioDeEdicion
from app.commons.invariantes import registro

ORDEN_DE_LOS_BRIEFS = ("brief-base", "brief-injection", "brief-incoherencia-temporal",
                       "brief-contradicciones", "brief-vetadas-por-variantes")
"""El orden de prioridad de `PLAN-31` § «Que pasa al acercarse al techo»."""

PASADAS = ("antes", "despues")

NO_EJECUTADAS = {"INV-06": "exige una comparacion semantica entre hechos canonicos, y hoy "
                           "no hay quien la haga: SPEC-30 RF-12"}
"""Lo que el sistema no ejecuta nunca. Es la lista de la puerta de publicacion
(`auditoria/publicacion.NO_EJECUTADAS`); una prueba compara las dos."""

OTRAS_COLUMNAS = ("schema.plan", "entrevista.instrucciones", "entrevista.contradicciones",
                  "publicacion")


class Resultado(str, enum.Enum):
    """Los valores de `SPEC-31` `RF-02`, literales."""

    PASO = "pasó"
    FALLO = "falló"
    NO_APLICA = "no aplica"
    SIN_VEREDICTO = "sin veredicto"
    SIN_EJECUTAR = "sin ejecutar"
    NO_EJECUTADO = "no ejecutado"


@dataclass(frozen=True)
class Celda:
    resultado: Resultado
    disparos: int = 0
    motivo: str | None = None

    @property
    def texto(self) -> str:
        if self.disparos and self.resultado in (Resultado.PASO, Resultado.FALLO):
            return "{0} ({1} disparo{2})".format(self.resultado.value, self.disparos,
                                                 "" if self.disparos == 1 else "s")
        return self.resultado.value


def _numero(id_inv):
    return int(id_inv.split("-")[1])


def columnas() -> list:
    """Se calcula cada vez: el registro manda, no una copia hecha al importar."""
    invariantes = sorted(registro.TODAS, key=_numero)
    criterios = ["INV-26.{0}".format(c.value) for c in CriterioDeEdicion]
    return invariantes + criterios + list(OTRAS_COLUMNAS)


def celda_fija(columna):
    """Lo que vale una columna sin mirar ninguna obra, o `None`: obsoleta o nunca
    ejecutada. Vale igual para una fila ejecutada que para una sin ejecutar."""
    inv = registro.TODAS.get(columna)
    if inv is not None and inv.obsoleta:
        return Celda(Resultado.NO_APLICA, motivo="obsoleta (SPEC-26 v3)")
    if columna in NO_EJECUTADAS:
        return Celda(Resultado.NO_EJECUTADO, motivo=NO_EJECUTADAS[columna])
    return None


def fila_sin_ejecutar() -> dict:
    return {c: celda_fija(c) or Celda(Resultado.SIN_EJECUTAR) for c in columnas()}


@dataclass
class Fila:
    brief: str
    pasada: str
    celdas: dict | None
    """`None` si el brief no se ejecuto en esta pasada."""
    ejecucion: str | None = None
    coste: str | None = None
    version_del_escritor: str | None = None
    """`RF-03`: la huella del prompt del Escritor con que se hizo (`SPEC-29` `RF-05`)."""


def _celda(fila, columna):
    if fila.celdas is None:
        return fila_sin_ejecutar()[columna]
    return fila.celdas.get(columna) or celda_fija(columna) or Celda(
        Resultado.SIN_VEREDICTO, motivo="sin constancia de ejecucion")


def generar(filas) -> str:
    """El Markdown entero. Cada brief y pasada tiene su fila, se haya ejecutado o no."""
    por_clave = {(f.brief, f.pasada): f for f in filas}
    briefs = list(ORDEN_DE_LOS_BRIEFS) + sorted(
        {f.brief for f in filas} - set(ORDEN_DE_LOS_BRIEFS))
    cols = columnas()
    lineas = [
        "# Resultados de la evaluacion",
        "",
        "Generado por `backend/evaluar.py` desde `gasto_de_evaluacion` y la base de cada "
        "ejecucion: **no se edita a mano**. Una fila por brief y pasada, una columna por "
        "validador (`SPEC-31` `RF-02`). Las columnas salen del registro de invariantes.",
        "",
        "Como se lee: **pasó** solo con constancia de que el validador se ejecuto; "
        "**sin veredicto** es que no la hay, o que el validador no llego a juzgar; "
        "**sin ejecutar** es que el brief no se ejecuto; **no ejecutado** es que el "
        "sistema no ejecuta nunca ese validador (`INV-06`, `SPEC-30` `RF-12`); "
        "**no aplica** es una invariante obsoleta, o una comprobacion de la entrevista en "
        "un brief que entra por ficha. `INV-28` es Lean.",
        "",
    ]
    if not any(f.celdas is not None for f in filas):
        lineas += ["**Ningun brief se ha ejecutado todavia.** Todas las filas dicen "
                   "«sin ejecutar»: no hay nada medido.", ""]
    for pasada in PASADAS:
        lineas += ["## Pasada «{0}»".format(pasada), "",
                   "| brief | " + " | ".join(cols) + " |",
                   "| --- | " + " | ".join("---" for _ in cols) + " |"]
        for brief in briefs:
            fila = por_clave.get((brief, pasada)) or Fila(brief, pasada, None)
            lineas.append("| {0} | ".format(brief)
                          + " | ".join(_celda(fila, c).texto for c in cols) + " |")
        lineas += ["", "| ejecucion | brief | coste | version del prompt del escritor |",
                   "| --- | --- | --- | --- |"]
        for brief in briefs:
            fila = por_clave.get((brief, pasada)) or Fila(brief, pasada, None)
            lineas.append("| {0} | {1} | {2} | {3} |".format(
                fila.ejecucion or "sin ejecutar", brief, fila.coste or "sin medir",
                fila.version_del_escritor or "sin medir"))
        lineas.append("")
    return "\n".join(lineas)
