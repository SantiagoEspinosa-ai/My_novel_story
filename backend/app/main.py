"""Punto de montaje de la API.

Monta el router de cada feature y nada mas: `A-01` dice que `main.py` compone,
no decide. Cada `include_router` que se anada aqui llega con su feature entera
-router, schemas, service, repository y tests-, nunca antes.
"""

import contextlib
import sqlite3

from fastapi import FastAPI

from app.commons.db import migraciones, procedencia
from app.commons.politica import auditoria
from app.commons.trabajos import cola
from app.features.brief import repository as repositorio_brief
from app.features.brief.router import router as router_brief
from app.features.entrevista import repository as repositorio_entrevista
from app.features.entrevista.router import router as router_entrevista
from app.features.escaleta import repository as repositorio_escaleta
from app.features.orquestacion.router import router as router_ciclo

def fabrica_de_observacion(exportador):
    """`SPEC-29`: lo que lee el router de la entrevista, `(obra, nombre, con) ->
    Observacion`, con la version de cada prompt ya fijada (`RF-05`)."""
    from app.commons.observabilidad.observacion import Observacion
    from app.features.orquestacion import prompts
    versiones = {rol: v.version for rol, v in prompts.registro().items()}

    def observar(obra, nombre, con=None):
        obs = Observacion(exportador, con=con, obra=obra, nombre=nombre)
        obs.versiones = versiones
        return obs
    return observar


def activar_observabilidad(aplicacion, ruta_env=None):
    """Con claves en `backend/.env`, la entrevista por la API se observa; sin ellas, nada
    cambia y no se envia nada. Devuelve el exportador si la activa, o `None`."""
    from app.commons.observabilidad.langfuse import crear_exportador
    exportador = crear_exportador(ruta_env)
    if exportador.motivo is not None:
        return None
    aplicacion.state.observabilidad = fabrica_de_observacion(exportador)
    return exportador


@contextlib.asynccontextmanager
async def _ciclo_de_vida(aplicacion):
    activar_observabilidad(aplicacion)
    yield


app = FastAPI(title="Harness de novelas", version="0.1.0", lifespan=_ciclo_de_vida)
app.include_router(router_brief)
app.include_router(router_ciclo)
app.include_router(router_entrevista)


def preparar_base(ruta=":memory:"):
    con = sqlite3.connect(ruta)
    migraciones.migrar(con)
    # Con que codigo se escribio esta base. Sin esto, una base generada por un
    # proceso que arranco antes de un cambio es **indistinguible** de una
    # generada ahora, y cualquier medida sobre ella contesta en silencio sobre
    # otro codigo. Paso de verdad: una obra de diez capitulos escribio una hora
    # con los modulos que importo al lanzarse.
    procedencia.registrar(con)
    cola.asegurar_tabla(con)
    repositorio_brief.asegurar_tablas(con)
    repositorio_escaleta.asegurar_tablas(con)
    repositorio_entrevista.asegurar_tablas(con)
    auditoria.asegurar_tabla(con)
    return con
