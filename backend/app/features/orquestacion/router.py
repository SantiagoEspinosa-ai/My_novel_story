"""Los endpoints que conducen el ciclo de una escena.

NINGUNO QUE LLAME AL MODELO RESPONDE DE FORMA SINCRONA
-------------------------------------------------------
Devuelven `202` y un identificador de trabajo. Generar una escena tarda, y un
endpoint que espera a que termine convierte cada reintento en un timeout del
cliente. `A-05` puso la cola en una tabla precisamente para esto.

Y **nunca devuelven el texto**. El texto se consulta despues, con
`GET /escenas/{id}`, que por `RF-23` lo entrega siempre con su estado y sus
hallazgos abiertos. Un texto suelto induce a darlo por bueno.

LAS PUERTAS CON FIRMA HUMANA
-----------------------------
`POST /escenas/{id}/aceptar` y `POST /capitulos/{id}/cerrar` las dispara un
cliente, **nunca el worker**. Son las dos puertas que cierra una persona
(`A-04`, `RF-17`, `RF-27`), y `VER-29` comprueba que el worker no tenga
ninguna ruta de codigo que produzca esas transiciones.

EL 409 DICE QUE LO BLOQUEA
---------------------------
No solo que la transicion no es legal. En el cierre de capitulo dice **que
escenas no estan consolidadas y que hallazgos `mayor` siguen abiertos**: sin
eso, el cliente sabe que no puede cerrar y no sabe que arreglar.
"""

import sqlite3

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status

from app.commons.dominio.enumeraciones import Severidad
from app.commons.trabajos import cola
from app.features.auditoria import capitulo as puerta_capitulo
from app.features.escaleta import repository as repo
from app.features.brief import repository as brief
from app.features.orquestacion import entrega, regeneracion
from app.features.orquestacion import schemas

router = APIRouter(tags=["ciclo"])


def conexion(request: Request):
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"))
    try:
        yield con
    finally:
        con.close()


@router.post("/escenas/{id_escena}/generar", status_code=status.HTTP_202_ACCEPTED)
def generar(id_escena: str, con: sqlite3.Connection = Depends(conexion)):
    """`202` y un identificador. Nunca el texto, y nunca sincrono."""
    if repo.escena(con, id_escena) is None:
        raise HTTPException(404, "no existe la escena {0}".format(id_escena))
    id_trabajo = cola.encolar(con, "generar_escena", {"escena": id_escena})
    return {"id_trabajo": id_trabajo}


@router.post("/escenas/{id_escena}/aceptar")
def aceptar(id_escena: str, version: int, rindiendose: bool = False,
            con: sqlite3.Connection = Depends(conexion)):
    """La dispara una persona. El worker no tiene ninguna ruta que llegue aqui.

    `rindiendose` deja la escena en `aceptada_por_rendicion`, que **no es el
    mismo hecho** que `aceptada`: su delta entra igual al canon y quien lea el
    manuscrito despues necesita saber cuales fueron.
    """
    escena = repo.escena(con, id_escena)
    if escena is None:
        raise HTTPException(404, "no existe la escena {0}".format(id_escena))
    abiertos = repo.hallazgos_abiertos(con, id_escena)
    bloqueantes = [h for h in abiertos if h["severidad"] is Severidad.BLOQUEANTE]
    if bloqueantes:
        raise HTTPException(409, {
            "motivo": "hay invariantes bloqueantes abiertas y una bloqueante no se rinde",
            "bloqueantes": [h["invariante"] for h in bloqueantes],
        })
    repo.aceptar_borrador(con, id_escena, version=version, rindiendose=rindiendose)
    return {"escena": id_escena, "estado": repo.escena(con, id_escena)["estado"]}


@router.post("/escenas/{id_escena}/rechazar")
def rechazar(id_escena: str, motivo: str, con: sqlite3.Connection = Depends(conexion)):
    if repo.escena(con, id_escena) is None:
        raise HTTPException(404, "no existe la escena {0}".format(id_escena))
    return {"escena": id_escena, "estado": "rechazada", "motivo": motivo}


@router.post("/capitulos/{id_capitulo}/cerrar")
def cerrar_capitulo(id_capitulo: str, con: sqlite3.Connection = Depends(conexion)):
    """La segunda puerta con firma humana.

    Devuelve los `menor` que se dejan pasar: si no se enseñaran, `mayor` y
    `menor` volverian a producir el mismo comportamiento.
    """
    # Por **capitulo**, no por obra. `escenas_de` filtra por obra y aqui llega
    # un capitulo: mientras el guion creaba una obra por capitulo los dos
    # identificadores coincidian y esto salia bien por accidente. Con varios
    # capitulos dentro de una obra, devolveria cero escenas y el endpoint
    # concluiria que el capitulo no existe.
    escenas = repo.escenas_de_capitulo(con, id_capitulo)
    if not escenas:
        raise HTTPException(404, "no existe el capitulo {0}".format(id_capitulo))
    hallazgos = [h for e in escenas for h in repo.hallazgos_abiertos(con, e["id"])]
    try:
        cierre = puerta_capitulo.cerrar([e["estado"] for e in escenas], hallazgos)
    except puerta_capitulo.NoSePuedeCerrar as e:
        raise HTTPException(409, {
            "motivo": str(e),
            "escenas_sin_consolidar": [e_["id"] for e_ in escenas
                                       if e_["estado"] not in ("consolidada",
                                                               "aceptada_por_rendicion")],
            "mayores_abiertos": [h["invariante"] for h in hallazgos
                                 if h["severidad"] is Severidad.MAYOR],
        })
    return {"capitulo": id_capitulo, "estado": cierre.estado,
            "menores_que_se_dejan_pasar": cierre.menores_que_se_dejan_pasar}


