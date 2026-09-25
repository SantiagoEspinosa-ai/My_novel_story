"""Los agentes de la novela regalo y lo que cuestan (`SPEC-33` `RF-11`, `RF-18`, `RF-21`).

Vivia en `novela_regalo.py`. El lanzamiento desde la web (`PLAN-33` E11) y la CLI tienen
que escribir la misma novela con los mismos agentes, asi que los dos llaman a esto: si la
web copiara la funcion, habria dos pipelines y el dia que divergieran nadie se enteraria.

Vive en `orquestacion/` porque compone: el Editor aislado de `ciclo` y las sesiones de
`commons/modelo`. `orquestacion/` es la unica feature autorizada a hacerlo
(`docs/architecture.md`).
"""

import os
import tempfile
import uuid

from app.commons.modelo import gasto, proveedor
from app.commons.modelo.contador import Contador
from app.features.entrevista import repository as entrevistas
from app.features.orquestacion import ciclo
from app.features.regalo import repository as lecturas

TIPO_DE_TRABAJO = "generacion_regalo"
_SIN_TERMINAR = ("en_cola", "en_curso", "esperando_presupuesto")


class NoSePuedeLanzar(Exception):
    """El motivo llega al cliente como `409` tal cual (`SPEC-33` `RF-13`)."""


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


def ficha_cerrada(con, obra):
    """La ficha de la entrevista cerrada de la obra, o `NoSePuedeLanzar` con el motivo."""
    for id_e in entrevistas.de_la_obra(con, obra):
        e = entrevistas.leer(con, id_e)
        if e is not None and e.cerrada:
            return e.ficha
    raise NoSePuedeLanzar(
        "la obra {0} no tiene una entrevista cerrada: la novela se escribe a partir de "
        "una ficha que el comprador ha confirmado".format(obra))


def en_curso(con, obra):
    """Si ya hay una generacion de la obra sin terminar, en la cola de trabajos."""
    if not con.execute("SELECT 1 FROM sqlite_master WHERE name = 'trabajo'").fetchone():
        return False
    marcas = ",".join("?" * len(_SIN_TERMINAR))
    return con.execute(
        "SELECT 1 FROM trabajo WHERE tipo = ? AND json_extract(carga, '$.obra') = ? "
        "AND estado IN ({0})".format(marcas),
        (TIPO_DE_TRABAJO, obra) + _SIN_TERMINAR).fetchone() is not None


def comprobar(con, obra, techo):
    """Las tres reglas de `RF-11` y `RF-13`, en el backend: la web solo las ensena."""
    ficha = ficha_cerrada(con, obra)
    if en_curso(con, obra):
        raise NoSePuedeLanzar("ya hay una generacion de la obra {0} en curso".format(obra))
    usd, _, _ = lecturas.gasto_de(con)
    if usd is not None and usd >= techo:
        raise NoSePuedeLanzar(
            "lo gastado en esta base ({0:.2f} USD, como minimo) ya alcanza el techo de las "
            "generaciones desde la web ({1:g} USD)".format(usd, techo))
    return ficha


def nueva_generacion():
    return "gen-" + uuid.uuid4().hex[:10]


def generar(con, ruta, obra, ficha, generacion, sistema, fabrica=None, lean=None,
            observacion=None):
    """`RF-11`: la misma novela que `novela_regalo.py`, con los mismos agentes, anotando el
    gasto de cada delegacion con el identificador de esta generacion."""
    from app.features.orquestacion import novela
    registro_hooks = os.path.join(tempfile.gettempdir(), "hooks-{0}.jsonl".format(obra))
    entorno = {"HARNESS_DB": os.path.abspath(ruta), "HARNESS_OBRA": obra,
               "HARNESS_REGISTRO_HOOKS": registro_hooks}
    ag = (fabrica or agentes)(sistema, entorno, anotar=gasto.anotador(con, obra, generacion))
    techo = sistema.generacion_web.techo_de_gasto_usd

    def seguir(numero, coste_del_capitulo):
        """`SPEC-41` `RF-03`: al terminar cada capitulo, lo gastado en la base contra el techo."""
        usd, _, _ = lecturas.gasto_de(con)
        return usd is None or usd < techo
    try:
        r = novela.escribir(con, obra, ficha, ag, carpeta_de_reglas=tempfile.gettempdir(),
                            sistema=sistema, lean=lean, observacion=observacion, seguir=seguir)
    finally:
        if observacion is not None:
            observacion.vaciar()
    pub = r.get("publicacion")
    return {"generacion": generacion, "coste": coste_total(r, ag),
            "publicada": None if pub is None else pub.publicada,
            "parada": r["generacion"].parada}


def abandonar_huerfanas(con):
    """`SPEC-39` `RF-06`, `F-208`: las generaciones y publicaciones corren dentro del proceso de
    la API. Al arrancar, lo que estaba en cola o en curso es de un proceso que ya no existe:
    pasa a abandonado, y una generacion deja su obra parada con el motivo. Devuelve cuantas."""
    from app.commons.trabajos import cola
    from app.features.orquestacion import progreso
    cola.asegurar_tabla(con)
    filas = con.execute("SELECT id, tipo, json_extract(carga, '$.obra') FROM trabajo WHERE tipo IN "
                        "(?, 'publicacion_regalo') AND estado IN ('en_cola', 'en_curso')",
                        (TIPO_DE_TRABAJO,)).fetchall()
    for id_t, tipo, obra in filas:
        cola.marcar_abandonado(con, id_t)
        if tipo == TIPO_DE_TRABAJO and obra:
            progreso.fijar(con, obra, "parada",
                           motivo="el servidor se reinició mientras se escribía: se puede reanudar")
    return len(filas)
