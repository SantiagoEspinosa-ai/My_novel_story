"""Los endpoints de la entrevista (`SPEC-25` `RF-06`, `PLAN-25` E9).

`A-01`: el router no tiene logica. Valida, llama al servicio y devuelve.

LOS QUE LLAMAN AL MODELO NO RESPONDEN DE FORMA SINCRONA
--------------------------------------------------------
Un turno y el texto libre delegan en el Entrevistador, asi que devuelven `202`
y un trabajo de la cola (`CLAUDE.md`, `A-05`), y el cliente lo consulta en
`GET /trabajos/{id}`. El trabajo lo ejecuta una tarea en segundo plano **que lo
toma de la tabla**: la tabla sigue siendo la fuente de verdad, y si el proceso
muere el trabajo queda `en_curso` y no se relanza solo.

Crear, consultar, confirmar un hecho y cerrar no llaman al modelo y responden
en el momento.

LOS AGENTES SE INYECTAN
-----------------------
`app.state.entrevistador` y `app.state.extractor` son fabricas. Por defecto
crean una sesion delegada con el modelo de `sistema.json`; las pruebas ponen un
doble. Si `sistema.json` no declara el modelo del entrevistador, el trabajo
falla con ese motivo en vez de inventarse uno.
"""

import sqlite3
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.commons.configuracion import carga
from app.commons.modelo import proveedor
from app.commons.trabajos import cola
from app.features.entrevista import repository as repo
from app.features.entrevista import service
from app.features.entrevista.schemas import (HistorialSalida, RespuestaEntrada,
                                             TextoLibreEntrada, turno_a_dict)
from app.features.entrevista.texto_libre import TextoDemasiadoLargo, validar_longitud

router = APIRouter(tags=["entrevista"])


def _ruta(request: Request):
    return getattr(request.app.state, "ruta_db", ":memory:")


def conexion(request: Request):
    # F-133: FastAPI la crea, la usa y la cierra en hilos distintos del pool. Se usa en
    # serie, nunca a la vez: no comprobar el hilo es seguro.
    con = sqlite3.connect(_ruta(request), check_same_thread=False)
    repo.asegurar_tablas(con)
    try:
        yield con
    finally:
        con.close()


def _sesion_del_entrevistador():
    modelo = carga.cargar_sistema().modelos.entrevistador
    if not modelo:
        raise proveedor.FaltaEntorno(
            "sistema.json no declara modelos.entrevistador (`SPEC-25`)")
    return proveedor.SesionDelegada(modelo=modelo, agente="entrevistador")


def _fabrica(request, nombre):
    return getattr(request.app.state, nombre, None) or _sesion_del_entrevistador


def _observar(request):
    """`SPEC-29`: una fabrica `(obra, nombre) -> Observacion`, o nada. Sin ella la
    entrevista sigue igual y no se envia nada."""
    return getattr(request.app.state, "observabilidad", None)


def _reglas():
    return carga.cargar_sistema().contradicciones


def _extensiones():
    """`SPEC-32` `RF-07`: las opciones que se ofrecen salen de `sistema.json`."""
    return carga.cargar_sistema().extensiones


def _existe(con, id_e):
    if repo.leer(con, id_e) is None:
        raise HTTPException(404, "no existe la entrevista {0}".format(id_e))


def _ejecutar(ruta, id_trabajo, trabajo):
    """Toma el trabajo de la tabla, lo ejecuta y deja el resultado o el motivo."""
    con = sqlite3.connect(ruta)
    try:
        cola.tomar(con, id_trabajo)
        try:
            resultado = trabajo(con)
        except Exception as e:  # el motivo tiene que llegar al cliente, sea cual sea
            cola.registrar_fallo(con, id_trabajo, "{0}: {1}".format(
                type(e).__name__, e))
            return
        cola.registrar_resultado(con, id_trabajo, resultado)
    finally:
        con.close()


@router.post("/entrevistas", status_code=status.HTTP_201_CREATED)
def crear(con: sqlite3.Connection = Depends(conexion)):
    return turno_a_dict(service.crear(con))


