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
from app.features.orquestacion import regalo

router = APIRouter(tags=["regalo"])


def conexion(request: Request):
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"))
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
