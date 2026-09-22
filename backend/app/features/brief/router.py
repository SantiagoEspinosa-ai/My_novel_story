"""Endpoints del alta de obra.

`A-01`: el router no tiene logica. Valida, llama al servicio y devuelve. Si
aparece un `if` de dominio aqui, va al servicio.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.features.brief import service
from app.features.brief.schemas import BriefEntrada, ObraSalida

router = APIRouter(tags=["obras"])


def conexion(request: Request):
    """La ruta de la base viaja en el estado de la app, no en un global.

    Un modulo con la conexion abierta a nivel de import es imposible de probar
    contra una base temporal, y las pruebas acabarian compartiendo estado sin
    que nadie lo decidiera.
    """
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"))
    try:
        yield con
    finally:
        con.close()


@router.post("/obras", status_code=status.HTTP_201_CREATED, response_model=ObraSalida)
def alta_de_obra(entrada: BriefEntrada, con: sqlite3.Connection = Depends(conexion)):
    id_obra = service.dar_de_alta(con, entrada.model_dump())
    return service.consultar(con, id_obra)


@router.get("/obras/{id_obra}", response_model=ObraSalida)
def consultar_obra(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    obra = service.consultar(con, id_obra)
    if obra is None:
        raise HTTPException(status_code=404, detail="no existe la obra {0}".format(id_obra))
    return obra
