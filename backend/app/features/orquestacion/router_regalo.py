"""Lanzar una novela regalo desde la web (`SPEC-33` `RF-11`, `RF-13`, `PLAN-33` E11).

Un router propio y no una ruta mas en `router.py`: aquel lo tiene a medias `PLAN-22`, y
esto no comparte nada con el ciclo de una escena. Lanzar **gasta dinero**: arranca un
trabajo y devuelve su identificador, sin bloquear (`CLAUDE.md`). Las tres reglas -la
entrevista cerrada, una sola a la vez y el techo- las impone aqui el backend.
"""

import sqlite3

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.commons.configuracion import carga
from app.commons.trabajos import cola
from app.features.orquestacion import acciones as modulo_acciones
from app.features.orquestacion import regalo
from app.features.orquestacion.schemas_de_acciones import AccionesDeObra

router = APIRouter(tags=["regalo"])


def conexion(request: Request):
    # `F-202`: FastAPI puede crear la conexion en un hilo y usarla en otro, como los demas
    # routers ya contemplan.
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"),
                          check_same_thread=False)
    try:
        yield con
    finally:
        con.close()


def _ejecutar(ruta, id_trabajo, trabajo):
    """Toma el trabajo, lo ejecuta y deja el resultado o el motivo, sea cual sea."""
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    try:
        cola.tomar(con, id_trabajo)
        try:
            resultado = trabajo(con)
        except BaseException as e:  # tambien `FaltanModelos`, que es un `SystemExit`
            cola.registrar_fallo(con, id_trabajo, "{0}: {1}".format(type(e).__name__, e))
            return
        cola.registrar_resultado(con, id_trabajo, resultado)
    finally:
        con.close()


@router.post("/obras/{id_obra}/generaciones", status_code=status.HTTP_202_ACCEPTED)
def lanzar(id_obra: str, request: Request, tareas: BackgroundTasks,
           con: sqlite3.Connection = Depends(conexion)):
    """`RF-11`: escribe la novela de la obra a partir de su ficha cerrada. `409` con el
    motivo si la entrevista no esta cerrada, si ya hay una en curso o si lo gastado alcanza
    el techo (`RF-13`)."""
    sistema = carga.cargar_sistema()
    try:
        ficha = regalo.comprobar(con, id_obra, sistema.generacion_web.techo_de_gasto_usd)
    except regalo.NoSePuedeLanzar as e:
        raise HTTPException(409, str(e))
    generacion = regalo.nueva_generacion()
    id_t = cola.encolar(con, regalo.TIPO_DE_TRABAJO, {"obra": id_obra, "generacion": generacion})
    estado = request.app.state
    ruta = estado.ruta_db
    observar = getattr(estado, "observabilidad", None)

    def trabajo(c):
        return regalo.generar(
            c, ruta, id_obra, ficha, generacion, sistema,
            fabrica=getattr(estado, "agentes_regalo", None),
            lean=getattr(estado, "lean_regalo", None),
            observacion=observar(id_obra, "generacion", c) if observar else None)

    tareas.add_task(_ejecutar, ruta, id_t, trabajo)
    return {"id_trabajo": id_t, "generacion": generacion}


# --- `SPEC-39`: publicar y reanudar -----------------------------------------------------

def _lean(estado):
    """Con un Lean inyectado (las pruebas), esta disponible; si no, se busca `lake`."""
    if getattr(estado, "lean_regalo", None) is not None:
        return True, None
    return modulo_acciones.lake_disponible()


@router.get("/obras/{id_obra}/acciones", response_model=AccionesDeObra)
def acciones(id_obra: str, request: Request, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-39` `RF-07`: si se puede publicar o reanudar, por que no, desde donde y cuanto."""
    sistema = carga.cargar_sistema()
    r = modulo_acciones.acciones(con, id_obra, sistema, _lean(request.app.state),
                                 sistema.generacion_web.techo_de_gasto_usd)
    if r is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    return r


def _juez_de_publicacion(sistema, con, obra, ficha):
    """El Editor aislado, con la frontera de los nombres y anotando su gasto."""
    from app.commons.modelo import gasto
    from app.commons.politica import pseudonimos
    from app.features.orquestacion import ciclo
    juez = pseudonimos.envolver(ciclo.editor_aislado(modelo=sistema.modelos.editor),
                                pseudonimos.asegurar(con, obra, ficha))
    juez.anotador = gasto.anotador(con, obra, regalo.nueva_generacion())
    return juez


@router.post("/obras/{id_obra}/publicaciones", status_code=status.HTTP_202_ACCEPTED)
def publicar(id_obra: str, request: Request, tareas: BackgroundTasks,
             con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-39` `RF-01`..`RF-03`: una ronda de la puerta, Lean incluido, sin reescribir. `409`
    con el motivo si no se puede, **sin Lean incluido**, antes de llamar a nadie."""
    sistema = carga.cargar_sistema()
    estado = request.app.state
    a = modulo_acciones.acciones(con, id_obra, sistema, _lean(estado),
                                 sistema.generacion_web.techo_de_gasto_usd)
    if a is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    if not a["publicar"]["posible"]:
        raise HTTPException(409, a["publicar"]["motivo"])
    ficha = regalo.ficha_cerrada(con, id_obra)
    id_t = cola.encolar(con, modulo_acciones.TIPO_DE_PUBLICACION, {"obra": id_obra})
    ruta = estado.ruta_db

    def trabajo(c):
        from app.features.auditoria.lean import VerificadorLean
        lean = getattr(estado, "lean_regalo", None) or VerificadorLean(
            tiempo=sistema.lean.tiempo_maximo_segundos)
        fabrica = getattr(estado, "juez_de_publicacion", None)
        juez = fabrica() if fabrica else _juez_de_publicacion(sistema, c, id_obra, ficha)
        return modulo_acciones.publicar_una_ronda(c, id_obra, ficha, lean, juez, sistema)

    tareas.add_task(_ejecutar, ruta, id_t, trabajo)
    return {"id_trabajo": id_t}
