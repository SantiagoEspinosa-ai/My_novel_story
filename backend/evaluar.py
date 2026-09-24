"""La ejecucion de un brief de evaluacion (`SPEC-31`, `PLAN-31`).

Se construye por pasos: E3 trae la entrevista desde un guion, E10 el resto del guion de
ejecucion real.
"""

import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import entrevista_cli  # noqa: E402


@dataclass
class Entrevista:
    """Lo que dejo una entrevista hecha desde un guion. `ficha` es `None` si no cerro."""

    obra: str | None
    ficha: dict | None
    dicho: list = field(default_factory=list)


class _Espia:
    """El cliente HTTP, con la respuesta de `POST /entrevistas` guardada: es la que trae
    la obra, y `dialogar` solo la enseña si la entrevista cierra."""

    def __init__(self, cliente):
        self.cliente, self.creada = cliente, None

    def post(self, url, **kw):
        r = self.cliente.post(url, **kw)
        if url == "/entrevistas" and self.creada is None:
            self.creada = r.json()
        return r

    def get(self, url, **kw):
        return self.cliente.get(url, **kw)


def entradas_del_guion(guion) -> list:
    """El guion, en lo que teclearia el comprador en `entrevista_cli`."""
    salida = []
    for t in guion.turnos:
        if t.accion == "respuesta":
            salida.append(t.respuesta)
        elif t.accion == "texto_libre":
            salida.append(":texto")
            salida.extend(t.texto_libre.splitlines() or [""])
            salida.append(".")
        else:
            salida.append(":cerrar")
    return salida


def entrevistar(cliente, guion, espera=0) -> Entrevista:
    """`PLAN-31` E3: la entrevista del guion contra la API. **El guion no escucha las
    preguntas**: contesta en su orden. Si se acaba sin cerrar, sale con `:salir` y la
    entrevista queda abierta, dicho en `dicho`; no se inventa un cierre."""
    pendientes = iter(entradas_del_guion(guion))
    espia, dicho = _Espia(cliente), []
    ficha = entrevista_cli.dialogar(espia, entrada=lambda _: next(pendientes, ":salir"),
                                    salida=dicho.append, espera=espera)
    return Entrevista(obra=(espia.creada or {}).get("obra"), ficha=ficha, dicho=dicho)