@router.get("/trabajos/{id_trabajo}", response_model=schemas.TrabajoSalida)
def consultar_trabajo(id_trabajo: str, con: sqlite3.Connection = Depends(conexion)):
    """El estado de un trabajo encolado: su resultado, o el motivo si fallo.

    Es la otra mitad de todos los `202`: sin esto el cliente sabe que se encolo
    algo y no tiene forma de saber que paso.
    """
    t = cola.leer(con, id_trabajo)
    if t is None:
        raise HTTPException(404, "no existe el trabajo {0}".format(id_trabajo))
    return {"id": t.id, "tipo": t.tipo, "estado": t.estado.value,
            "resultado": t.resultado, "motivo": t.motivo_ultimo_fallo,
            "volvio_tras_abandono": t.volvio_tras_abandono}


@router.post("/obras/{id_obra}/entregar")
def entregar(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """`SPEC-25` `RF-21`: borra la entrevista y conserva la novela, sus vetadas y
    sus hechos. Devuelve cuantas filas se borraron, nunca que contenian."""
    try:
        return entrega.entregar(con, id_obra)
    except entrega.NoSePuedeEntregar as e:
        raise HTTPException(409, str(e))


# --- Las versiones de una obra (`SPEC-23` `D-2`, `PLAN-23` A5) -----------------------

@router.get("/obras/{id_obra}/versiones", response_model=schemas.VersionesSalida)
def versiones(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """Las versiones con su numero, su anterior, su commit, cuando se crearon y su
    peticion (`RF-53`)."""
    lista = brief.versiones_de(con, id_obra)
    if not lista:
        raise HTTPException(404, "la obra {0} no tiene versiones".format(id_obra))
    return {"obra": id_obra, "versiones": lista}


@router.get("/obras/{id_obra}/versiones/{numero}", response_model=schemas.VersionDetalleSalida)
def version(id_obra: str, numero: int, con: sqlite3.Connection = Depends(conexion)):
    """Los capitulos en orden: si es compartido con la anterior, su estado, y por
    escena su `estado_de_escena` y su `estado_de_verificacion` (`RF-52`..`RF-54`)."""
    vista = regeneracion.vista_de_version(con, id_obra, numero)
    if vista is None:
        raise HTTPException(404, "la obra {0} no tiene version {1}".format(id_obra, numero))
    return vista


# --- La peticion de cambio (`PLAN-23` A7) ----------------------------------------------

def _existe_la_obra(con, id_obra):
    if not brief.versiones_de(con, id_obra):
        raise HTTPException(404, "la obra {0} no tiene versiones".format(id_obra))


@router.post("/obras/{id_obra}/cambios/propuesta", response_model=schemas.PropuestaSalida)
def propuesta(id_obra: str, entrada: schemas.PeticionEntrada,
              con: sqlite3.Connection = Depends(conexion)):
    """Los capitulos que se van a tocar, **antes** de tocarlos, con la promesa y su
    punto ciego (`RF-51`, `RF-55`). Sincrona y sin modelo. `409` si `C-4` no la admite."""
    _existe_la_obra(con, id_obra)
    try:
        return regeneracion.proponer(con, id_obra, entrada.model_dump())
    except regeneracion.PeticionNoAdmitida as e:
        raise HTTPException(409, str(e))


def _atender(ruta, id_trabajo):
    con = sqlite3.connect(ruta)
    try:
        regeneracion.atender(con, id_trabajo)
    finally:
        con.close()


@router.post("/obras/{id_obra}/cambios", status_code=status.HTTP_202_ACCEPTED)
def cambios(id_obra: str, entrada: schemas.CambioEntrada, request: Request,
            tareas: BackgroundTasks, con: sqlite3.Connection = Depends(conexion)):
    """`202` con el identificador de trabajo. `409` si no hay salida elegida -hoy,
    siempre: falta la medida-, si la lista no es la propuesta o si `C-4` no la admite.
    Con `409` **no se guarda ni se encola nada**."""
    _existe_la_obra(con, id_obra)
    try:
        id_trabajo, _ = regeneracion.pedir(con, id_obra, entrada.model_dump())
    except (regeneracion.PeticionNoAdmitida, regeneracion.SalidaSinElegir,
            regeneracion.ListaCambiada) as e:
        raise HTTPException(409, str(e))
    tareas.add_task(_atender, getattr(request.app.state, "ruta_db", ":memory:"), id_trabajo)
    return {"id_trabajo": id_trabajo}