@router.get("/entrevistas/{id_e}")
def consultar(id_e: str, con: sqlite3.Connection = Depends(conexion)):
    _existe(con, id_e)
    return turno_a_dict(service.estado(con, id_e, _reglas(), date.today().year))


@router.get("/entrevistas/{id_e}/turnos", response_model=HistorialSalida)
def historial(id_e: str, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-33` `RF-10`: la conversacion entera, en orden."""
    _existe(con, id_e)
    return service.historial(con, id_e, _reglas(), date.today().year)


@router.post("/entrevistas/{id_e}/turnos", status_code=status.HTTP_202_ACCEPTED)
def turno(id_e: str, entrada: RespuestaEntrada, request: Request,
          tareas: BackgroundTasks, con: sqlite3.Connection = Depends(conexion)):
    _existe(con, id_e)
    fabrica, reglas, observar = _fabrica(request, "entrevistador"), _reglas(), _observar(request)
    id_t = cola.encolar(con, "turno_de_entrevista", {"entrevista": id_e})
    tareas.add_task(_ejecutar, _ruta(request), id_t, lambda c: turno_a_dict(
        service.turno(c, id_e, entrada.respuesta, fabrica(), reglas,
                      date.today().year, extensiones=_extensiones(), observar=observar)))
    return {"id_trabajo": id_t}


@router.post("/entrevistas/{id_e}/texto-libre", status_code=status.HTTP_202_ACCEPTED)
def texto_libre(id_e: str, entrada: TextoLibreEntrada, request: Request,
                tareas: BackgroundTasks, con: sqlite3.Connection = Depends(conexion)):
    _existe(con, id_e)
    try:
        validar_longitud(entrada.texto)
    except TextoDemasiadoLargo as e:
        raise HTTPException(422, str(e))
    fabrica, observar = _fabrica(request, "extractor"), _observar(request)
    id_t = cola.encolar(con, "texto_libre", {"entrevista": id_e})

    def _trabajo(c):
        r = service.pegar_texto(c, id_e, entrada.texto, fabrica(), observar=observar)
        return {"hechos": [h.model_dump(mode="json") for h in r.hechos],
                "instrucciones_detectadas": r.instrucciones_detectadas}

    tareas.add_task(_ejecutar, _ruta(request), id_t, _trabajo)
    return {"id_trabajo": id_t}


@router.post("/entrevistas/{id_e}/hechos/{id_h}/confirmar")
def confirmar(id_e: str, id_h: str, con: sqlite3.Connection = Depends(conexion)):
    return _cambiar_hecho(con, id_e, id_h, True)


@router.post("/entrevistas/{id_e}/hechos/{id_h}/descartar")
def descartar(id_e: str, id_h: str, con: sqlite3.Connection = Depends(conexion)):
    return _cambiar_hecho(con, id_e, id_h, False)


def _cambiar_hecho(con, id_e, id_h, confirmar_):
    _existe(con, id_e)
    try:
        return service.confirmar_hecho(con, id_e, id_h, confirmar_).model_dump(
            mode="json")
    except KeyError as e:
        raise HTTPException(404, str(e))
    except service.EntrevistaCerrada:
        raise HTTPException(409, "la entrevista ya esta cerrada")


@router.post("/entrevistas/{id_e}/cerrar")
def cerrar(id_e: str, con: sqlite3.Connection = Depends(conexion)):
    """El comprador confirma la ficha. `409` dice que lo impide, no solo que no."""
    _existe(con, id_e)
    try:
        return service.cerrar(con, id_e, _reglas(), date.today().year).model_dump(
            mode="json")
    except service.NoSePuedeCerrar as e:
        raise HTTPException(409, {
            "motivo": str(e), "faltan": e.faltan, "avisos": e.avisos,
            "contradicciones": [{"tipo": c.tipo.value, "descripcion": c.descripcion}
                                for c in e.contradicciones]})
    except service.EntrevistaCerrada:
        raise HTTPException(409, "la entrevista ya esta cerrada")
