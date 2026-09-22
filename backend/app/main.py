"""Punto de montaje de la API.

Todavia no monta ningun router: las features llegan en la Fase B de `PLAN-01`,
y un router sin su feature seria andamiaje. Lo que hace hoy es arrancar y
migrar la base, que es lo que `A-05` necesita para que la cola exista antes que
el primer endpoint asincrono.
"""

import sqlite3

from fastapi import FastAPI

from app.commons.db import migraciones
from app.commons.trabajos import cola

app = FastAPI(title="Harness de novelas", version="0.1.0")


def preparar_base(ruta=":memory:"):
    con = sqlite3.connect(ruta)
    migraciones.migrar(con)
    cola.asegurar_tabla(con)
    return con
