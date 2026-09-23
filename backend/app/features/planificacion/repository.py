"""Las versiones del plan y su veredicto (`SPEC-26` `RF-07`).

Se guarda cada version, tambien las rechazadas: cuando una generacion no
empieza porque el plan no se aprobo, lo primero que hay que poder leer es que
objeto el Revisor en cada ronda.

`origen` dice quien rechazo: `codigo` (un hueco de cobertura), `esquema` (el
plan no se pudo leer) o `revisor`. No es vocabulario del dominio: es de donde
salio una fila de esta tabla.
"""

import json

from app.commons.configuracion.esquemas import PlanDeLaObra

SQL = """
CREATE TABLE IF NOT EXISTS plan_de_obra (
    obra       TEXT NOT NULL,
    version    INTEGER NOT NULL,
    plan       TEXT,
    aprobado   INTEGER NOT NULL,
    origen     TEXT NOT NULL,
    objeciones TEXT NOT NULL DEFAULT '[]',
    PRIMARY KEY (obra, version)
);
"""


def asegurar_tablas(con):
    with con:
        con.executescript(SQL)


def guardar(con, obra, version, plan, aprobado, origen, objeciones):
    with con:
        con.execute("INSERT OR REPLACE INTO plan_de_obra (obra, version, plan, "
                    "aprobado, origen, objeciones) VALUES (?, ?, ?, ?, ?, ?)",
                    (obra, version, plan.model_dump_json() if plan else None,
                     int(aprobado), origen, json.dumps(objeciones, ensure_ascii=False)))


def versiones(con, obra) -> list:
    filas = con.execute("SELECT version, aprobado, origen, objeciones FROM plan_de_obra "
                        "WHERE obra = ? ORDER BY version", (obra,)).fetchall()
    return [{"version": f[0], "aprobado": bool(f[1]), "origen": f[2],
             "objeciones": json.loads(f[3])} for f in filas]


def aprobado(con, obra) -> PlanDeLaObra | None:
    f = con.execute("SELECT plan FROM plan_de_obra WHERE obra = ? AND aprobado = 1 "
                    "ORDER BY version DESC LIMIT 1", (obra,)).fetchone()
    return PlanDeLaObra.model_validate_json(f[0]) if f else None
