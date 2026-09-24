"""Las rutas de la lectura web (`SPEC-22`, `PLAN-22` DP-2).

Solo lectura y sin logica: valida, llama al servicio y devuelve (`A-01`). `GET /obras/{id}`
se queda como la respuesta del alta; la lectura tiene sus rutas propias.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.features.lectura import service
from app.features.lectura.schemas import Indice

router = APIRouter(tags=["lectura"])


def conexion(request: Request):
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"))
    try:
        yield con
    finally:
        con.close()


@router.get("/obras/{id_obra}/indice", response_model=Indice)
def indice(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """La portada y el indice: capitulos por su orden, escenas con estado y hallazgos."""
    resultado = service.indice(con, id_obra)
    if resultado is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    return resultado
