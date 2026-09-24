"""La puerta de publicacion (`SPEC-30` v4): decide si una version se publica.

Funcion pura sobre datos ya resueltos, igual que `capitulo.cerrar`: no lee la base
ni ejecuta Lean. Quien la llama (`orquestacion/publicacion.py`) reune los datos.

LAS CUATRO CONDICIONES DE `RF-01`
----------------------------------
1. Ningun capitulo rendido (`INV-29`). **Decision nuestra, mas estricta que el
   enunciado**, que no habla de rendicion: un capitulo que se rindio no es un
   capitulo que paso.
2. Ninguna `bloqueante` abierta, de capitulo o de obra.
3. Lean devuelve `0` (`INV-28`). El `2` —sin veredicto— bloquea igual que el `1`, y
   un Lean que no se pudo ejecutar tambien: ninguno de los dos es «se miro y esta
   bien».
4. Ningun hallazgo de obra del Editor abierto (`INV-27`).

Se devuelven **todas** las que fallan, no la primera: `RF-04` informa de todo.

QUE ES REINTENTABLE
-------------------
Solo `INV-27`: el Editor lo convierte en instrucciones y el capitulo se reescribe
(`RF-07`, `RF-10`). Un fallo de Lean **no**: lo que Lean mira lo fija el plan antes de
escribir, asi que reescribir la prosa no lo arregla; vuelve al Editor como feedback y
la generacion se detiene (`RF-06`, `C-2`). Lo demas tampoco se arregla reescribiendo.

LO QUE NO SE EJECUTA
--------------------
`INV-06` queda sin comprobar y no bloquea (`RF-12`, `C-4`), y se dice en cada
veredicto: un validador que no corre no es un validador que paso.
"""

from dataclasses import dataclass, field

from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad as S

ABIERTOS = {EH.ABIERTO, EH.SIN_VEREDICTO}

NO_EJECUTADAS = (
    ("INV-06", "exige una comparacion semantica entre hechos canonicos, y hoy no hay "
               "quien la haga: decision nuestra, `SPEC-30` `RF-12`"),
)


@dataclass(frozen=True)
class ResultadoLean:
    """`codigo`: 0 limpio, 1 violaciones, 2 sin veredicto, `None` no se pudo ejecutar."""

    codigo: int | None
    violaciones: list = field(default_factory=list)
    detalle: str = ""


@dataclass(frozen=True)
class Condicion:
    rf: str
    invariante: str
    capitulo: str | None
    detalle: str
    reintentable: bool


@dataclass(frozen=True)
class NoEjecutada:
    invariante: str
    motivo: str


@dataclass(frozen=True)
class Decision:
    publica: bool
    condiciones: list
    no_ejecutadas: list


def _lean(lean):
    if lean.codigo == 0:
        return []
    if lean.codigo is None:
        detalle = "Lean no se pudo ejecutar" + (": " + lean.detalle if lean.detalle else "")
    elif lean.codigo == 2:
        detalle = "sin veredicto: no habia dato bastante para mirar"
    elif lean.codigo == 1:
        detalle = "{0} violacion(es): {1}".format(len(lean.violaciones), "; ".join(
            "{0} {1}".format(v.get("invariante"), ",".join(v.get("eventos", [])))
            for v in lean.violaciones) or "sin detalle")
    else:
        detalle = "codigo desconocido {0}: sin veredicto".format(lean.codigo)
    return [Condicion("RF-01.3", "INV-28", None, detalle, False)]


def decidir(rendidos, hallazgos, lean, no_ejecutadas=NO_EJECUTADAS) -> Decision:
    condiciones = [Condicion("RF-01.1", "INV-29", c, "el capitulo se rindio", False)
                   for c in rendidos]
    abiertos = [h for h in hallazgos if h["estado"] in ABIERTOS]
    condiciones += [Condicion("RF-01.2", h["invariante"], h.get("capitulo"),
                              h.get("descripcion", ""), False)
                    for h in abiertos if h["severidad"] is S.BLOQUEANTE]
    condiciones += _lean(lean)
    condiciones += [Condicion("RF-01.4", "INV-27", h.get("capitulo"),
                              h.get("descripcion", ""), True)
                    for h in abiertos if h["invariante"] == "INV-27"]
    return Decision(publica=not condiciones, condiciones=condiciones,
                    no_ejecutadas=[NoEjecutada(i, m) for i, m in no_ejecutadas])
