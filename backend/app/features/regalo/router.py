"""Las rutas de la novela regalo en la web (`SPEC-33`). Sin logica: valida, llama al
servicio y devuelve (`A-01`)."""

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Request

from app.commons.configuracion import carga
from app.features.regalo import service
from app.features.regalo import historia as modulo_historia
from app.features.regalo.schemas import CambiosPedidos, RetiradaEntrada
from app.features.regalo.schemas import (Administracion, ConfirmacionDeGasto, Estanteria,
                                         GeneracionEnVivo, HistoriaDeObra, MatrizDeObra,
                                         PeticionDeLaVersion)

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


def _sistema():
    return carga.cargar_sistema()


@router.get("/obras", response_model=Estanteria)
def estanteria(con: sqlite3.Connection = Depends(conexion)):
    """`RF-01`..`RF-03`: todas las obras, con su portada, su destinatario y su estado."""
    return service.estanteria(con)


@router.get("/admin/obras", response_model=Administracion)
def administracion(con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-36` `RF-03`: todas las novelas con su fase, coste, hallazgos y Lean. **Sin
    login**, por decision del autor: cualquiera con la URL la ve."""
    return service.administracion(con, _sistema().generacion_web.techo_de_gasto_usd)


@router.post("/admin/obras/{id_obra}/retirada")
def retirar(id_obra: str, entrada: RetiradaEntrada, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-41` `RF-01`: quitarla de la estanteria con su motivo. No borra nada."""
    from app.features.regalo import repository as repo
    if not repo.existe_la_obra(con, id_obra):
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    repo.retirar(con, id_obra, entrada.motivo, entrada.quien)
    return {"obra": id_obra, "retirada": repo.retiradas(con)[id_obra]}


@router.delete("/admin/obras/{id_obra}/retirada")
def devolver(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-41` `RF-02`: devolverla a la estanteria."""
    from app.features.regalo import repository as repo
    return {"obra": id_obra, "devuelta": bool(repo.devolver(con, id_obra))}


@router.get("/admin/obras/{id_obra}/cambios", response_model=CambiosPedidos)
def cambios(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-45` `RF-04`: los cambios pedidos de la novela, con el motivo tecnico si fallaron."""
    from app.features.regalo import repository as repo
    return {"cambios": repo.cambios_pedidos(con, id_obra)}


@router.get("/admin/obras/{id_obra}/historia", response_model=HistoriaDeObra)
def historia(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-37`: la historia de una novela, en orden, con sus totales. Sin login (`SPEC-36`)."""
    r = modulo_historia.historia(con, id_obra, _sistema().edicion.umbral_del_editor)
    if r is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    return r


@router.get("/admin/obras/{id_obra}/matriz", response_model=MatrizDeObra)
def matriz(id_obra: str, version: int | None = None,
           con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-38`: la matriz por capitulo de una version (por defecto, la vigente)."""
    sistema = _sistema()
    techo = sistema.generacion_web.techo_de_gasto_usd
    try:
        r = modulo_historia.matriz(con, id_obra, sistema.edicion.umbral_del_editor, techo,
                                   service.confirmacion(con, techo)["gastado"], version)
    except modulo_historia.VersionQueNoExiste:
        raise HTTPException(404, "la obra {0} no tiene la version {1}".format(id_obra, version))
    if r is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    return r


@router.get("/generaciones/gasto", response_model=ConfirmacionDeGasto)
def confirmacion(con: sqlite3.Connection = Depends(conexion)):
    """`RF-12`: lo que la web ensena antes de gastar, con la procedencia de cada cifra."""
    return service.confirmacion(con, _sistema().generacion_web.techo_de_gasto_usd)


@router.get("/obras/{id_obra}/versiones/{numero}/peticion", response_model=PeticionDeLaVersion)
def peticion_de_la_version(id_obra: str, numero: int,
                           con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-35` `RF-10`: que peticion cambio esta version, con las palabras del lector."""
    existe, texto = service.peticion_de_la_version(con, id_obra, numero)
    if not existe:
        raise HTTPException(404, "no existe la version {0} de {1}".format(numero, id_obra))
    return {"texto": texto}


@router.get("/obras/{id_obra}/generacion", response_model=GeneracionEnVivo)
def generacion(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """`RF-14`..`RF-17`, `RF-20`: los capitulos con su fase, las notas del Editor al
    cerrarse cada uno y el coste de la ultima generacion."""
    r = service.generacion(con, id_obra, _sistema().edicion.umbral_del_editor)
    if r is None:
        raise HTTPException(404, "no existe la obra {0}".format(id_obra))
    return r
