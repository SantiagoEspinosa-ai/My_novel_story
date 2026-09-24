"""Las rutas de la lectura web (`SPEC-22`, `PLAN-22` DP-2).

Solo lectura y sin logica: valida, llama al servicio y devuelve (`A-01`). `GET /obras/{id}`
se queda como la respuesta del alta; la lectura tiene sus rutas propias.
"""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.features.lectura import service
from app.features.lectura.schemas import CapituloLeido, EscenaLeida, Fichas, Indice
from app.features.lectura.schemas import HechosDeEscena, ProgresoDeGeneracion

router = APIRouter(tags=["lectura"])


def conexion(request: Request):
    # F-133: FastAPI la crea, la usa y la cierra en hilos distintos del pool. Se usa en
    # serie, nunca a la vez: no comprobar el hilo es seguro.
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"),
                          check_same_thread=False)
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


@router.get("/capitulos/{id_capitulo}", response_model=CapituloLeido)
def capitulo(id_capitulo: str, con: sqlite3.Connection = Depends(conexion)):
    """Un capitulo de corrido: sus escenas en orden, cada una con estado y hallazgos."""
    resultado = service.capitulo(con, id_capitulo)
    if resultado is None:
        raise HTTPException(404, "no existe el capitulo {0}".format(id_capitulo))
    return resultado


@router.get("/escenas/{id_escena}", response_model=EscenaLeida)
def escena(id_escena: str, con: sqlite3.Connection = Depends(conexion)):
    """Una escena con su estado, sus hallazgos abiertos y su texto elegido (`RF-39`)."""
    resultado = service.escena(con, id_escena)
    if resultado is None:
        raise HTTPException(404, "no existe la escena {0}".format(id_escena))
    return resultado


@router.get("/escenas/{id_escena}/hechos", response_model=HechosDeEscena)
def hechos_de_escena(id_escena: str, con: sqlite3.Connection = Depends(conexion)):
    """Los hechos que usa una escena, con su enunciado: lo que la pagina ofrece al lector
    cuando selecciona un fragmento para pedir un cambio (`PLAN-22` E14)."""
    resultado = service.hechos_de_escena(con, id_escena)
    if resultado is None:
        raise HTTPException(404, "no existe la escena {0}".format(id_escena))
    return resultado


@router.get("/obras/{id_obra}/fichas", response_model=Fichas)
def fichas(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """Las fichas de personajes y lugares, cada una con los capitulos donde aparece."""
    resultado = service.fichas(con, id_obra)
    if resultado is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    return resultado


@router.get("/obras/{id_obra}/progreso", response_model=ProgresoDeGeneracion)
def progreso(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """En que punto va la generacion, con los segundos desde la ultima actividad. `404` si
    la obra no se ha empezado a generar: no se inventa una fase."""
    resultado = service.progreso(con, id_obra)
    if resultado is None:
        raise HTTPException(404, "la obra {0} no tiene progreso de generacion".format(id_obra))
    return resultado
