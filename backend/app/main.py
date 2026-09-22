"""Punto de montaje de la API.

Monta el router de cada feature y nada mas: `A-01` dice que `main.py` compone,
no decide. Cada `include_router` que se anada aqui llega con su feature entera
-router, schemas, service, repository y tests-, nunca antes.
"""

import sqlite3

from fastapi import FastAPI

from app.commons.db import migraciones
from app.commons.trabajos import cola
from app.features.brief import repository as repositorio_brief
from app.features.brief.router import router as router_brief

app = FastAPI(title="Harness de novelas", version="0.1.0")
app.include_router(router_brief)


def preparar_base(ruta=":memory:"):
    con = sqlite3.connect(ruta)
    migraciones.migrar(con)
    cola.asegurar_tabla(con)
    repositorio_brief.asegurar_tablas(con)
    return con
