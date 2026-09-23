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

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.commons.dominio.enumeraciones import Severidad
from app.commons.trabajos import cola
from app.features.auditoria import capitulo as puerta_capitulo
from app.features.escaleta import repository as repo

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
