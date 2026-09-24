"""Los agentes de la novela regalo y lo que cuestan (`SPEC-33` `RF-11`, `RF-18`, `RF-21`).

Vivia en `novela_regalo.py`. El lanzamiento desde la web (`PLAN-33` E11) y la CLI tienen
que escribir la misma novela con los mismos agentes, asi que los dos llaman a esto: si la
web copiara la funcion, habria dos pipelines y el dia que divergieran nadie se enteraria.

Vive en `orquestacion/` porque compone: el Editor aislado de `ciclo` y las sesiones de
`commons/modelo`. `orquestacion/` es la unica feature autorizada a hacerlo
(`docs/architecture.md`).
"""

from app.commons.modelo import proveedor
from app.commons.modelo.contador import Contador
from app.features.orquestacion import ciclo

AGENTES = ("planificador", "revisor_plan", "editor", "escritor", "resumidor")


class FaltanModelos(SystemExit):
    """Es un `SystemExit` porque la CLI lo trataba asi; la web lo convierte en un `409`."""


def agentes(sistema, entorno, anotar=None, ejecutar=None):
    """Las cinco sesiones de la novela regalo.

    Con `anotar` (`SPEC-33` `RF-18`), cada `SesionDelegada` deja su coste en la base,
    tambien las del Planificador y el Revisor, que van dentro de un `Contador`. Con
    `ejecutar`, el proceso es un doble: solo las pruebas lo pasan.
    """
    m = sistema.modelos
    faltan = [n for n in AGENTES if not getattr(m, n)]
    if faltan:
        raise FaltanModelos("faltan modelos en config/sistema.json: " + ", ".join(faltan))
    sesiones = {
        "planificador": Contador(proveedor.SesionDelegada(modelo=m.planificador,
                                                          agente="planificador")),
        "revisor": Contador(proveedor.SesionDelegada(modelo=m.revisor_plan,
                                                     agente="revisor_plan")),
        "escritor": proveedor.SesionDelegada(modelo=m.escritor, agente="escritor"),
        "editor": ciclo.editor_aislado(modelo=m.editor),
        "resumidor": proveedor.SesionDelegada(modelo=m.resumidor, agente="resumidor"),
    }
    for s in sesiones.values():
        sesion = s.sesion if isinstance(s, Contador) else s
        sesion.entorno.update(entorno)
        if anotar is not None:
            sesion.anotador = anotar
        if ejecutar is not None:
            sesion._ejecutar = ejecutar
    return sesiones


def coste_total(resultado, ag) -> dict:
    """Lo que costo una generacion, como lo informa la CLI: el de los capitulos y el cierre
    (`generacion.coste`) mas el del Planificador y el Revisor, que no pasan por el ciclo.

    Con alguna delegacion sin coste, `usd` es un **suelo** (`sin_coste > 0`).
    """
    g = resultado["generacion"]
    return {
        "usd": g.coste["usd"] + ag["planificador"].usd + ag["revisor"].usd,
        "delegaciones": (g.coste["delegaciones"] + ag["planificador"].delegaciones
                         + ag["revisor"].delegaciones),
        "sin_coste": (g.coste["sin_coste"] + ag["planificador"].sin_coste
                      + ag["revisor"].sin_coste),
    }
